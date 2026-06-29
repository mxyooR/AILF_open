"""
用户认证API路由
提供用户登录、注册、登出等功能
"""
from fastapi import APIRouter, HTTPException, Depends, status, Request, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import bcrypt
from datetime import datetime

from app.core.database import get_db
from app.core.auth.jwt_handler import jwt_handler
from app.models.user import User
from app.models.role import RoleDBModel
from app.schemas.user_auth import (
    UserRegisterRequest, UserLoginRequest, UserResponse,
    LoginResponse, PermissionsResponse, UserProfileResponse, UserTokenRefreshRequest
)
from app.services.permission_service import permission_service
from app.services.token_session_service import token_session_service
from app.services.security_audit_service import log_security_event
from app.core.response import UnifiedResponse

from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/user", tags=["用户认证"])


async def _create_role_entity_record(user: User, request: UserRegisterRequest, role_code: str, db: Session):
    """为用户创建对应的角色实体数据记录"""
    try:
        from app.services.entity_service import EntityService

        entity_service = EntityService()

        # 获取角色对应的实体定义
        entity_result = entity_service.get_entity_by_name(role_code)

        if not entity_result.get("success") or not entity_result.get("data"):
            logger.warning(f"未找到角色 {role_code} 对应的实体，跳过实体记录创建")
            return

        entity = entity_result["data"]["entity"]

        def _get_field_attr(field_obj, attr_name, default=None):
            if isinstance(field_obj, dict):
                return field_obj.get(attr_name, default)
            return getattr(field_obj, attr_name, default)

        if isinstance(entity, dict):
            entity_fields = entity.get("fields", [])
        else:
            entity_fields = getattr(entity, "fields", []) or []

        # 构建实体数据，从注册请求中提取对应字段
        entity_data = {"user_id": user.id}  # 关联用户ID

        # 将请求数据转换为字典，以便动态访问
        request_dict = request.dict()

        # 检查必填字段是否都有值
        missing_required_fields = []

        for field in entity_fields:
            field_name = _get_field_attr(field, "name")
            required = _get_field_attr(field, "required", False)
            display_name = (
                _get_field_attr(field, "displayName")
                or _get_field_attr(field, "display_name")
                or field_name
            )

            # 从请求中获取字段值
            field_value = request_dict.get(field_name)

            if required and (field_value is None or field_value == ""):
                missing_required_fields.append(display_name)
            elif field_value is not None and field_value != "":
                entity_data[field_name] = field_value

        # 如果有必填字段缺失，记录警告但不阻止注册
        if missing_required_fields:
            logger.warning(f"用户 {user.username} 缺少必填字段: {', '.join(missing_required_fields)}，跳过实体记录创建")
            return

        # 创建实体数据记录
        result = entity_service.create_entity_data(role_code, entity_data)

        if result.get("success"):
            logger.info(f"为用户 {user.username} 创建 {role_code} 实体记录成功")
        else:
            logger.error(f"为用户 {user.username} 创建 {role_code} 实体记录失败: {result.get('details')}")

    except Exception as e:
        logger.error(f"创建角色实体记录时发生错误: {str(e)}")
        # 不抛出异常，避免影响用户注册流程
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """密码哈希"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户"""
    try:
        token = credentials.credentials
        verify_result = jwt_handler.verify_token(
            token,
            expected_user_type="user",
            expected_token_type="access",
            check_session=True,
        )
        if not verify_result["valid"]:
            raise UnifiedResponse.unauthorized(
                message="无效的token",
                error_type=verify_result.get("error", "invalid_token")
            )

        payload = verify_result.get("payload", {})
        user_id = payload.get("user_id")
        
        if not user_id:
            raise UnifiedResponse.unauthorized(
                message="无效的token",
                error_type="invalid_token"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnifiedResponse.unauthorized(
                message="用户不存在",
                error_type="user_not_found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception:
        raise UnifiedResponse.unauthorized(
            message="无效的token",
            error_type="invalid_token"
        )


@router.post("/register", response_model=UserResponse)
async def register_user(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册

    创建新用户账户，根据注册配置分配默认角色
    """
    try:
        # 动态获取注册配置
        from app.models.role import RoleDBModel
        from app.config import settings

        # 从配置中读取注册设置
        allow_public_registration = settings.ALLOW_PUBLIC_REGISTRATION
        default_role_code = settings.DEFAULT_REGISTER_ROLE_CODE

        logger.info(f"注册配置 - 允许公开注册: {allow_public_registration}, 默认角色: {default_role_code}")

        # 检查是否允许公开注册
        if not allow_public_registration:
            raise UnifiedResponse.forbidden(
                message="当前不允许公开注册，请联系管理员",
                error_type="registration_disabled"
            )

        # 检查用户名是否已存在
        query_filters = [User.username == request.username]
        if request.email:
            query_filters.append(User.email == request.email)

        existing_user = db.query(User).filter(
            *query_filters
        ).first()

        if existing_user:
            if existing_user.username == request.username:
                raise UnifiedResponse.conflict(
                    message="用户名已存在",
                    error_type="username_exists"
                )
            elif request.email and existing_user.email == request.email:
                raise UnifiedResponse.conflict(
                    message="邮箱已存在",
                    error_type="email_exists"
                )

        # 获取配置的默认角色
        default_role = db.query(RoleDBModel).filter(RoleDBModel.code == default_role_code).first()
        if not default_role:
            # 如果配置的默认角色不存在，使用第一个可用角色
            default_role = db.query(RoleDBModel).filter(RoleDBModel.status == "active").first()
            if not default_role:
                raise UnifiedResponse.internal_error(
                    message="系统角色配置错误，请联系管理员",
                    error_type="role_config_error"
                )
            logger.warning(f"配置的默认角色 {default_role_code} 不存在，使用角色 {default_role.code}")

        # 验证角色是否激活
        if default_role.status != "active":
            raise UnifiedResponse.internal_error(
                message="默认注册角色未激活，请联系管理员",
                error_type="role_inactive"
            )
        
        # 创建新用户
        hashed_password = hash_password(request.password)
        new_user = User(
            username=request.username,
            email=request.email,
            password_hash=hashed_password,
            phone=request.phone,
            real_name=request.real_name,
            role_id=request.role_id or default_role.id,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # 获取用户角色信息
        user_role = db.query(RoleDBModel).filter(RoleDBModel.id == new_user.role_id).first()

        # 更新角色的用户数量统计
        if user_role:
            user_role.user_count = (user_role.user_count or 0) + 1
            db.commit()

        # 创建对应的角色实体数据记录
        if user_role:
            await _create_role_entity_record(new_user, request, user_role.code, db)
        
        return UnifiedResponse.created(
            message="注册成功",
            data={
                "user_id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "role": {
                    "id": user_role.id,
                    "name": user_role.name,
                    "code": user_role.code
                },
                "created_at": new_user.created_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        db.rollback()
        raise UnifiedResponse.internal_error(
            message="注册失败，请稍后重试",
            error_type="registration_failed",
            details=str(e)
        )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    request: UserLoginRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    验证用户凭据，返回访问令牌和权限信息
    """
    try:
        # 查找用户（只使用用户名登录）
        user = db.query(User).filter(User.username == request.username).first()
        
        if not user:
            log_security_event(
                event_type="auth",
                action="user_login",
                actor_type="user",
                actor_id=request.username,
                success=False,
                request=http_request,
                error="invalid_credentials",
                details={"reason": "user_not_found"}
            )
            raise UnifiedResponse.unauthorized(
                message="用户名或密码错误",
                error_type="invalid_credentials"
            )
        
        # 验证密码
        if not verify_password(request.password, user.password_hash):
            log_security_event(
                event_type="auth",
                action="user_login",
                actor_type="user",
                actor_id=str(user.id),
                success=False,
                request=http_request,
                error="invalid_credentials",
                details={"reason": "password_mismatch", "username": request.username}
            )
            raise UnifiedResponse.unauthorized(
                message="用户名或密码错误",
                error_type="invalid_credentials"
            )
        
        # 检查用户状态
        if not user.is_active:
            log_security_event(
                event_type="auth",
                action="user_login",
                actor_type="user",
                actor_id=str(user.id),
                success=False,
                request=http_request,
                error="account_disabled",
                details={"username": request.username}
            )
            raise UnifiedResponse.forbidden(
                message="账户已被禁用",
                error_type="account_disabled"
            )
        
        # 获取用户角色和权限
        user_role = db.query(RoleDBModel).filter(RoleDBModel.id == user.role_id).first()
        if not user_role:
            raise UnifiedResponse.internal_error(
                message="用户角色配置错误",
                error_type="role_config_error"
            )
        
        # 生成访问令牌
        token_data = {
            "user_id": user.id,
            "username": user.username,
            "role_id": user_role.id,
            "role_code": user_role.code,
            "user_type": "user"  # 标记为普通用户token
        }
        token_pair = jwt_handler.create_token_pair(
            data=token_data,
            user_type="user",
        )
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.commit()
        
        # 获取用户可访问的API列表（从数据库动态获取角色权限）
        accessible_apis = permission_service.get_user_accessible_apis(user, db)
        
        log_security_event(
            event_type="auth",
            action="user_login",
            actor_type="user",
            actor_id=str(user.id),
            success=True,
            request=http_request,
            details={
                "username": user.username,
                "role_code": user_role.code,
                "session_id": token_pair.get("session_id")
            }
        )

        return UnifiedResponse.success(
            message="登录成功",
            data={
                "access_token": token_pair["token"],
                "refresh_token": token_pair["refresh_token"],
                "token_type": "bearer",
                "expires_in": token_pair["expires_in"],
                "issued_at": token_pair["issued_at"],
                "expires_at": token_pair["expires_at"],
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "real_name": user.real_name,
                    "role": {
                        "id": user_role.id,
                        "name": user_role.name,
                        "code": user_role.code,
                        "permissions": _get_role_permissions(user_role)
                    }
                },
                "permissions": {
                    "apis": accessible_apis,
                    "features": get_user_features(user_role)
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_security_event(
            event_type="auth",
            action="user_login",
            actor_type="user",
            actor_id=request.username,
            success=False,
            request=http_request,
            error="login_failed",
            details={"reason": str(e)}
        )
        logger.error(f"用户登录失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="登录失败，请稍后重试",
            error_type="login_failed",
            details=str(e)
        )


@router.post("/refresh-token")
async def refresh_user_token(
    http_request: Request,
    request_data: UserTokenRefreshRequest = Body(default_factory=UserTokenRefreshRequest),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db)
):
    """
    刷新用户令牌
    
    优先使用 refresh_token 刷新；为兼容旧客户端，也接受 access token 刷新
    """
    actor_id = "unknown"
    try:
        verify_result: Optional[Dict[str, Any]] = None

        if request_data.refresh_token:
            verify_result = jwt_handler.verify_token(
                request_data.refresh_token,
                expected_user_type="user",
                expected_token_type="refresh",
                check_session=True,
            )
            if not verify_result["valid"]:
                raise UnifiedResponse.unauthorized(
                    message="刷新令牌无效",
                    error_type=verify_result.get("error", "invalid_refresh_token")
                )
        elif credentials and credentials.credentials:
            verify_result = jwt_handler.verify_token(
                credentials.credentials,
                expected_user_type="user",
                expected_token_type="access",
                check_session=True,
            )
            if not verify_result["valid"]:
                raise UnifiedResponse.unauthorized(
                    message="访问令牌无效",
                    error_type=verify_result.get("error", "invalid_token")
                )
        else:
            raise UnifiedResponse.bad_request(
                message="缺少刷新凭据",
                error_type="missing_credentials",
                details="请传入 refresh_token 或 Authorization 访问令牌"
            )

        payload = verify_result.get("payload", {}) if verify_result else {}
        user_id = payload.get("user_id") or payload.get("sub")
        actor_id = str(user_id)
        current_user = db.query(User).filter(User.id == user_id).first()
        if not current_user:
            raise UnifiedResponse.unauthorized(
                message="用户不存在",
                error_type="user_not_found"
            )
        if not current_user.is_active:
            raise UnifiedResponse.forbidden(
                message="账户已被禁用",
                error_type="account_disabled"
            )

        # 获取用户角色
        user_role = db.query(RoleDBModel).filter(RoleDBModel.id == current_user.role_id).first()
        if not user_role:
            raise UnifiedResponse.internal_error(
                message="用户角色配置错误",
                error_type="role_config_error"
            )
        
        # 生成新的访问令牌（沿用原会话ID）
        token_data = {
            "user_id": current_user.id,
            "username": current_user.username,
            "role_id": user_role.id,
            "role_code": user_role.code,
            "user_type": "user"
        }
        token_pair = jwt_handler.create_token_pair(
            data=token_data,
            user_type="user",
            session_id=verify_result.get("session_id") if verify_result else None,
        )

        # refresh token 轮换：使用 refresh_token 刷新时吊销旧 jti
        if verify_result and verify_result.get("token_type") == "refresh":
            refresh_exp = payload.get("exp")
            token_session_service.revoke_token_jti(
                jti=verify_result.get("jti"),
                exp_ts=float(refresh_exp) if refresh_exp is not None else None,
                reason="user_refresh_rotation"
            )

        log_security_event(
            event_type="auth",
            action="user_refresh_token",
            actor_type="user",
            actor_id=str(current_user.id),
            success=True,
            request=http_request,
            details={"session_id": token_pair.get("session_id")}
        )
        
        return UnifiedResponse.success(
            message="令牌刷新成功",
            data={
                "access_token": token_pair["token"],
                "refresh_token": token_pair["refresh_token"],
                "token_type": "bearer",
                "expires_in": token_pair["expires_in"],
                "issued_at": token_pair["issued_at"],
                "expires_at": token_pair["expires_at"],
            }
        )
        
    except HTTPException as exc:
        log_security_event(
            event_type="auth",
            action="user_refresh_token",
            actor_type="user",
            actor_id=actor_id,
            success=False,
            request=http_request,
            error="token_refresh_denied",
            details={"reason": str(exc.detail)}
        )
        raise
    except Exception as e:
        log_security_event(
            event_type="auth",
            action="user_refresh_token",
            actor_type="user",
            actor_id=actor_id,
            success=False,
            request=http_request,
            error="token_refresh_failed",
            details={"reason": str(e)}
        )
        logger.error(f"刷新用户令牌失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="刷新令牌失败，请重新登录",
            error_type="token_refresh_failed",
            details=str(e)
        )


@router.post("/logout")
async def logout_user(
    http_request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user)
):
    """
    用户登出
    
    使当前token失效
    """
    try:
        verify_result = jwt_handler.verify_token(
            credentials.credentials,
            expected_user_type="user",
            expected_token_type="access",
            check_session=False
        )
        if verify_result["valid"]:
            payload = verify_result.get("payload", {})
            sid = verify_result.get("session_id") or payload.get("sid")
            jti = verify_result.get("jti") or payload.get("jti")
            exp_ts = payload.get("exp")
            if sid:
                token_session_service.revoke_session(str(sid), reason="user_logout")
            token_session_service.revoke_token_jti(
                jti=str(jti) if jti else None,
                exp_ts=float(exp_ts) if exp_ts is not None else None,
                reason="user_logout",
            )

        log_security_event(
            event_type="auth",
            action="user_logout",
            actor_type="user",
            actor_id=str(current_user.id),
            success=True,
            request=http_request,
            details={"username": current_user.username}
        )
        
        return UnifiedResponse.success(
            message="登出成功",
            data={
                "logged_out_at": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        log_security_event(
            event_type="auth",
            action="user_logout",
            actor_type="user",
            actor_id=str(current_user.id) if current_user else "unknown",
            success=False,
            request=http_request,
            error="logout_failed",
            details={"reason": str(e)}
        )
        logger.error(f"用户登出失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="登出失败，请稍后重试",
            error_type="logout_failed",
            details=str(e)
        )


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户信息
    
    返回当前登录用户的详细信息
    """
    try:
        user_role = db.query(RoleDBModel).filter(RoleDBModel.id == current_user.role_id).first()
        
        return UnifiedResponse.success(
            message="获取成功",
            data={
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "real_name": current_user.real_name,
                "phone": current_user.phone,
                "role": {
                    "id": user_role.id,
                    "name": user_role.name,
                    "code": user_role.code
                },
                "created_at": current_user.created_at.isoformat(),
                "last_login": current_user.last_login.isoformat() if current_user.last_login else None
            }
        )
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="获取用户信息失败",
            error_type="get_profile_failed",
            details=str(e)
        )


def _get_role_permissions(role: RoleDBModel) -> List[str]:
    """获取角色权限列表"""
    try:
        # 从角色的权限关联中获取权限
        permissions = []
        for permission in role.permissions:
            permissions.append(permission.name)

        # 如果没有关联权限，根据角色代码返回默认权限
        if not permissions:
            if role.code == "super_admin":
                permissions = ["*:*"]
            elif role.code in ["admin", "manager"]:
                permissions = ["user:*", "data:*", "report:read"]
            elif role.code in ["doctor", "nurse", "regular_user", "vip_user"]:
                permissions = ["user:read", "user:update_self", "data:query"]
            else:  # 访客
                permissions = ["user:read"]

        return permissions

    except Exception:
        return ["user:read"]  # 默认最小权限


def get_user_features(role: RoleDBModel) -> List[str]:
    """获取用户可用功能列表"""
    features = ["profile_management"]

    # 根据角色代码分配功能
    if role.code in ["regular_user", "vip_user", "admin", "super_admin"]:
        features.extend(["ai_interaction", "data_query"])

    if role.code in ["admin", "super_admin"]:
        features.extend(["user_management", "system_config"])

    return features
