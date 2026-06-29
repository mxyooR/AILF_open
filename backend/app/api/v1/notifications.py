"""
固定通知 API（系统内置）

目标：
- 通知能力作为平台内置 API 提供，不依赖动态路由是否存在
- 仍支持从 API 配置读取 handler_config（用于调整持久化、默认值等策略）
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.core.response import UnifiedResponse
from app.core.auth.jwt_handler import verify_token
from app.models.api_route import APIRouteDBModel, RouteStatus
from app.models.user import User
from app.services.service_dispatcher import dispatch_service_call

logger = get_logger(__name__)
router = APIRouter(prefix="/notifications", tags=["通知"])
security = HTTPBearer(auto_error=False)


class NotificationSendRequest(BaseModel):
    notification_type: str
    message: str
    title: Optional[str] = None
    channel: Optional[str] = "in_app"
    template_code: Optional[str] = None
    user_id: Optional[str] = None
    idempotency_key: Optional[str] = None


def _service_result_to_response(result: Dict[str, Any]):
    code = int(result.get("code", 500))
    message = result.get("message", "请求失败")
    data = _make_json_safe(result.get("data"))

    if 200 <= code < 300:
        return UnifiedResponse.success(data=data, message=message, status_code=code)
    if code == 400:
        raise UnifiedResponse.bad_request(message=message, details=data)
    if code == 401:
        raise UnifiedResponse.unauthorized(message=message, details=data)
    if code == 403:
        raise UnifiedResponse.forbidden(message=message, details=data)
    if code == 404:
        raise UnifiedResponse.not_found(message=message, details=data)
    if code == 409:
        raise UnifiedResponse.conflict(message=message, details=data)
    raise UnifiedResponse.internal_error(message=message, details=data)


def _make_json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(k): _make_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_make_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_make_json_safe(item) for item in value]
    return value


def _load_notification_route_config(db: Session, method: str, endpoint: str) -> Optional[Dict[str, Any]]:
    route = (
        db.query(APIRouteDBModel)
        .filter(
            APIRouteDBModel.method == method.upper(),
            APIRouteDBModel.endpoint == endpoint,
            APIRouteDBModel.status == RouteStatus.ACTIVE,
        )
        .order_by(APIRouteDBModel.updated_at.desc())
        .first()
    )
    if not route:
        return None
    return {
        "handler_config": route.handler_config or {},
        "api_id": route.api_id,
        "endpoint": route.endpoint,
        "method": route.method,
    }


async def get_notification_actor(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if not credentials:
        raise UnifiedResponse.unauthorized(message="缺少认证凭据", error_type="missing_token")

    try:
        payload = verify_token(credentials.credentials)
    except Exception as exc:
        raise UnifiedResponse.unauthorized(
            message="令牌无效或已过期",
            error_type="invalid_token",
            details=str(exc),
        )

    user_type = payload.get("user_type")
    if user_type == "developer":
        return {"user_type": "developer", "user_id": "developer", "payload": payload}
    if user_type != "user":
        raise UnifiedResponse.forbidden(
            message="不支持的认证类型",
            error_type="unsupported_user_type",
            details={"user_type": user_type},
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise UnifiedResponse.unauthorized(message="令牌缺少 user_id", error_type="invalid_token_payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise UnifiedResponse.unauthorized(message="用户不存在或已禁用", error_type="user_not_available")

    return {
        "user_type": "user",
        "user_id": str(user.id),
        "username": user.username,
        "payload": payload,
    }


@router.post("/send")
async def send_notification(
    request: NotificationSendRequest,
    actor: Dict[str, Any] = Depends(get_notification_actor),
    db: Session = Depends(get_db),
):
    target_user_id = request.user_id
    if actor["user_type"] == "user":
        # 普通用户仅允许给自己创建站内通知
        if target_user_id and str(target_user_id) != actor["user_id"]:
            raise UnifiedResponse.forbidden(message="普通用户不能给其他用户发送通知")
        target_user_id = actor["user_id"]

    route_config = _load_notification_route_config(db, "POST", "/api/v1/notifications/send")
    request_data = {
        "body": {
            "notification_type": request.notification_type,
            "message": request.message,
            "title": request.title,
            "channel": request.channel,
            "template_code": request.template_code,
            "user_id": target_user_id,
            "idempotency_key": request.idempotency_key,
        }
    }
    result = await dispatch_service_call(
        "notification_service",
        "send_notification",
        request_data=request_data,
        route_config=route_config,
    )
    return _service_result_to_response(result)


@router.get("")
async def list_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    actor: Dict[str, Any] = Depends(get_notification_actor),
    db: Session = Depends(get_db),
):
    effective_user_id = user_id
    if actor["user_type"] == "user":
        # 普通用户仅可查询自己的通知
        effective_user_id = actor["user_id"]

    route_config = _load_notification_route_config(db, "GET", "/api/v1/notifications")
    request_data = {
        "query": {
            "page": page,
            "limit": limit,
            "user_id": effective_user_id,
        }
    }
    result = await dispatch_service_call(
        "notification_service",
        "list_notifications",
        request_data=request_data,
        route_config=route_config,
    )
    return _service_result_to_response(result)


@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    actor: Dict[str, Any] = Depends(get_notification_actor),
    db: Session = Depends(get_db),
):
    route_config = _load_notification_route_config(
        db, "POST", "/api/v1/notifications/{notification_id}/read"
    )
    request_data = {
        "path": {"notification_id": notification_id},
        "body": {
            "notification_id": notification_id,
            "user_id": actor["user_id"] if actor["user_type"] == "user" else None,
            "requester_user_id": actor["user_id"] if actor["user_type"] == "user" else None,
        },
    }
    result = await dispatch_service_call(
        "notification_service",
        "mark_as_read",
        request_data=request_data,
        route_config=route_config,
    )
    return _service_result_to_response(result)


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    actor: Dict[str, Any] = Depends(get_notification_actor),
    db: Session = Depends(get_db),
):
    route_config = _load_notification_route_config(
        db, "DELETE", "/api/v1/notifications/{notification_id}"
    )
    request_data = {
        "path": {"notification_id": notification_id},
        "body": {
            "notification_id": notification_id,
            "user_id": actor["user_id"] if actor["user_type"] == "user" else None,
            "requester_user_id": actor["user_id"] if actor["user_type"] == "user" else None,
        },
    }
    result = await dispatch_service_call(
        "notification_service",
        "delete_notification",
        request_data=request_data,
        route_config=route_config,
    )
    return _service_result_to_response(result)
