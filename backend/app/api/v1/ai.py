"""
AI交互API路由 - 重构版本
提供AI命令处理、意图分析、推荐等功能
确保token验证、用户认证、权限检查流程正确
"""
from app.core.logging_config import get_logger
from fastapi import APIRouter, Depends
from typing import Optional

from app.schemas.ai import (
    CommandRequest
)
from pydantic import BaseModel
from typing import Dict, Any
from app.services.permission_service import permission_service
from app.core.auth.jwt_handler import verify_developer_token, verify_token
from app.core.database import get_db
from app.models.user import User
from app.models.role import RoleDBModel
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.response import UnifiedResponse
from app.services.async_command_service import async_command_service

logger = get_logger(__name__)

router = APIRouter(tags=["AI交互"])
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """
    获取当前用户信息（可选，不强制认证）- 重构版本

    流程：
    1. 检查是否有token
    2. 尝试开发者token验证
    3. 尝试用户token验证
    4. 获取用户权限和可访问API
    """
    if not credentials:
        logger.debug("🔍 没有提供认证凭据")
        return None

    try:
        token = credentials.credentials
        
        # 步骤1: 尝试开发者token验证
        developer_user = await _verify_developer_token(credentials)
        if developer_user:
            logger.debug("开发者token验证成功")
            return developer_user

        # 步骤2: 尝试用户token验证
        user_info = await _verify_user_token(token, db)
        if user_info:
            logger.debug(f"用户token验证成功: {user_info.get('username')}")
            return user_info

        logger.warning("❌ token验证失败")
        return None

    except Exception as e:
        logger.error(f"❌ token验证异常: {str(e)}")
        return None


async def _verify_developer_token(credentials: HTTPAuthorizationCredentials) -> Optional[Dict[str, Any]]:
    """验证开发者token"""
    try:
        dev_payload = verify_developer_token(credentials)
        if dev_payload and dev_payload.get("user_type") == "developer":
            # 开发者拥有所有 API 权限，获取所有活跃的 API
            from app.core.database import get_db_session
            from app.models.api_route import APIRouteDBModel, RouteStatus
            
            all_apis = []
            try:
                with get_db_session() as db:
                    apis = db.query(APIRouteDBModel).filter(
                        APIRouteDBModel.status == RouteStatus.ACTIVE
                    ).all()
                    for api in apis:
                        api_info = {
                            "api_id": api.api_id,
                            "name": api.name,
                            "endpoint": api.endpoint,
                            "method": api.method,
                            "description": api.description,
                            "resource": api.api_id,
                            "action": "access"
                        }
                        if api.parameters_config:
                            api_info["parameters"] = api.parameters_config
                        all_apis.append(api_info)
                    logger.debug(f"开发者获取到 {len(all_apis)} 个可用 API")
            except Exception as e:
                logger.warning(f"获取开发者 API 列表失败: {str(e)}")
            
            # 这是内部helper函数，返回用户信息dict（不是API响应）
            return {
                "user_id": "developer",
                "username": "developer",
                "user_object": None,
                "role": {
                    "id": "developer",
                    "name": "开发者",
                    "level": 10,
                    "permissions": ["*:*"]
                },
                "permissions": ["*:*"],
                "accessible_apis": all_apis
            }
        return None
    except Exception as e:
        logger.debug(f"开发者token验证失败: {str(e)}")
        return None


async def _verify_user_token(token: str, db: Session) -> Optional[Dict[str, Any]]:
    """验证用户token"""
    try:
        # 验证token
        payload = verify_token(token)

        # 检查token类型
        if payload.get("user_type") != "user":
            logger.debug(f"Token类型不匹配，期望user，实际: {payload.get('user_type')}")
            return None

        # 获取用户ID
        user_id = payload.get("user_id")
        if not user_id:
            logger.warning("Token中没有user_id")
            return None

        # 查询用户
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"用户不存在: {user_id}")
            return None

        # 获取用户角色
        user_role = None
        if user.role_id:
            user_role = db.query(RoleDBModel).filter(RoleDBModel.id == user.role_id).first()
            if not user_role:
                logger.warning(f"用户角色不存在: {user.role_id}")

        return await _build_user_info(user, user_role, db)

    except Exception as e:
        logger.warning(f"用户token验证失败: {str(e)}")
        return None


