"""
API路由管理模块Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from datetime import datetime
import uuid


class RouteStatus(str, Enum):
    """路由状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"
    TESTING = "testing"


class HandlerType(str, Enum):
    """处理器类型枚举"""
    ENTITY_CRUD = "entity_crud"
    CUSTOM_FUNCTION = "custom_function"
    PROXY = "proxy"
    WORKFLOW = "workflow"
    STATIC_DATA = "static_data"
    SCRIPT = "script"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    IMAGE_DISPLAY = "image_display"
    MEDIA_STREAMING = "media_streaming"


class ParameterLocation(str, Enum):
    """参数位置枚举"""
    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    BODY = "body"


# 统一响应格式相关模型
class ResponseMeta(BaseModel):
    """响应元信息模型 - 与 core/response.py 保持一致"""
    timestamp: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp() * 1000), description="响应时间戳(毫秒)")
    request_id: Optional[str] = Field(None, description="请求唯一标识")
    execution_time: Optional[int] = Field(None, description="处理耗时(ms)")


class StandardResponse(BaseModel):
    """标准响应格式"""
    code: int = Field(..., description="HTTP状态码对应的业务码")
    message: str = Field(..., description="人类可读的消息描述")
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]], Any]] = Field(None, description="实际的响应数据")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="响应元信息")


class ErrorDetails(BaseModel):
    """错误详情模型"""
    field_errors: Optional[Dict[str, List[str]]] = Field(None, description="字段级错误")
    global_errors: Optional[List[str]] = Field(None, description="全局错误")
    conflicting_endpoint: Optional[str] = Field(None, description="冲突的端点")
    conflicting_method: Optional[str] = Field(None, description="冲突的方法")
    existing_route: Optional[Dict[str, Any]] = Field(None, description="已存在的路由")
    required_permissions: Optional[List[str]] = Field(None, description="所需权限")
    user_permissions: Optional[List[str]] = Field(None, description="用户权限")
    resource_type: Optional[str] = Field(None, description="资源类型")
    resource_id: Optional[str] = Field(None, description="资源ID")
    conflict_reason: Optional[str] = Field(None, description="冲突原因")
    limit: Optional[int] = Field(None, description="限制数量")
    window: Optional[str] = Field(None, description="时间窗口")
    reset_at: Optional[str] = Field(None, description="重置时间")
    upstream_service: Optional[str] = Field(None, description="上游服务")
    last_success: Optional[str] = Field(None, description="最后成功时间")
    reason: Optional[str] = Field(None, description="错误原因")
    estimated_resume: Optional[str] = Field(None, description="预计恢复时间")
    error_id: Optional[str] = Field(None, description="错误ID")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    code: int = Field(..., description="错误状态码")
    message: str = Field(..., description="错误消息")
    data: Dict[str, Any] = Field(..., description="错误数据")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="响应元信息")

    @staticmethod
    def create_error(
        code: int,
        message: str,
        error_type: str,
        details: Optional[ErrorDetails] = None,
        suggestion: Optional[str] = None,
        error_code: Optional[str] = None
    ) -> "ErrorResponse":
        """创建标准错误响应"""
        meta = ResponseMeta()
        if error_code:
            meta.error_code = error_code
            
        data = {
            "error_type": error_type,
            "details": details.dict(exclude_none=True) if details else {},
        }
        if suggestion:
            data["suggestion"] = suggestion
            
        return ErrorResponse(
            code=code,
            message=message,
            data=data,
            meta=meta
        )


# 表单配置相关模型
class FormLayout(BaseModel):
    """表单布局配置"""
    type: str = Field(default="vertical", description="布局类型")
    columns: Optional[int] = Field(1, description="列数")
    spacing: Optional[int] = Field(16, description="间距")


class FormSection(BaseModel):
    """表单分组"""
    title: str = Field(..., description="分组标题")
    fields: List[str] = Field(..., description="字段列表")
    collapsible: Optional[bool] = Field(False, description="是否可折叠")


class FormConfig(BaseModel):
    """表单配置模型"""
    auto_generate: bool = Field(True, description="是否自动生成表单")
    fields: Optional[List[str]] = Field(None, description="表单字段列表")
    layout: Optional[FormLayout] = Field(None, description="表单布局")
    sections: Optional[List[FormSection]] = Field(None, description="表单分组")


class RouteParameter(BaseModel):
    """路由参数模型"""
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型")
    location: ParameterLocation = Field(..., description="参数位置")
    required: bool = Field(False, description="是否必填")
    description: Optional[str] = Field(None, description="参数描述")
    validation: Optional[Dict[str, Any]] = Field(None, description="验证配置")
    default: Optional[str] = Field(None, description="默认值")


class RouteResponse(BaseModel):
    """路由响应模型"""
    description: str = Field(..., description="响应描述")
    response_schema: Optional[Dict[str, Any]] = Field(None, description="响应Schema", alias="schema")
    headers: Optional[Dict[str, str]] = Field(None, description="响应头")

    class Config:
        populate_by_name = True


