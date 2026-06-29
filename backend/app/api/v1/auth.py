"""
认证模块API路由
严格按照API文档实现开发者认证和令牌验证接口
"""
from fastapi import APIRouter, HTTPException, Header, Request
from typing import Optional
from app.schemas.auth import (
    DeveloperAuthRequest,
    DeveloperAuthResponse,
    TokenRefreshRequest,
    TokenVerifyRequest,
    TokenVerifyResponse,
    APIResponse,
    ErrorResponse,
    ErrorData
)
from app.services.auth_service import auth_service
from app.services.configuration_status_service import configuration_status_service
from app.services.security_audit_service import log_security_event
from app.services.token_session_service import token_session_service
from app.core.auth.jwt_handler import jwt_handler
from app.core.response import UnifiedResponse

router = APIRouter(prefix="/auth", tags=["认证模块"])


@router.post(
    "/developer",
    response_model=DeveloperAuthResponse,
    summary="开发者认证",
    description="开发者使用密码进行身份认证，获取访问令牌"
)
async def authenticate_developer(request: DeveloperAuthRequest, http_request: Request):
    """
    开发者认证接口
    
    - **password**: 开发者密码
    
    返回JWT访问令牌和相关信息
    """
    # 验证请求参数
    if not request.password:
        raise UnifiedResponse.bad_request(
            message="请求参数错误",
            error_type="validation_error",
            details={"password": ["密码不能为空"]}
        )
    
    # 调用认证服务
    result = auth_service.authenticate_developer(request.password)
    
    if result["success"]:
        log_security_event(
            event_type="auth",
            action="developer_login",
            actor_type="developer",
            actor_id="developer",
            success=True,
            request=http_request,
            details={"login_method": "password"}
        )
        # 认证成功，更新配置状态
        configuration_status_service.update_step_completion(
            step_number=1,
            completed=True,
            details={"authenticated_at": getattr(result["data"], "timestamp", None)}
        )

        return DeveloperAuthResponse(
            code=200,
            message="认证成功",
            data=result["data"]
        )
    else:
        log_security_event(
            event_type="auth",
            action="developer_login",
            actor_type="developer",
            actor_id="developer",
            success=False,
            request=http_request,
            error=result.get("error"),
            details={"reason": result.get("details")}
        )
        # 认证失败
        raise UnifiedResponse.unauthorized(
            message="密码错误",
            error_type=result["error"],
            details=result["details"]
        )


@router.post(
    "/developer/refresh-token",
    response_model=DeveloperAuthResponse,
    summary="刷新开发者令牌",
    description="使用刷新令牌获取新的访问令牌"
)
async def refresh_developer_token(request: TokenRefreshRequest, http_request: Request):
    """
    刷新开发者令牌接口
    
    - **refresh_token**: JWT刷新令牌
    
    返回新的JWT访问令牌和相关信息
    """
    if not request.refresh_token:
        raise UnifiedResponse.bad_request(
            message="请求参数错误",
            error_type="validation_error",
            details={"refresh_token": ["刷新令牌不能为空"]}
        )
        
    result = auth_service.refresh_token(request.refresh_token)
    
    if result["success"]:
        log_security_event(
            event_type="auth",
            action="developer_refresh_token",
            actor_type="developer",
            actor_id="developer",
            success=True,
            request=http_request
        )
        return DeveloperAuthResponse(
            code=200,
            message="令牌刷新成功",
            data=result["data"]
        )
    else:
        log_security_event(
            event_type="auth",
            action="developer_refresh_token",
            actor_type="developer",
            actor_id="developer",
            success=False,
            request=http_request,
            error=result.get("error"),
            details={"reason": result.get("details")}
        )
        raise UnifiedResponse.unauthorized(
            message="刷新令牌无效",
            error_type=result["error"],
            details=result["details"]
        )


@router.post(
    "/developer/verify-token",
    response_model=TokenVerifyResponse,
    summary="验证开发者令牌",
    description="验证开发者令牌的有效性，用于检查令牌是否过期或被撤销"
)
async def verify_developer_token(
    request: TokenVerifyRequest,
    http_request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    验证开发者令牌接口
    
    - **token**: 需要验证的JWT令牌
    - **Authorization**: 请求头中的Bearer token（可选）
    
    返回令牌验证结果
    """
    # 验证请求参数
    if not request.token:
        raise UnifiedResponse.bad_request(
            message="请求参数错误",
            error_type="validation_error",
            details={"token": ["令牌格式不正确"]}
        )
    
    # 调用令牌验证服务
    result = auth_service.verify_token(request.token)
    
    if result["success"]:
        log_security_event(
            event_type="auth",
            action="developer_verify_token",
            actor_type="developer",
            actor_id="developer",
            success=True,
            request=http_request
        )
        # 验证成功
        return TokenVerifyResponse(
            code=200,
            message="令牌有效",
            data=result["data"]
        )
    else:
        log_security_event(
            event_type="auth",
            action="developer_verify_token",
            actor_type="developer",
            actor_id="developer",
            success=False,
            request=http_request,
            error=result.get("error"),
            details={"reason": str(result.get("data"))}
        )
        # 验证失败
        raise UnifiedResponse.unauthorized(
            message="令牌无效",
            error_type=result.get("error", "invalid_token"),
            details=result["data"].model_dump() if hasattr(result["data"], "model_dump") else result["data"]
        )


@router.post(
    "/developer/logout",
    response_model=APIResponse,
    summary="开发者登出",
    description="吊销开发者当前访问令牌和会话"
)
async def logout_developer(
    http_request: Request,
    authorization: Optional[str] = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise UnifiedResponse.unauthorized(
            message="未提供认证信息",
            error_type="no_token"
        )

    token = authorization.replace("Bearer ", "").strip()
    verify_result = jwt_handler.verify_token(
        token,
        expected_user_type="developer",
        expected_token_type="access",
        check_session=False
    )
    if not verify_result["valid"]:
        log_security_event(
            event_type="auth",
            action="developer_logout",
            actor_type="developer",
            actor_id="developer",
            success=False,
            request=http_request,
            error=verify_result.get("error"),
            details={"reason": verify_result.get("details")}
        )
        raise UnifiedResponse.unauthorized(
            message="令牌无效",
            error_type=verify_result.get("error", "invalid_token"),
            details=verify_result.get("details")
        )

    payload = verify_result.get("payload", {})
    sid = verify_result.get("session_id") or payload.get("sid")
    jti = verify_result.get("jti") or payload.get("jti")
    exp_ts = payload.get("exp")

    if sid:
        token_session_service.revoke_session(str(sid), reason="developer_logout")
    token_session_service.revoke_token_jti(
        jti=str(jti) if jti else None,
        exp_ts=float(exp_ts) if exp_ts is not None else None,
        reason="developer_logout",
    )

    log_security_event(
        event_type="auth",
        action="developer_logout",
        actor_type="developer",
        actor_id=str(payload.get("sub", "developer")),
        success=True,
        request=http_request,
        details={"session_id": sid}
    )

    return APIResponse(
        code=200,
        message="登出成功",
        data={"logged_out": True}
    )
