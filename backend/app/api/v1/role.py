"""
角色管理API路由
实现8个角色管理相关的API端点
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional

from app.core.auth import verify_developer_token
from app.core.permissions import require_permission_or_guest
from app.services.role_service import RoleService
from app.services.security_audit_service import log_security_event
from app.schemas.role import (
    RoleCreateRequest, RoleUpdateRequest, RolePermissionsRequest
)
from app.core.response import UnifiedResponse

from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/roles", tags=["角色管理"])

# 创建服务实例
role_service = RoleService()


@router.post("", response_model=dict, status_code=201)
async def create_role(
    request: RoleCreateRequest,
    current_user: dict = Depends(verify_developer_token)
):
    """
    创建新的用户角色

    - **name**: 角色名称
    - **code**: 角色代码（唯一标识）
    - **description**: 角色描述
    - **status**: 角色状态（active/inactive）
    - **permissions**: 初始权限列表
    - **metadata**: 角色元数据
    """
    result = role_service.create_role(request, current_user.get("user_id"))
    
    if not result["success"]:
        if result["error"] == "role_code_exists":
            raise UnifiedResponse.conflict(
                message="角色代码已存在",
                error_type=result["error"],
                details={
                    "details": result["details"],
                    "existing_role": result.get("existing_role")
                }
            )
        else:
            raise UnifiedResponse.internal_error(
                message="创建角色失败",
                error_type=result["error"],
                details=result["details"]
            )
    
    return UnifiedResponse.created(
        message="角色创建成功",
        data=result["data"]
    )


@router.get("", response_model=dict)
async def get_roles_list(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    limit: int = Query(50, ge=1, le=100, description="每页数量，最大100"),
    status: Optional[str] = Query(None, description="角色状态筛选：active, inactive"),
    search: Optional[str] = Query(None, description="搜索角色名称或代码"),
    current_user: dict = Depends(verify_developer_token)
):
    """
    获取角色列表

    支持分页、状态筛选和搜索功能
    """
    # 记录访问日志 - 装饰器已经处理了权限验证
    logger.info(f"角色列表访问请求 - 页码: {page}, 限制: {limit}")

    result = role_service.get_roles_list(
        page=page,
        limit=limit,
        status=status
    )
    
    if not result["success"]:
        raise UnifiedResponse.internal_error(
            message="获取角色列表失败",
            error_type=result["error"],
            details=result["details"]
        )
    
    return UnifiedResponse.success(
        message="获取角色列表成功",
        data=result["data"]
    )


@router.get("/{role_id}", response_model=dict)
async def get_role_detail(
    role_id: str,
    current_user: dict = Depends(verify_developer_token)
):
    """
    获取角色详细信息
    
    包括角色基本信息、权限列表、关联用户等
    """
    result = role_service.get_role_detail(role_id)
    
    if not result["success"]:
        if result["error"] == "role_not_found":
            raise UnifiedResponse.not_found(
                message="角色不存在",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="获取角色详情失败",
                error_type=result["error"],
                details=result["details"]
            )
    
    return UnifiedResponse.success(
        message="获取角色详情成功",
        data=result["data"]
    )


@router.put("/{role_id}", response_model=dict)
async def update_role(
    role_id: str,
    request: RoleUpdateRequest,
    current_user: dict = Depends(verify_developer_token)
):
    """
    更新角色信息
    
    可以更新角色的基本信息，但不包括权限（权限需要单独API）
    """
    result = role_service.update_role(role_id, request, current_user.get("user_id"))
    
    if not result["success"]:
        if result["error"] == "role_not_found":
            raise UnifiedResponse.not_found(
                message="角色不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] == "role_code_exists":
            raise UnifiedResponse.conflict(
                message="角色代码已存在",
                error_type=result["error"],
                details={
                    "details": result["details"],
                    "existing_role": result.get("existing_role")
                }
            )
        else:
            raise UnifiedResponse.internal_error(
                message="更新角色失败",
                error_type=result["error"],
                details=result["details"]
            )
    
    return UnifiedResponse.success(
        message="角色更新成功",
        data=result["data"]
    )


@router.delete("/{role_id}", response_model=dict)
async def delete_role(
    role_id: str,
    force: bool = Query(False, description="是否强制删除（即使有关联用户）"),
    current_user: dict = Depends(verify_developer_token)
):
    """
    删除角色
    
    默认情况下，如果角色有关联用户则不能删除，除非使用force参数
    """
    result = role_service.delete_role(role_id, force, current_user.get("user_id"))
    
    if not result["success"]:
        if result["error"] == "role_not_found":
            raise UnifiedResponse.not_found(
                message="角色不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] == "role_has_users":
            raise UnifiedResponse.bad_request(
                message="角色有关联用户，无法删除",
                error_type=result["error"],
                details={
                    "details": result["details"],
                    "user_count": result.get("user_count")
                },
                suggestion="请先移除关联用户或使用force参数强制删除"
            )
        else:
            raise UnifiedResponse.internal_error(
                message="删除角色失败",
                error_type=result["error"],
                details=result["details"]
            )
    
    return UnifiedResponse.success(
        message="角色删除成功",
        data=result["data"]
    )


@router.get("/{role_id}/permissions", response_model=dict)
async def get_role_permissions(
    role_id: str,
    current_user: dict = Depends(verify_developer_token)
):
    """
    获取角色权限列表
    
    返回角色的所有权限，包括直接权限和继承权限
    """
    result = role_service.get_role_permissions(role_id)
    
    if not result["success"]:
        if result["error"] == "role_not_found":
            raise UnifiedResponse.not_found(
                message="角色不存在",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="获取角色权限失败",
                error_type=result["error"],
                details=result["details"]
            )
    
    return UnifiedResponse.success(
        message="获取角色权限成功",
        data=result["data"]
    )


@router.put("/{role_id}/permissions", response_model=dict)
async def update_role_permissions(
    http_request: Request,
    role_id: str,
    request: RolePermissionsRequest,
    current_user: dict = Depends(verify_developer_token)
):
    """
    更新角色权限
    
    完全替换角色的权限列表
    """
    result = role_service.assign_permissions(
        role_id,
        request,
        current_user.get("user_id")
    )
    
    if not result["success"]:
        log_security_event(
            event_type="permission",
            action="update_role_permissions",
            actor_type="developer",
            actor_id=str(current_user.get("user_id", "developer")),
            success=False,
            request=http_request,
            target_type="role",
            target_id=str(role_id),
            error=result.get("error"),
            details={"reason": result.get("details")}
        )
        if result["error"] == "role_not_found":
            raise UnifiedResponse.not_found(
                message="角色不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] == "invalid_permissions":
            raise UnifiedResponse.bad_request(
                message="无效的权限配置",
                error_type=result["error"],
                details={
                    "details": result["details"],
                    "invalid_permissions": result.get("invalid_permissions")
                }
            )
        else:
            raise UnifiedResponse.internal_error(
                message="更新角色权限失败",
                error_type=result["error"],
                details=result["details"]
            )
    
    log_security_event(
        event_type="permission",
        action="update_role_permissions",
        actor_type="developer",
        actor_id=str(current_user.get("user_id", "developer")),
        success=True,
        request=http_request,
        target_type="role",
        target_id=str(role_id),
        details={"permission_count": len(request.permissions)}
    )
    return UnifiedResponse.success(
        message="角色权限更新成功",
        data=result["data"]
    )


