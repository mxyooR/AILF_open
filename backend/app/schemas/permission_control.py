"""
权限控制Pydantic模型
定义权限检查、权限配置和权限矩阵的请求响应模型
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime


# 权限检查相关模型
class PermissionCheckRequest(BaseModel):
    """权限检查请求模型"""
    user_id: str = Field(..., description="用户唯一标识符")
    resource: str = Field(..., description="资源名称")
    action: str = Field(..., description="操作类型")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class UserInfo(BaseModel):
    """用户信息模型"""
    id: str = Field(..., description="用户ID")
    name: str = Field(..., description="用户名称")
    roles: List[str] = Field(..., description="用户角色列表")


class PermissionInfo(BaseModel):
    """权限信息模型"""
    resource: str = Field(..., description="资源名称")
    action: str = Field(..., description="操作类型")
    permission_name: str = Field(..., description="权限名称")
    granted_by: Optional[str] = Field(None, description="授权来源")


class PermissionCheckResponse(BaseModel):
    """权限检查响应模型"""
    allowed: bool = Field(..., description="是否允许访问")
    user: UserInfo = Field(..., description="用户信息")
    permission: PermissionInfo = Field(..., description="权限信息")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    reason: Optional[str] = Field(None, description="拒绝原因")
    suggestions: Optional[List[str]] = Field(None, description="建议操作")
    checked_at: datetime = Field(..., description="检查时间")


# 用户API访问相关模型
class RoleInfo(BaseModel):
    """角色信息模型"""
    id: str = Field(..., description="角色ID")
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色代码")


class APIInfo(BaseModel):
    """API信息模型"""
    api_id: str = Field(..., description="API唯一标识符")
    name: str = Field(..., description="API名称")
    endpoint: str = Field(..., description="API端点")
    method: str = Field(..., description="HTTP方法")
    resource: str = Field(..., description="资源名称")
    action: str = Field(..., description="操作类型")
    permission: str = Field(..., description="所需权限")
    granted_by: str = Field(..., description="授权来源")


class UserAPIsResponse(BaseModel):
    """用户API访问列表响应模型"""
    user: Dict[str, Any] = Field(..., description="用户信息")
    accessible_apis: List[APIInfo] = Field(..., description="可访问的API列表")
    summary: Dict[str, Any] = Field(..., description="统计信息")


# 权限配置相关模型
class RoleAPIPermissionRequest(BaseModel):
    """角色API权限配置请求模型"""
    role_id: str = Field(..., description="角色唯一标识符")
    api_id: str = Field(..., description="API唯一标识符")
    permission: str = Field(..., description="权限名称")
    action: str = Field(..., pattern="^(grant|revoke)$", description="操作类型：grant授予，revoke撤销")


class PermissionUpdateResult(BaseModel):
    """权限更新结果模型"""
    role_id: str = Field(..., description="角色ID")
    api_id: str = Field(..., description="API ID")
    permission: str = Field(..., description="权限名称")
    action: str = Field(..., description="操作类型")
    status: str = Field(..., description="更新状态")
    message: str = Field(..., description="结果消息")
    error: Optional[str] = Field(None, description="错误代码")


class BatchPermissionUpdateRequest(BaseModel):
    """批量权限更新请求模型"""
    updates: List[RoleAPIPermissionRequest] = Field(..., description="权限更新列表")
    dry_run: bool = Field(False, description="是否为试运行模式")


class BatchPermissionUpdateResponse(BaseModel):
    """批量权限更新响应模型"""
    results: List[PermissionUpdateResult] = Field(..., description="更新结果列表")
    summary: Dict[str, Any] = Field(..., description="汇总信息")


# 权限矩阵相关模型
class PermissionMatrixRole(BaseModel):
    """权限矩阵角色信息"""
    id: str = Field(..., description="角色ID")
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色代码")
    level: int = Field(..., description="角色级别")


class PermissionMatrixAPI(BaseModel):
    """权限矩阵API信息"""
    id: str = Field(..., description="API ID")
    name: str = Field(..., description="API名称")
    endpoint: str = Field(..., description="API端点")
    method: str = Field(..., description="HTTP方法")
    permission: str = Field(..., description="所需权限")


class PermissionMatrix(BaseModel):
    """权限矩阵模型"""
    roles: List[PermissionMatrixRole] = Field(..., description="角色列表")
    apis: List[PermissionMatrixAPI] = Field(..., description="API列表")
    permissions: Dict[str, Dict[str, bool]] = Field(..., description="权限矩阵")


class PermissionMatrixResponse(BaseModel):
    """权限矩阵响应模型"""
    matrix: PermissionMatrix = Field(..., description="权限矩阵")
    statistics: Dict[str, Any] = Field(..., description="统计信息")


class PermissionMatrixUpdateRequest(BaseModel):
    """权限矩阵更新请求模型"""
    matrix: Dict[str, Dict[str, bool]] = Field(..., description="权限矩阵对象")
    merge_mode: str = Field("merge", pattern="^(replace|merge)$", description="合并模式")


class PermissionMatrixUpdateResponse(BaseModel):
    """权限矩阵更新响应模型"""
    updated_permissions: Dict[str, Dict[str, List[str]]] = Field(..., description="更新的权限")
    summary: Dict[str, Any] = Field(..., description="更新汇总")
    updated_at: datetime = Field(..., description="更新时间")


# 通用响应模型
class PermissionControlResponse(BaseModel):
    """权限控制通用响应模型"""
    code: int = Field(..., description="响应代码")
    message: str = Field(..., description="响应消息")
    data: Union[
        PermissionCheckResponse,
        UserAPIsResponse,
        Dict[str, Any],
        PermissionMatrixResponse,
        BatchPermissionUpdateResponse,
        PermissionMatrixUpdateResponse
    ] = Field(..., description="响应数据")


# API端点配置模型
class APIEndpointConfig(BaseModel):
    """API端点配置模型"""
    id: str = Field(..., description="API端点ID")
    name: str = Field(..., description="API端点名称")
    endpoint: str = Field(..., description="API端点路径")
    method: str = Field(..., description="HTTP方法")
    resource: str = Field(..., description="资源名称")
    action: str = Field(..., description="操作类型")
    permission: str = Field(..., description="所需权限")
    description: Optional[str] = Field(None, description="API描述")
    is_public: bool = Field(False, description="是否为公开API")
    is_active: bool = Field(True, description="是否启用")
    min_role_level: int = Field(1, description="最低角色级别要求")
    api_metadata: Optional[Dict[str, Any]] = Field(None, description="API元数据")


# 权限检查日志模型
class PermissionCheckLog(BaseModel):
    """权限检查日志模型"""
    id: str = Field(..., description="日志ID")
    user_id: str = Field(..., description="用户ID")
    resource: str = Field(..., description="请求资源")
    action: str = Field(..., description="请求操作")
    permission_required: str = Field(..., description="所需权限")
    is_allowed: bool = Field(..., description="是否允许访问")
    granted_by_role: Optional[str] = Field(None, description="授权角色")
    denial_reason: Optional[str] = Field(None, description="拒绝原因")
    request_context: Optional[Dict[str, Any]] = Field(None, description="请求上下文")
    user_roles: Optional[List[str]] = Field(None, description="用户角色列表")
    checked_at: datetime = Field(..., description="检查时间")
    ip_address: Optional[str] = Field(None, description="请求IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")


# 权限统计模型
class PermissionStatistics(BaseModel):
    """权限统计模型"""
    total_roles: int = Field(..., description="总角色数")
    total_apis: int = Field(..., description="总API数")
    total_permissions: int = Field(..., description="总权限数")
    granted_permissions: int = Field(..., description="已授予权限数")
    denied_permissions: int = Field(..., description="拒绝权限数")
    coverage: float = Field(..., description="权限覆盖率")
    by_resource: Dict[str, int] = Field(..., description="按资源分组统计")
    by_method: Dict[str, int] = Field(..., description="按HTTP方法分组统计")
    by_role_level: Dict[int, int] = Field(..., description="按角色级别分组统计")
