"""
安全审计日志服务
记录登录、权限变更、配置变更等敏感操作
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import json

from fastapi import Request

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger("app.security.audit")

_SENSITIVE_KEYS = {
    "password",
    "new_password",
    "old_password",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
}


def _mask_value(value: Any) -> str:
    raw = str(value or "")
    if len(raw) <= 8:
        return "***"
    return f"{raw[:3]}***{raw[-3:]}"


def _sanitize(data: Any) -> Any:
    if isinstance(data, dict):
        result: Dict[str, Any] = {}
        for key, value in data.items():
            if str(key).lower() in _SENSITIVE_KEYS:
                result[key] = _mask_value(value)
            else:
                result[key] = _sanitize(value)
        return result
    if isinstance(data, list):
        return [_sanitize(item) for item in data]
    return data


def _request_context(request: Optional[Request]) -> Dict[str, Any]:
    if request is None:
        return {}
    return {
        "client_ip": request.client.host if request.client else None,
        "method": request.method,
        "path": str(request.url.path),
        "user_agent": request.headers.get("user-agent"),
        "request_id": request.headers.get("x-request-id"),
    }


def log_security_event(
    event_type: str,
    action: str,
    actor_type: str,
    actor_id: Optional[str],
    success: bool,
    request: Optional[Request] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    if not settings.SECURITY_AUDIT_ENABLED:
        return

    payload = {
        "event_type": event_type,
        "action": action,
        "success": success,
        "actor": {
            "type": actor_type,
            "id": actor_id,
        },
        "target": {
            "type": target_type,
            "id": target_id,
        },
        "details": _sanitize(details or {}),
        "error": error,
        "request": _request_context(request),
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
    }

    level = logger.info if success else logger.warning
    level(f"SECURITY_AUDIT {json.dumps(payload, ensure_ascii=False)}")

