"""
角色管理Pydantic模型
定义API请求和响应的数据结构
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class RoleStatus(str, Enum):
    """角色状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    LOCKED = "locked"


class PermissionBase(BaseModel):
    """权限基础模型"""
    name: str = Field(..., description="权限名称（如：products:read）")
    description: Optional[str] = Field(None, description="权限描述")
    resource: str = Field(..., description="资源名称")
    action: str = Field(..., description="操作类型")


class Permission(PermissionBase):
    """权限完整模型"""
    id: str = Field(..., description="权限唯一标识符")
    is_system: bool = Field(False, description="是否为系统权限")
    is_active: bool = Field(True, description="是否激活")
    metadata: Optional[Dict[str, Any]] = Field(None, description="权限元数据")
    granted_at: Optional[str] = Field(None, description="授权时间")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class RoleCreateRequest(BaseModel):
    """创建角色请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="角色名称")
    code: str = Field(..., min_length=1, max_length=50, description="角色代码（唯一标识）")
    description: Optional[str] = Field(None, max_length=1000, description="角色描述")
    status: Optional[RoleStatus] = Field(RoleStatus.ACTIVE, description="角色状态")
    permissions: Optional[List[str]] = Field([], description="初始权限列表")
    metadata: Optional[Dict[str, Any]] = Field({}, description="角色元数据")
    
    @validator('code')
    def validate_code(cls, v):
        """验证角色代码格式"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('角色代码只能包含字母、数字、下划线和连字符')
        return v.lower()
    
    @validator('permissions')
    def validate_permissions(cls, v):
        """验证权限格式"""
        if v:
            for perm in v:
                if ':' not in perm:
                    raise ValueError(f'权限格式错误: {perm}，应为 resource:action 格式')
        return v


