"""
认证服务
处理开发者认证和令牌验证的业务逻辑
"""
from typing import Dict, Any
from app.config import settings
from app.core.auth.jwt_handler import jwt_handler
from app.services.token_session_service import token_session_service
from app.schemas.auth import (
    DeveloperAuthData, 
    TokenVerifySuccessData, 
    TokenVerifyFailData
)


class AuthService:
    """认证服务类"""
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新访问令牌
        
        Args:
            refresh_token: JWT刷新令牌
            
        Returns:
            刷新结果字典
        """
        result = jwt_handler.verify_token(
            refresh_token,
            expected_user_type="developer",
            expected_token_type="refresh",
            check_session=True,
        )

        if not result["valid"]:
            return {
                "success": False,
                "error": "invalid_refresh_token",
                "details": "无效的刷新令牌"
            }

        payload = result["payload"]
        refresh_exp = payload.get("exp")
        token_session_service.revoke_token_jti(
            jti=result.get("jti"),
            exp_ts=float(refresh_exp) if refresh_exp is not None else None,
            reason="developer_refresh_rotation",
        )

        # 刷新时保持同一会话，降低并发会话膨胀
        new_token_data = jwt_handler.create_token_pair(
            data={
                "sub": payload.get("sub", "developer"),
                "type": payload.get("type", "developer"),
                "user_type": "developer",
            },
            user_type="developer",
            session_id=result.get("session_id"),
        )
        
        return {
            "success": True,
            "data": DeveloperAuthData(**new_token_data)
        }

    def authenticate_developer(self, password: str) -> Dict[str, Any]:
        """
        开发者认证
        
        Args:
            password: 开发者密码
            
        Returns:
            认证结果字典
        """
        # 验证密码
        if password != settings.DEVELOPER_PASSWORD:
            return {
                "success": False,
                "error": "invalid_password",
                "details": "提供的密码不正确"
            }
        
        # 生成JWT token（含刷新令牌和会话ID）
        token_data = jwt_handler.create_token_pair(
            data={"sub": "developer", "type": "developer", "user_type": "developer"}
        )
        
        return {
            "success": True,
            "data": DeveloperAuthData(**token_data)
        }
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        验证令牌
        
        Args:
            token: 要验证的JWT令牌
            
        Returns:
            验证结果字典
        """
        # 验证token
        result = jwt_handler.verify_token(
            token,
            expected_user_type="developer",
            expected_token_type="access",
            check_session=True,
        )
        
        if result["valid"]:
            # 验证成功
            return {
                "success": True,
                "data": TokenVerifySuccessData(
                    valid=result["valid"],
                    user_type=result["user_type"],
                    issued_at=result["issued_at"],
                    expires_at=result["expires_at"],
                    remaining_time=result["remaining_time"]
                )
            }
        else:
            # 验证失败
            return {
                "success": False,
                "error": result.get("error", "invalid_token"),
                "data": TokenVerifyFailData(
                    valid=result["valid"],
                    error=result["error"],
                    details=result["details"]
                )
            }


# 全局认证服务实例
auth_service = AuthService()