class RouteHandler(BaseModel):
    """路由处理器模型"""
    type: HandlerType = Field(..., description="处理器类型")
    config: Dict[str, Any] = Field(..., description="处理器配置")


# 动态响应配置相关模型
class DynamicResponseCondition(BaseModel):
    """动态响应条件模型"""
    type: str = Field(..., description="条件类型：parameter, header, user_role, time, random, data_count")
    field: Optional[str] = Field(None, description="字段名称（适用于parameter、header类型）", alias="field_name")
    operator: str = Field(..., description="操作符：eq, ne, gt, gte, lt, lte, in, not_in, contains, exists, not_exists")
    value: Union[str, int, float, List[str]] = Field(..., description="比较值")

    class Config:
        populate_by_name = True


class ResponseTemplate(BaseModel):
    """响应模板模型"""
    status_code: int = Field(200, description="HTTP状态码")
    body_template: Dict[str, Any] = Field(..., description="响应体模板")
    headers: Optional[Dict[str, str]] = Field(None, description="响应头")


class DynamicResponseRule(BaseModel):
    """动态响应规则模型"""
    id: Optional[str] = Field(None, description="规则ID")
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    priority: int = Field(1, description="优先级，数值越高优先级越高")
    enabled: bool = Field(True, description="是否启用")
    conditions: List[DynamicResponseCondition] = Field(..., description="条件列表")
    response_template: ResponseTemplate = Field(..., description="响应模板", alias="template")

    class Config:
        populate_by_name = True


# 权限配置模型
class RoutePermission(BaseModel):
    """路由权限配置模型"""
    resource: str = Field(..., description="资源名称（如: products, orders, users）")
    action: str = Field(..., description="操作类型（如: read, create, update, delete, *）")
    description: Optional[str] = Field(None, description="权限描述")


class RoutePermissionConfig(BaseModel):
    """路由权限配置"""
    required_permissions: Optional[List[RoutePermission]] = Field([], description="所需权限列表（任一权限满足即可访问）")
    required_roles: Optional[List[str]] = Field([], description="所需角色列表（任一角色满足即可访问）")
    min_role_level: Optional[int] = Field(None, description="最低角色级别（1-10）")
    allow_developer: bool = Field(True, description="是否允许开发者访问")


# API路由管理相关模型
class APIRouteRegisterRequest(BaseModel):
    """注册API路由请求"""
    api_id: str = Field(..., min_length=1, max_length=100, description="API标识符")
    name: str = Field(..., min_length=1, max_length=200, description="路由名称")
    endpoint: str = Field(..., min_length=1, max_length=500, description="API端点")
    method: str = Field(..., description="HTTP方法")
    description: Optional[str] = Field(None, description="路由描述")
    auth_required: bool = Field(True, description="是否需要认证")
    permission_config: Optional[RoutePermissionConfig] = Field(None, description="权限配置")
    handler: RouteHandler = Field(..., description="处理器配置")
    parameters: Optional[List[RouteParameter]] = Field([], description="参数列表")
    responses: Dict[str, RouteResponse] = Field(..., description="响应配置")
    form_config: Optional[FormConfig] = Field(None, description="表单配置")
    dynamic_rules: Optional[List[DynamicResponseRule]] = Field([], description="动态响应规则")