class RoleUpdateRequest(BaseModel):
    """更新角色请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="角色名称")
    description: Optional[str] = Field(None, max_length=1000, description="角色描述")
    status: Optional[RoleStatus] = Field(None, description="角色状态")
    metadata: Optional[Dict[str, Any]] = Field(None, description="角色元数据")


class UserInfo(BaseModel):
    """用户信息模型"""
    id: str = Field(..., description="用户ID")
    name: str = Field(..., description="用户名称")
    email: str = Field(..., description="用户邮箱")
    status: str = Field(..., description="用户状态")
    assigned_at: str = Field(..., description="分配时间")


class RoleStatistics(BaseModel):
    """角色统计信息模型"""
    user_count: int = Field(0, description="关联用户数量")
    permission_count: int = Field(0, description="权限数量")
    active_users: int = Field(0, description="活跃用户数量")
    last_login: Optional[str] = Field(None, description="最后登录时间")


class Role(BaseModel):
    """角色完整模型"""
    id: str = Field(..., description="角色唯一标识符")
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色代码")
    description: Optional[str] = Field(None, description="角色描述")
    status: str = Field(..., description="角色状态")
    user_count: int = Field(0, description="关联用户数量")
    permission_count: int = Field(0, description="权限数量")
    permissions: Optional[List[Permission]] = Field(None, description="权限列表")
    users: Optional[List[UserInfo]] = Field(None, description="关联用户列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="角色元数据")
    statistics: Optional[RoleStatistics] = Field(None, description="统计信息")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class RoleListItem(BaseModel):
    """角色列表项模型"""
    id: str = Field(..., description="角色唯一标识符")
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色代码")
    description: Optional[str] = Field(None, description="角色描述")
    status: str = Field(..., description="角色状态")
    user_count: int = Field(0, description="关联用户数量")
    permission_count: int = Field(0, description="权限数量")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class RolePagination(BaseModel):
    """角色分页信息模型"""
    page: int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页数量")
    total: int = Field(..., description="总数量")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class RoleSummary(BaseModel):
    """角色汇总信息模型"""
    total_roles: int = Field(..., description="总角色数")
    active_roles: int = Field(..., description="活跃角色数")
    inactive_roles: int = Field(..., description="非活跃角色数")
    total_users: int = Field(..., description="总用户数")
    avg_permissions_per_role: float = Field(..., description="平均每个角色的权限数")


class RolePermissionsRequest(BaseModel):
    """角色权限分配请求模型"""
    permissions: List[str] = Field(..., description="权限列表")
    replace: bool = Field(False, description="是否替换现有权限")
    
    @validator('permissions')
    def validate_permissions(cls, v):
        """验证权限格式"""
        for perm in v:
            if ':' not in perm:
                raise ValueError(f'权限格式错误: {perm}，应为 resource:action 格式')
        return v


class PermissionsSummary(BaseModel):
    """权限汇总信息模型"""
    total_permissions: int = Field(..., description="总权限数")
    by_resource: Dict[str, int] = Field(..., description="按资源分组的权限数")
    by_action: Dict[str, int] = Field(..., description="按操作分组的权限数")


class RolePermissionsResponse(BaseModel):
    """角色权限响应模型"""
    role: Dict[str, str] = Field(..., description="角色基本信息")
    permissions: List[Permission] = Field(..., description="权限列表")
    summary: PermissionsSummary = Field(..., description="权限汇总")


class RolePermissionAssignResponse(BaseModel):
    """角色权限分配响应模型"""
    role: Dict[str, str] = Field(..., description="角色基本信息")
    permissions: Dict[str, Any] = Field(..., description="权限变更信息")


class RoleDeleteResponse(BaseModel):
    """角色删除响应模型"""
    role_id: str = Field(..., description="角色ID")
    name: str = Field(..., description="角色名称")
    deleted_at: str = Field(..., description="删除时间")
    affected_users: int = Field(..., description="受影响的用户数")
    reassigned_to: Optional[str] = Field(None, description="重新分配到的角色ID")


class PermissionRemoveResponse(BaseModel):
    """权限移除响应模型"""
    role: Dict[str, str] = Field(..., description="角色基本信息")
    permission: Dict[str, str] = Field(..., description="被移除的权限信息")
    removed_at: str = Field(..., description="移除时间")


# API响应模型
class RoleCreateResponse(BaseModel):
    """创建角色响应模型"""
    code: int = Field(201, description="响应码")
    message: str = Field("角色创建成功", description="响应消息")
    data: Dict[str, Role] = Field(..., description="响应数据")


class RoleListResponse(BaseModel):
    """角色列表响应模型"""
    code: int = Field(200, description="响应码")
    message: str = Field("获取角色列表成功", description="响应消息")
    data: Dict[str, Any] = Field(..., description="响应数据")


class RoleDetailResponse(BaseModel):
    """角色详情响应模型"""
    code: int = Field(200, description="响应码")
    message: str = Field("获取角色详情成功", description="响应消息")
    data: Dict[str, Role] = Field(..., description="响应数据")


class RoleUpdateResponse(BaseModel):
    """角色更新响应模型"""
    code: int = Field(200, description="响应码")
    message: str = Field("角色更新成功", description="响应消息")
    data: Dict[str, Role] = Field(..., description="响应数据")


class RoleDeleteResponseModel(BaseModel):
    """角色删除响应模型"""
    code: int = Field(200, description="响应码")
    message: str = Field("角色删除成功", description="响应消息")
    data: RoleDeleteResponse = Field(..., description="响应数据")


class RolePermissionsResponseModel(BaseModel):
    """角色权限响应模型"""
    code: int = Field(200, description="响应码")
    message: str = Field("获取角色权限成功", description="响应消息")
    data: RolePermissionsResponse = Field(..., description="响应数据")


class RolePermissionAssignResponseModel(BaseModel):
    """角色权限分配响应模型"""
    code: int = Field(200, description="响应码")
    message: str = Field("权限分配成功", description="响应消息")
    data: RolePermissionAssignResponse = Field(..., description="响应数据")


class PermissionRemoveResponseModel(BaseModel):
    """权限移除响应模型"""
    code: int = Field(200, description="响应码")
    message: str = Field("角色权限移除成功", description="响应消息")
    data: PermissionRemoveResponse = Field(..., description="响应数据")
