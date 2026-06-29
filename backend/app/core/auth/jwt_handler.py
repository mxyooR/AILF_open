"""
JWT认证处理器
实现JWT token的生成、验证和解析功能
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
import uuid
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.services.token_session_service import token_session_service


class JWTHandler:
    """JWT处理器类"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expire_hours = settings.JWT_EXPIRE_HOURS

    @staticmethod
    def _to_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
            except Exception:
                pass
        raise ValueError("invalid datetime value")

    @staticmethod
    def _resolve_user_id(data: Dict[str, Any]) -> str:
        if data.get("user_id") is not None:
            return str(data.get("user_id"))
        if data.get("sub") is not None:
            return str(data.get("sub"))
        return str(data.get("username", "anonymous"))

    def _resolve_expire_seconds(self, user_type: str) -> Tuple[int, int]:
        if user_type == "developer":
            return (
                int(settings.DEVELOPER_ACCESS_TOKEN_EXPIRE_SECONDS),
                int(settings.DEVELOPER_REFRESH_TOKEN_EXPIRE_SECONDS),
            )
        return (
            int(settings.USER_ACCESS_TOKEN_EXPIRE_SECONDS),
            int(settings.USER_REFRESH_TOKEN_EXPIRE_SECONDS),
        )

    def _build_claims(
        self,
        data: Dict[str, Any],
        user_type: str,
        token_type: str,
        expire_seconds: int,
        session_id: str,
    ) -> Tuple[Dict[str, Any], datetime, datetime]:
        now = datetime.now(timezone.utc)
        expire_at = now + timedelta(seconds=max(60, int(expire_seconds)))
        claims = data.copy()
        claims.update({
            "sub": str(data.get("sub") or self._resolve_user_id(data)),
            "iat": int(now.timestamp()),
            "exp": int(expire_at.timestamp()),
            "user_type": user_type,
            "token_type": token_type,
            "sid": session_id,
            "jti": uuid.uuid4().hex,
        })
        claims.pop("is_refresh_token", None)
        return claims, now, expire_at

    def create_token_pair(
        self,
        data: Dict[str, Any],
        user_type: Optional[str] = None,
        session_id: Optional[str] = None,
        access_expires_seconds: Optional[int] = None,
        refresh_expires_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        resolved_user_type = user_type or str(data.get("user_type", "user"))
        user_id = self._resolve_user_id(data)

        if session_id is None:
            max_sessions = (
                settings.MAX_ACTIVE_DEVELOPER_SESSIONS
                if resolved_user_type == "developer"
                else settings.MAX_ACTIVE_USER_SESSIONS
            )
            session_id = token_session_service.create_session(
                user_type=resolved_user_type,
                user_id=user_id,
                max_sessions=max_sessions,
                metadata={
                    "username": data.get("username"),
                    "role_code": data.get("role_code"),
                },
            )

        default_access_exp, default_refresh_exp = self._resolve_expire_seconds(resolved_user_type)
        access_exp = int(access_expires_seconds or default_access_exp)
        refresh_exp = int(refresh_expires_seconds or default_refresh_exp)

        access_claims, issued_at, access_expires_at = self._build_claims(
            data=data,
            user_type=resolved_user_type,
            token_type="access",
            expire_seconds=access_exp,
            session_id=session_id,
        )
        refresh_claims, _, _ = self._build_claims(
            data=data,
            user_type=resolved_user_type,
            token_type="refresh",
            expire_seconds=refresh_exp,
            session_id=session_id,
        )

        access_token = jwt.encode(access_claims, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_claims, self.secret_key, algorithm=self.algorithm)

        return {
            "token": access_token,
            "refresh_token": refresh_token,
            "expires_in": access_exp,
            "token_type": "Bearer",
            "issued_at": issued_at.isoformat(),
            "expires_at": access_expires_at.isoformat(),
            "session_id": session_id,
        }
    
    def create_access_token(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建访问令牌 + 刷新令牌（兼容旧接口）
        
        Args:
            data: 要编码到token中的数据
            
        Returns:
            包含token信息的字典
        """
        return self.create_token_pair(data=data, user_type=str(data.get("user_type", "user")))

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        创建刷新令牌
        
        Args:
            data: 要编码到token中的数据
            
        Returns:
            刷新令牌字符串
        """
        token_data = self.create_token_pair(data=data, user_type=str(data.get("user_type", "user")))
        return token_data["refresh_token"]
    
    def verify_token(
        self,
        token: str,
        expected_user_type: Optional[str] = None,
        expected_token_type: Optional[str] = None,
        check_session: bool = True,
    ) -> Dict[str, Any]:
        """
        验证token
        
        Args:
            token: 要验证的JWT token
            
        Returns:
            验证结果字典
        """
        try:
            # 解码token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_type = str(payload.get("user_type", "developer"))
            token_type = str(payload.get("token_type") or ("refresh" if payload.get("is_refresh_token") else "access"))
            jti = payload.get("jti")
            sid = payload.get("sid")
            user_id = payload.get("user_id") or payload.get("sub")

            if expected_user_type and user_type != expected_user_type:
                return {
                    "valid": False,
                    "error": "invalid_user_type",
                    "details": "令牌用户类型不匹配"
                }

            if expected_token_type and token_type != expected_token_type:
                return {
                    "valid": False,
                    "error": "invalid_token_type",
                    "details": "令牌类型不匹配"
                }

            if token_session_service.is_token_revoked(str(jti) if jti else None):
                return {
                    "valid": False,
                    "error": "token_revoked",
                    "details": "令牌已失效，请重新登录"
                }

            if check_session:
                if sid:
                    if not token_session_service.is_session_active(
                        sid=str(sid),
                        user_type=user_type,
                        user_id=str(user_id),
                    ):
                        return {
                            "valid": False,
                            "error": "session_revoked",
                            "details": "会话已失效，请重新登录"
                        }
                    token_session_service.touch_session(str(sid))
                elif not settings.AUTH_ALLOW_LEGACY_TOKENS:
                    return {
                        "valid": False,
                        "error": "session_missing",
                        "details": "令牌会话无效，请重新登录"
                    }
            
            # 获取时间信息
            issued_at = self._to_datetime(payload.get("iat"))
            expires_at = self._to_datetime(payload.get("exp"))
            now = datetime.now(timezone.utc)
            
            # 计算剩余时间
            remaining_seconds = int((expires_at - now).total_seconds())
            
            return {
                "valid": True,
                "user_type": user_type,
                "token_type": token_type,
                "issued_at": issued_at.isoformat(),
                "expires_at": expires_at.isoformat(),
                "remaining_time": max(0, remaining_seconds),
                "session_id": sid,
                "jti": jti,
                "payload": payload
            }
            
        except JWTError as e:
            # 判断错误类型
            error_msg = str(e).lower()
            if "expired" in error_msg:
                error_type = "token_expired"
                details = "令牌已过期"
            elif "invalid" in error_msg or "decode" in error_msg:
                error_type = "token_invalid"
                details = "令牌格式无效"
            else:
                error_type = "token_invalid"
                details = "令牌验证失败"
            
            return {
                "valid": False,
                "error": error_type,
                "details": details
            }
        except Exception:
            return {
                "valid": False,
                "error": "token_invalid",
                "details": "令牌验证失败"
            }
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        解码token（不验证过期时间）
        
        Args:
            token: 要解码的JWT token
            
        Returns:
            解码后的payload，失败返回None
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # 不验证过期时间
            )
            return payload
        except JWTError:
            return None


# 全局JWT处理器实例
jwt_handler = JWTHandler()

# HTTP Bearer认证方案
security = HTTPBearer()


def create_access_token(data: Dict[str, Any]) -> str:
    """
    创建访问令牌（兼容接口）

    Args:
        data: 要编码到token中的数据

    Returns:
        JWT token字符串
    """
    result = jwt_handler.create_access_token(data)
    return result["token"]


def verify_token(token: str) -> Dict[str, Any]:
    """
    验证token（兼容接口）

    Args:
        token: 要验证的JWT token

    Returns:
        token payload

    Raises:
        JWTError: 当token无效或过期时
    """
    from jose import JWTError

    result = jwt_handler.verify_token(token, expected_token_type="access", check_session=True)
    if not result["valid"]:
        if result.get("error") == "token_expired":
            raise JWTError("Token has expired")
        elif result.get("error") in {"token_revoked", "session_revoked", "session_missing"}:
            raise JWTError("Token revoked")
        else:
            raise JWTError("Invalid token")

    return result["payload"]


def verify_developer_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    验证开发者token的依赖函数

    Args:
        credentials: HTTP Bearer认证凭据

    Returns:
        验证后的token payload

    Raises:
        HTTPException: 当token无效或过期时
    """
    try:
        # 验证token
        result = jwt_handler.verify_token(
            credentials.credentials,
            expected_user_type="developer",
            expected_token_type="access",
            check_session=True
        )

        if not result["valid"]:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": 401,
                    "message": "认证失败",
                    "data": {
                        "error": result.get("error", "token_invalid"),
                        "details": result.get("details", "令牌无效")
                    }
                }
            )

        # 检查用户类型
        payload = dict(result["payload"])
        if payload.get("user_id") is None:
            payload["user_id"] = payload.get("sub")
        if payload.get("user_type") is None:
            payload["user_type"] = result.get("user_type")
        if payload.get("remaining_time") is None:
            payload["remaining_time"] = result.get("remaining_time")
        return payload

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail={
                "code": 401,
                "message": "认证失败",
                "data": {
                    "error": "token_verification_failed",
                    "details": f"令牌验证失败: {str(e)}"
                }
            }
        )