class APIRouteUpdateRequest(BaseModel):
    """更新API路由请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="路由名称")
    endpoint: Optional[str] = Field(None, min_length=1, max_length=500, description="API端点")
    method: Optional[str] = Field(None, description="HTTP方法")
    description: Optional[str] = Field(None, description="路由描述")
    auth_required: Optional[bool] = Field(None, description="是否需要认证")
    permission_config: Optional[RoutePermissionConfig] = Field(None, description="权限配置")
    handler: Optional[RouteHandler] = Field(None, description="处理器配置")
    parameters: Optional[List[RouteParameter]] = Field(None, description="参数列表")
    responses: Optional[Dict[str, RouteResponse]] = Field(None, description="响应配置")
    form_config: Optional[FormConfig] = Field(None, description="表单配置")


class APIRouteStatusRequest(BaseModel):
    """路由状态请求"""
    status: RouteStatus = Field(..., description="路由状态")


# 统计信息模型
class RouteStatistics(BaseModel):
    """路由统计信息"""
    call_count: int = Field(0, description="调用次数")
    successful_calls: int = Field(0, description="成功调用次数")
    failed_calls: int = Field(0, description="失败调用次数")
    success_rate: float = Field(0.0, description="成功率")
    avg_response_time: int = Field(0, description="平均响应时间(ms)")
    last_called: Optional[str] = Field(None, description="最后调用时间")


class RoutePerformance(BaseModel):
    """路由性能信息"""
    health_status: str = Field("unknown", description="健康状态")
    response_time_trend: str = Field("stable", description="响应时间趋势")
    error_rate: float = Field(0.0, description="错误率")


class AssociatedForm(BaseModel):
    """关联表单信息"""
    id: str = Field(..., description="表单ID")
    name: str = Field(..., description="表单名称")
    field_count: int = Field(0, description="字段数量")
    created_at: str = Field(..., description="创建时间")


class APIRouteListItem(BaseModel):
    """API路由列表项模型"""
    id: str = Field(..., description="路由ID")
    api_id: str = Field(..., description="API标识符")
    name: str = Field(..., description="路由名称")
    endpoint: str = Field(..., description="API端点")
    method: str = Field(..., description="HTTP方法")
    description: Optional[str] = Field(None, description="路由描述")
    auth_required: bool = Field(..., description="是否需要认证")
    status: RouteStatus = Field(..., description="路由状态")
    handler_type: HandlerType = Field(..., description="处理器类型")
    statistics: Optional[RouteStatistics] = Field(None, description="统计信息")
    performance: Optional[RoutePerformance] = Field(None, description="性能信息")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class APIRoute(BaseModel):
    """API路由模型"""
    id: str = Field(..., description="路由ID")
    api_id: str = Field(..., description="API标识符")
    name: str = Field(..., description="路由名称")
    endpoint: str = Field(..., description="API端点")
    method: str = Field(..., description="HTTP方法")
    description: Optional[str] = Field(None, description="路由描述")
    auth_required: bool = Field(..., description="是否需要认证")
    status: RouteStatus = Field(..., description="路由状态")
    handler: RouteHandler = Field(..., description="处理器配置")
    parameters: List[RouteParameter] = Field([], description="参数列表")
    responses: Dict[str, RouteResponse] = Field(..., description="响应配置")
    access_url: Optional[str] = Field(None, description="访问URL")
    statistics: Optional[RouteStatistics] = Field(None, description="统计信息")
    performance: Optional[RoutePerformance] = Field(None, description="性能信息")
    associated_forms: Optional[List[AssociatedForm]] = Field([], description="关联表单")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


# 响应模型
class APIRouteRegisterResponse(StandardResponse):
    """API路由注册响应"""
    pass


class APIRouteListResponse(StandardResponse):
    """API路由列表响应"""
    pass


class APIRouteDetailResponse(StandardResponse):
    """API路由详情响应"""
    pass


class APIRouteHealthResponse(StandardResponse):
    """API路由健康检查响应"""
    pass


# 分页模型
class PaginationInfo(BaseModel):
    """分页信息"""
    page: int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页数量")
    total: int = Field(..., description="总记录数")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")
    next_page: Optional[int] = Field(None, description="下一页页码")
    prev_page: Optional[int] = Field(None, description="上一页页码")


class RouteSummary(BaseModel):
    """路由汇总信息"""
    total_routes: int = Field(0, description="总路由数")
    active_routes: int = Field(0, description="活跃路由数")
    inactive_routes: int = Field(0, description="非活跃路由数")
    maintenance_routes: int = Field(0, description="维护路由数")
    total_calls: int = Field(0, description="总调用次数")
    total_successful_calls: int = Field(0, description="总成功调用次数")
    overall_success_rate: float = Field(0.0, description="整体成功率")
    avg_response_time: int = Field(0, description="平均响应时间")
    healthy_routes: int = Field(0, description="健康路由数")
    warning_routes: int = Field(0, description="警告路由数")
    unhealthy_routes: int = Field(0, description="不健康路由数")


# 健康检查相关模型
class HealthCheckItem(BaseModel):
    """健康检查项"""
    name: str = Field(..., description="检查项名称")
    status: str = Field(..., description="检查状态")
    response_time: Optional[int] = Field(None, description="响应时间")


class ActivationDetails(BaseModel):
    """激活详情"""
    health_check: Dict[str, Any] = Field(..., description="健康检查结果")
    warm_up: Dict[str, Any] = Field(..., description="预热结果")
    dependencies: Dict[str, str] = Field(..., description="依赖状态")


class AccessInfo(BaseModel):
    """访问信息"""
    url: str = Field(..., description="访问URL")
    method: str = Field(..., description="HTTP方法")
    auth_required: bool = Field(..., description="是否需要认证")
    rate_limit: Optional[str] = Field(None, description="限流配置")
    documentation: Optional[str] = Field(None, description="文档链接")


class APIRouteHealthStatus(BaseModel):
    """API路由健康状态"""
    route_id: str = Field(..., description="路由ID")
    api_id: str = Field(..., description="API标识符")
    name: str = Field(..., description="路由名称")
    endpoint: str = Field(..., description="端点")
    status: str = Field(..., description="健康状态")
    response_time: Optional[int] = Field(None, description="响应时间")
    last_check: str = Field(..., description="最后检查时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    success_rate: float = Field(..., description="成功率")
    uptime: Optional[str] = Field(None, description="运行时间")