async def _build_user_info(user: User, user_role: Optional[RoleDBModel], db: Session) -> Dict[str, Any]:
    """构建用户信息"""
    try:
        # 获取用户权限
        permissions = []
        if user_role:
            permissions = permission_service.get_user_permissions(user, db)

        # 获取可访问的API
        accessible_apis = []
        if user_role:
            accessible_apis = permission_service.get_user_accessible_apis(user, db)

        # 构建角色信息
        role_info = {
            "id": user_role.id if user_role else "guest",
            "name": user_role.name if user_role else "访客",
            "code": user_role.code if user_role else "guest"
        }

        # 这是内部helper函数，返回用户信息dict（不是API响应）
        return {
            "user_id": user.id,
            "username": user.username,
            "user_object": user,
            "role": role_info,
            "permissions": permissions,
            "accessible_apis": accessible_apis
        }

    except Exception as e:
        logger.error(f"❌ 构建用户信息失败: {str(e)}")
        # 这是内部helper函数，返回基础用户信息dict（不是API响应）
        return {
            "user_id": user.id,
            "username": user.username,
            "user_object": user,
            "role": {"id": "guest", "name": "访客", "level": 0},
            "permissions": [],
            "accessible_apis": []
        }


class SchemaValidationRequest(BaseModel):
    """Schema验证请求"""
    schema: Dict[str, Any]
    schema_type: str = "amis"  # amis, json-schema等


class SchemaValidationResponse(BaseModel):
    """Schema验证响应"""
    success: bool
    valid: bool = False
    errors: list = []
    warnings: list = []
    suggestions: list = []
    error: str = None


class AmisPreviewRequest(BaseModel):
    """Amis预览请求"""
    schema: Dict[str, Any]
    mock_data: Dict[str, Any] = {}


class AmisPreviewResponse(BaseModel):
    """Amis预览响应"""
    success: bool
    preview_url: str = None
    error: str = None


@router.post("/command/async")
async def process_command_async(
    request: CommandRequest,
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    异步处理用户命令（后端编排 + worker 推理）
    """
    try:
        enhanced_context = await _build_enhanced_context(request, current_user, db)
        task_id = async_command_service.submit(request.command, enhanced_context)
        return UnifiedResponse.success(
            status_code=202,
            message="异步任务已提交",
            data={
                "task_id": task_id,
                "status": "PENDING",
                "poll_url": f"/api/v1/command/async/{task_id}"
            }
        )
    except Exception as e:
        logger.error(f"❌ 提交异步命令失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="提交异步命令失败",
            error_type="command_async_submit_error",
            details=str(e)
        )


@router.get("/command/async/{task_id}")
async def get_process_command_async_result(task_id: str):
    """
    查询异步命令执行状态/结果
    """
    try:
        task_result = async_command_service.get(task_id)
        if not task_result:
            raise UnifiedResponse.not_found(
                message="任务不存在或已过期",
                error_type="task_not_found",
                details={"task_id": task_id}
            )
        state = task_result.get("status", "PENDING")

        payload = {
            "task_id": task_id,
            "status": state
        }

        if state == "SUCCESS":
            payload["result"] = task_result.get("result")
        elif state == "FAILURE":
            payload["error"] = task_result.get("error") or "任务执行失败"
        elif state in {"RETRY", "STARTED"}:
            payload["message"] = "任务执行中"
        else:
            payload["message"] = "任务排队中"

        return UnifiedResponse.success(
            message="任务状态获取成功",
            data=payload
        )
    except Exception as e:
        logger.error(f"❌ 查询异步命令结果失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="查询异步命令结果失败",
            error_type="command_async_query_error",
            details=str(e)
        )

async def _build_enhanced_context(request: CommandRequest, current_user: Optional[Dict[str, Any]],
                                db: Session) -> Dict[str, Any]:
    """构建增强的上下文信息 - 简化版，直接使用 current_user 中已有的信息"""
    try:
        # 基础上下文
        enhanced_context = request.context or {}

        if not current_user:
            # 未登录用户
            enhanced_context.update({
                "user_id": None,
                "user_permissions": [],
                "accessible_apis": [],
                "user_role": {"id": "guest", "name": "访客", "level": 0}
            })
            return enhanced_context

        # 已登录用户 - 直接使用 get_current_user_optional 返回的信息
        enhanced_context.update({
            "user_id": current_user.get("user_id"),
            "user_permissions": current_user.get("permissions", []),
            "accessible_apis": current_user.get("accessible_apis", []),
            "user_role": current_user.get("role", {"id": "guest", "name": "访客", "level": 0})
        })

        return enhanced_context

    except Exception as e:
        logger.error(f"❌ 构建增强上下文失败: {str(e)}")
        # 这是内部helper函数，返回基础上下文dict（不是API响应）
        return {
            "user_id": current_user.get("user_id") if current_user else None,
            "user_permissions": [],
            "accessible_apis": [],
            "user_role": {"id": "guest", "name": "访客", "level": 0}
        }




# 旧的 API 端点已废弃（依赖已删除的旧服务）
# amis_validator 和 amis_knowledge 已删除



