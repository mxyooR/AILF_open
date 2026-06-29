"""
权限控制API路由
实现6个权限控制相关的API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional

from app.core.auth import verify_developer_token
from app.services.permission_service import PermissionService
from app.services.security_audit_service import log_security_event
from app.schemas.permission_control import (
    PermissionCheckRequest, RoleAPIPermissionRequest, BatchPermissionUpdateRequest
)
from app.core.response import UnifiedResponse

router = APIRouter(prefix="/permissions", tags=["权限控制"])

# 创建服务实例
permission_service = PermissionService()


@router.post("/check", response_model=dict)
async def check_permission(
    request: PermissionCheckRequest,
    current_user: dict = Depends(verify_developer_token)
):
    """
    检查用户是否有访问特定API的权限
    
    - **user_id**: 用户唯一标识符
    - **resource**: 资源名称（如：products, orders）
    - **action**: 操作类型（如：read, create, update, delete）
    - **context**: 上下文信息（可选）
    """
    result = permission_service.check_permission(request, current_user.get("user_id"))
    
    if not result["success"]:
        raise UnifiedResponse.internal_error(
            message="权限检查失败",
            error_type=result["error"],
            details=result["details"]
        )
    
    # 根据权限检查结果返回不同的HTTP状态码
    if result["allowed"]:
        return UnifiedResponse.success(
            message="权限检查完成",
            data=result["data"]
        )
    else:
        raise UnifiedResponse.forbidden(
            message="权限不足",
            error_type="permission_denied",
            details=result["data"]
        )


@router.get("/user-apis", response_model=dict)
async def get_user_apis(
    user_id: str = Query(..., description="用户唯一标识符"),
    resource: Optional[str] = Query(None, description="筛选特定资源的API"),
    method: Optional[str] = Query(None, description="筛选特定HTTP方法的API"),
    include_details: bool = Query(False, description="是否包含API详细信息"),
    _: dict = Depends(verify_developer_token)
):
    """
    获取指定用户可以访问的API列表
    
    - **user_id**: 用户唯一标识符
    - **resource**: 筛选特定资源的API（可选）
    - **method**: 筛选特定HTTP方法的API（可选）
    - **include_details**: 是否包含API详细信息（可选）
    """
    from app.core.database import get_db_session
    from app.models.user import User
    
    try:
        with get_db_session() as db:
            # 获取用户
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UnifiedResponse.not_found(
                    message="用户不存在",
                    error_type="user_not_found",
                    details={"user_id": user_id}
                )
            
            # 获取用户可访问的API列表（使用简化版本）
            accessible_apis = permission_service.get_user_accessible_apis(user, db)
            
            # 根据筛选条件过滤
            if resource:
                accessible_apis = [api for api in accessible_apis if api.get("resource") == resource]
            if method:
                accessible_apis = [api for api in accessible_apis if api.get("method") == method]
            
            # 统计信息
            by_resource = {}
            by_method = {}
            for api in accessible_apis:
                api_resource = api.get("resource", "unknown")
                api_method = api.get("method", "GET")
                by_resource[api_resource] = by_resource.get(api_resource, 0) + 1
                by_method[api_method] = by_method.get(api_method, 0) + 1
            
            # 获取用户权限
            permissions = permission_service.get_user_permissions(user, db)
            
            return UnifiedResponse.success(
                message="获取用户API权限成功",
                data={
                    "user": {
                        "id": user_id,
                        "name": user.username if user else f"用户{user_id}",
                        "roles": [{"id": user.role_id, "name": "用户角色"}] if user and user.role_id else []
                    },
                    "accessible_apis": accessible_apis,
                    "summary": {
                        "total_apis": len(accessible_apis),
                        "by_resource": by_resource,
                        "by_method": by_method,
                        "permissions": permissions
                    }
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="获取用户API权限失败",
            error_type="query_failed",
            details=str(e)
        )


@router.post("/role-api", response_model=dict)
async def update_role_api_permission(
    http_request: Request,
    request: RoleAPIPermissionRequest,
    current_user: dict = Depends(verify_developer_token)
):
    """
    更新角色对特定API的访问权限
    
    - **role_id**: 角色唯一标识符
    - **api_id**: API唯一标识符
    - **permission**: 权限名称（如：products:read）
    - **action**: 操作类型（grant授予，revoke撤销）
    """
    result = permission_service.update_role_api_permission(request, current_user.get("user_id"))
    
    if not result["success"]:
        log_security_event(
            event_type="permission",
            action="update_role_api_permission",
            actor_type="developer",
            actor_id=str(current_user.get("user_id", "developer")),
            success=False,
            request=http_request,
            target_type="role_api_permission",
            target_id=f"{request.role_id}:{request.api_id}:{request.permission}",
            error=result.get("error"),
            details={"action": request.action, "reason": result.get("details")}
        )
        if result["error"] == "role_not_found":
            raise UnifiedResponse.not_found(
                message="角色不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] == "api_not_found":
            raise UnifiedResponse.not_found(
                message="API不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] == "permission_not_found":
            raise UnifiedResponse.not_found(
                message="权限不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] in ["permission_already_granted", "permission_not_granted"]:
            raise UnifiedResponse.bad_request(
                message="权限状态冲突",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="权限更新失败",
                error_type=result["error"],
                details=result["details"]
            )
    
    log_security_event(
        event_type="permission",
        action="update_role_api_permission",
        actor_type="developer",
        actor_id=str(current_user.get("user_id", "developer")),
        success=True,
        request=http_request,
        target_type="role_api_permission",
        target_id=f"{request.role_id}:{request.api_id}:{request.permission}",
        details={"action": request.action}
    )
    return UnifiedResponse.success(
        message="权限更新成功",
        data=result["data"]
    )


@router.post("/batch-update", response_model=dict)
async def batch_update_permissions(
    http_request: Request,
    request: BatchPermissionUpdateRequest,
    current_user: dict = Depends(verify_developer_token)
):
    """
    批量更新多个角色的API权限
    
    - **updates**: 权限更新列表
    - **dry_run**: 是否为试运行模式（可选）
    """
    result = permission_service.batch_update_permissions(request, current_user.get("user_id"))
    
    if not result["success"]:
        log_security_event(
            event_type="permission",
            action="batch_update_permissions",
            actor_type="developer",
            actor_id=str(current_user.get("user_id", "developer")),
            success=False,
            request=http_request,
            target_type="permission_batch",
            target_id="batch",
            error=result.get("error"),
            details={"reason": result.get("details")}
        )
        raise UnifiedResponse.internal_error(
            message="批量权限更新失败",
            error_type=result["error"],
            details=result["details"]
        )
    
    log_security_event(
        event_type="permission",
        action="batch_update_permissions",
        actor_type="developer",
        actor_id=str(current_user.get("user_id", "developer")),
        success=True,
        request=http_request,
        target_type="permission_batch",
        target_id="batch",
        details={"dry_run": request.dry_run, "update_count": len(request.updates)}
    )
    return UnifiedResponse.success(
        message="批量权限更新成功",
        data=result["data"]
    )


@router.get("/matrix", response_model=dict)
async def get_permission_matrix(
    format: str = Query("matrix", description="返回格式（matrix/list）"),
    include_inactive: bool = Query(False, description="是否包含非活跃角色"),
    _: dict = Depends(verify_developer_token)
):
    """
    获取系统的完整权限矩阵
    
    - **format**: 返回格式（matrix/list），默认matrix
    - **include_inactive**: 是否包含非活跃角色，默认false
    """
    result = permission_service.get_permission_matrix(format, include_inactive)
    
    if not result["success"]:
        raise UnifiedResponse.internal_error(
            message="获取权限矩阵失败",
            error_type=result["error"],
            details=result["details"]
        )
    
    return UnifiedResponse.success(
        message="获取权限矩阵成功",
        data=result["data"]
    )


