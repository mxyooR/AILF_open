"""
权限验证装饰器和中间件
在系统运行时进行真正的角色权限验证
"""
from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Callable, Any, Tuple
from functools import wraps
from app.core.logging_config import get_logger
from app.core.auth.jwt_handler import jwt_handler

from app.core.database import get_db_session
from app.services.permission_service import PermissionService

logger = get_logger(__name__)
security = HTTPBearer()
permission_service = PermissionService()


class PermissionDenied(HTTPException):
    """权限拒绝异常"""
    def __init__(self, detail: str = "权限不足"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _extract_token_from_args(args, kwargs) -> Tuple[Optional[Request], Optional[str]]:
    """
    从函数参数中提取Request对象和token
    
    Returns:
        Tuple[Optional[Request], Optional[str]]: (request对象, token字符串)
    """
    request = None
    credentials = None
    
    # 查找Request和HTTPAuthorizationCredentials参数
    for arg in args:
        if isinstance(arg, Request):
            request = arg
        elif isinstance(arg, HTTPAuthorizationCredentials):
            credentials = arg
    
    for key, value in kwargs.items():
        if isinstance(value, Request):
            request = value
        elif isinstance(value, HTTPAuthorizationCredentials):
            credentials = value
    
    # 获取token
    token = None
    if credentials:
        token = credentials.credentials
    elif request:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # 移除 "Bearer " 前缀
    
    return request, token


def extract_user_from_token(token: str) -> dict:
    """从token中提取用户信息"""
    try:
        verify_result = jwt_handler.verify_token(
            token,
            expected_token_type="access",
            check_session=True,
        )
        if not verify_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"无效的认证令牌: {verify_result.get('error', 'token_invalid')}"
            )

        payload = verify_result.get("payload", {})
        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌: user_id缺失"
            )

        return {
            "user_id": str(user_id),
            "user_type": payload.get("user_type", "user"),
            "name": payload.get("name") or payload.get("username") or "用户"
        }
        
    except Exception as e:
        logger.error(f"Token解析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )


def require_permission(resource: str, action: str, context: Optional[dict] = None):
    """
    权限验证装饰器
    
    Args:
        resource: 资源名称 (如: products, orders, customers)
        action: 操作类型 (如: read, create, update, delete)
        context: 上下文信息 (可选)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从请求中提取token
            request, token = _extract_token_from_args(args, kwargs)
            
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="缺少认证令牌"
                )
            
            # 提取用户信息
            user_info = extract_user_from_token(token)
            
            # 如果是开发者，跳过权限检查
            if user_info.get("user_type") == "developer":
                logger.info(f"开发者访问: {resource}:{action}")
                return await func(*args, **kwargs)
            
            # 进行权限检查
            try:
                with get_db_session() as db:
                    permission_check = permission_service.check_permission(
                        user_id=user_info["user_id"],
                        resource=resource,
                        action=action,
                        context=context or {},
                        db=db
                    )
                    
                    if not permission_check["allowed"]:
                        logger.warning(f"权限拒绝: 用户{user_info['user_id']}尝试访问{resource}:{action}")
                        raise PermissionDenied(
                            detail=f"用户没有'{resource}:{action}'权限"
                        )
                    
                    logger.info(f"权限验证通过: 用户{user_info['user_id']}访问{resource}:{action}")
                    
                    # 将用户信息添加到kwargs中，供API使用
                    kwargs['current_user'] = user_info
                    kwargs['permission_context'] = permission_check
                    
                    return await func(*args, **kwargs)
                    
            except PermissionDenied:
                raise
            except Exception as e:
                logger.error(f"权限检查异常: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="权限检查失败"
                )
        
        return wrapper
    return decorator


def require_permission_or_guest(resource: str, action: str, context: Optional[dict] = None):
    """
    权限验证装饰器 - 支持访客访问

    如果用户已登录，进行正常的权限检查
    如果用户未登录，给予访客权限进行检查

    Args:
        resource: 资源名称 (如: products, orders, customers)
        action: 操作类型 (如: read, create, update, delete)
        context: 上下文信息 (可选)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从请求中提取token
            request, token = _extract_token_from_args(args, kwargs)

            user_info = None
            is_guest = False

            # 如果有token，尝试提取用户信息
            if token:
                try:
                    user_info = extract_user_from_token(token)
                    logger.info(f"已登录用户访问: {user_info.get('user_id')} -> {resource}:{action}")
                except HTTPException as e:
                    # 如果是HTTPException，直接抛出
                    raise e
                except Exception as e:
                    logger.error(f"Token验证失败，拒绝访问: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"无效的认证令牌: {e}"
                    )
            else:
                logger.info(f"未登录用户访问，作为访客处理: {resource}:{action}")
                is_guest = True

            # 如果是访客，创建访客用户信息
            if is_guest or not user_info:
                user_info = {
                    "user_id": "guest",
                    "user_type": "guest",
                    "username": "访客",
                    "role": "guest"
                }
                is_guest = True

            # 如果是开发者，跳过权限检查
            if user_info.get("user_type") == "developer":
                logger.info(f"开发者访问: {resource}:{action}")
                kwargs['current_user'] = user_info
                return await func(*args, **kwargs)

            # 进行权限检查
            try:
                with get_db_session() as db:
                    if is_guest:
                        # 访客权限检查 - 使用guest角色
                        permission_check = permission_service.check_guest_permission(
                            resource=resource,
                            action=action,
                            context=context or {},
                            db=db
                        )
                    else:
                        # 正常用户权限检查
                        permission_check = permission_service.check_permission(
                            user_id=user_info["user_id"],
                            resource=resource,
                            action=action,
                            context=context or {},
                            db=db
                        )

                    if not permission_check["allowed"]:
                        if is_guest:
                            logger.warning(f"访客权限拒绝: 尝试访问{resource}:{action}")
                            raise PermissionDenied(
                                detail=f"访客没有'{resource}:{action}'权限，请登录后重试"
                            )
                        else:
                            logger.warning(f"权限拒绝: 用户{user_info['user_id']}尝试访问{resource}:{action}")
                            raise PermissionDenied(
                                detail=f"用户没有'{resource}:{action}'权限"
                            )

                    if is_guest:
                        logger.info(f"访客权限验证通过: {resource}:{action}")
                    else:
                        logger.info(f"权限验证通过: 用户{user_info['user_id']}访问{resource}:{action}")

                    # 将用户信息存储到请求上下文中，而不是传递给函数
                    # 这样可以避免函数签名问题
                    if request:
                        request.state.current_user = user_info
                        request.state.permission_context = permission_check
                        request.state.is_guest = is_guest

                    return await func(*args, **kwargs)

            except PermissionDenied:
                raise
            except Exception as e:
                logger.error(f"权限检查异常: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="权限检查失败"
                )

        return wrapper
    return decorator


def require_any_permission(permissions: List[tuple], context: Optional[dict] = None):
    """
    要求任一权限的装饰器
    
    Args:
        permissions: 权限列表，每个元素为(resource, action)元组
        context: 上下文信息
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从请求中提取token
            request, token = _extract_token_from_args(args, kwargs)
            
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="缺少认证令牌"
                )
            
            user_info = extract_user_from_token(token)
            
            # 开发者跳过权限检查
            if user_info.get("user_type") == "developer":
                return await func(*args, **kwargs)
            
            # 检查是否有任一权限
            has_permission = False
            permission_results = []
            
            try:
                with get_db_session() as db:
                    for resource, action in permissions:
                        permission_check = permission_service.check_permission(
                            user_id=user_info["user_id"],
                            resource=resource,
                            action=action,
                            context=context or {},
                            db=db
                        )
                        permission_results.append(permission_check)
                        
                        if permission_check["allowed"]:
                            has_permission = True
                            break
                    
                    if not has_permission:
                        required_perms = [f"{r}:{a}" for r, a in permissions]
                        raise PermissionDenied(
                            detail=f"用户需要以下任一权限: {', '.join(required_perms)}"
                        )
                    
                    kwargs['current_user'] = user_info
                    kwargs['permission_results'] = permission_results
                    
                    return await func(*args, **kwargs)
                    
            except PermissionDenied:
                raise
            except Exception as e:
                logger.error(f"权限检查异常: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="权限检查失败"
                )
        
        return wrapper
    return decorator


def require_role_level(min_level: int):
    """
    要求最低角色级别的装饰器
    
    Args:
        min_level: 最低角色级别 (1-10)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从请求中提取token
            request, token = _extract_token_from_args(args, kwargs)
            
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="缺少认证令牌"
                )
            
            user_info = extract_user_from_token(token)
            
            # 开发者跳过级别检查
            if user_info.get("user_type") == "developer":
                return await func(*args, **kwargs)
            
            # 检查用户角色级别
            try:
                with get_db_session() as db:
                    user_roles = permission_service._get_user_roles(user_info["user_id"], db)
                    
                    if not user_roles:
                        raise PermissionDenied("用户没有分配角色")
                    
                    # 根据角色代码计算最高级别
                    max_user_level = 0
                    for role in user_roles:
                        if role["code"] == "super_admin":
                            max_user_level = max(max_user_level, 10)
                        elif role["code"] in ["admin", "manager"]:
                            max_user_level = max(max_user_level, 5)
                        elif role["code"] in ["doctor", "nurse", "regular_user", "vip_user"]:
                            max_user_level = max(max_user_level, 1)
                        else:
                            max_user_level = max(max_user_level, 0)
                    
                    if max_user_level < min_level:
                        raise PermissionDenied(
                            f"需要角色级别 {min_level} 或以上，当前最高级别: {max_user_level}"
                        )
                    
                    kwargs['current_user'] = user_info
                    kwargs['user_roles'] = user_roles
                    kwargs['max_role_level'] = max_user_level
                    
                    return await func(*args, **kwargs)
                    
            except PermissionDenied:
                raise
            except Exception as e:
                logger.error(f"角色级别检查异常: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="角色级别检查失败"
                )
        
        return wrapper
    return decorator
