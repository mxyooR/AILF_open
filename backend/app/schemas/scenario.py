"""
场景管理模块数据模型
严格按照API文档定义的请求响应格式
"""
from datetime import datetime
from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field
from enum import Enum


# 场景类型枚举
class ScenarioType(str, Enum):
    ECOMMERCE = "ecommerce"
    HOSPITAL = "hospital"
    RESTAURANT = "restaurant"
    EDUCATION = "education"
    LOGISTICS = "logistics"
    FINANCE = "finance"
    CUSTOM = "custom"


# 场景状态枚举
class ScenarioStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"


# 场景配置模型
class ScenarioConfig(BaseModel):
    """场景配置"""
    business_domain: str = Field(..., description="业务领域")
    target_users: List[str] = Field(..., description="目标用户群体")
    key_features: List[str] = Field(..., description="关键功能列表")
    example_instructions: List[str] = Field(..., description="示例指令")
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="自定义设置")


# 场景基础信息模型
class ScenarioBase(BaseModel):
    """场景基础信息"""
    name: str = Field(..., description="场景名称")
    type: ScenarioType = Field(..., description="场景类型")
    description: Optional[str] = Field(None, description="场景描述")
    config: ScenarioConfig = Field(..., description="场景配置")


# 场景创建请求模型
class ScenarioCreateRequest(ScenarioBase):
    """创建场景请求"""
    pass


# 场景更新请求模型
class ScenarioUpdateRequest(BaseModel):
    """更新场景请求"""
    name: Optional[str] = Field(None, description="场景名称")
    type: Optional[ScenarioType] = Field(None, description="场景类型")
    description: Optional[str] = Field(None, description="场景描述")
    config: Optional[ScenarioConfig] = Field(None, description="场景配置")


# 场景完整信息模型
class Scenario(ScenarioBase):
    """场景完整信息"""
    id: str = Field(..., description="场景唯一标识符")
    status: ScenarioStatus = Field(default=ScenarioStatus.ACTIVE, description="场景状态")
    template_key: Optional[str] = Field(None, description="模板标识符")
    created_at: str = Field(..., description="创建时间（ISO 8601格式）")
    updated_at: str = Field(..., description="更新时间（ISO 8601格式）")


# 场景响应数据模型
class ScenarioData(BaseModel):
    """场景响应数据"""
    scenario: Scenario


# 场景响应模型
class ScenarioResponse(BaseModel):
    """场景响应"""
    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="success", description="响应消息")
    data: ScenarioData


# 场景验证请求模型
class ScenarioValidateRequest(BaseModel):
    """场景验证请求"""
    scenario_id: str = Field(..., description="场景ID")
    check_dependencies: bool = Field(default=True, description="是否检查依赖")
    check_completeness: bool = Field(default=True, description="是否检查完整性")


# 场景验证检查结果模型
class ValidationChecks(BaseModel):
    """验证检查结果"""
    basic_info: str = Field(..., description="基础信息检查结果")
    entities: str = Field(..., description="实体检查结果")
    workflows: str = Field(..., description="工作流检查结果")
    forms: str = Field(..., description="表单检查结果")
    permissions: str = Field(..., description="权限检查结果")


# 场景验证成功响应数据模型
class ScenarioValidateSuccessData(BaseModel):
    """场景验证成功响应数据"""
    valid: bool = Field(default=True, description="是否有效")
    scenario_id: str = Field(..., description="场景ID")
    checks: ValidationChecks = Field(..., description="检查结果")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    suggestions: List[str] = Field(default_factory=list, description="建议信息")


# 场景验证失败响应数据模型
class ScenarioValidateFailData(BaseModel):
    """场景验证失败响应数据"""
    valid: bool = Field(default=False, description="是否有效")
    scenario_id: str = Field(..., description="场景ID")
    errors: List[str] = Field(..., description="错误信息")
    warnings: List[str] = Field(default_factory=list, description="警告信息")


# 从模板创建场景请求模型
class ScenarioFromTemplateRequest(BaseModel):
    """从模板创建场景请求"""
    template_key: str = Field(..., description="模板标识符")
    name: str = Field(..., description="场景名称")
    description: Optional[str] = Field(None, description="场景描述")
    customizations: Dict[str, Any] = Field(default_factory=dict, description="自定义配置覆盖")


# 错误响应数据模型
class ScenarioErrorData(BaseModel):
    """场景错误响应数据"""
    error: str = Field(..., description="错误类型")
    details: str = Field(..., description="错误详情")


# 错误响应模型
class ScenarioErrorResponse(BaseModel):
    """场景错误响应"""
    code: int = Field(..., description="响应状态码")
    message: str = Field(..., description="响应消息")
    data: ScenarioErrorData
