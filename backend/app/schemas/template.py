"""
模板管理模块数据模型
严格按照API文档定义的请求响应格式
"""
from datetime import datetime
from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field
from enum import Enum


# 模板分类枚举
class TemplateCategory(str, Enum):
    BUSINESS = "business"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    HOSPITALITY = "hospitality"
    FINANCE = "finance"
    LOGISTICS = "logistics"
    GOVERNMENT = "government"
    CUSTOM = "custom"


# 难度等级枚举
class TemplateDifficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# 模板预览信息模型
class TemplatePreview(BaseModel):
    """模板预览信息"""
    entities: int = Field(..., description="实体数量")
    workflows: int = Field(..., description="工作流数量")
    forms: int = Field(..., description="表单数量")
    apis: int = Field(..., description="API数量")


# 模板基础信息模型
class TemplateBase(BaseModel):
    """模板基础信息"""
    key: str = Field(..., description="模板唯一标识符")
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    category: TemplateCategory = Field(..., description="模板分类")
    difficulty: TemplateDifficulty = Field(..., description="难度等级")
    estimated_setup_time: str = Field(..., description="预估配置时间")
    features: List[str] = Field(..., description="主要功能列表")
    tags: List[str] = Field(..., description="标签列表")
    created_at: str = Field(..., description="创建时间（ISO 8601格式）")
    updated_at: str = Field(..., description="更新时间（ISO 8601格式）")


# 模板列表项模型
class TemplateListItem(TemplateBase):
    """模板列表项"""
    preview: Optional[TemplatePreview] = Field(None, description="预览信息")


# 分类统计模型
class CategoryStats(BaseModel):
    """分类统计"""
    key: str = Field(..., description="分类标识")
    name: str = Field(..., description="分类名称")
    count: int = Field(..., description="模板数量")


# 模板列表响应数据模型
class TemplateListData(BaseModel):
    """模板列表响应数据"""
    templates: List[TemplateListItem] = Field(..., description="模板列表")
    total: int = Field(..., description="总数量")
    categories: List[CategoryStats] = Field(..., description="分类统计")


# 模板列表响应模型
class TemplateListResponse(BaseModel):
    """模板列表响应"""
    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="获取模板列表成功", description="响应消息")
    data: TemplateListData


# 实体字段验证模型
class FieldValidation(BaseModel):
    """字段验证规则"""
    maxLength: Optional[int] = Field(None, description="最大长度")
    minLength: Optional[int] = Field(None, description="最小长度")
    min: Optional[float] = Field(None, description="最小值")
    max: Optional[float] = Field(None, description="最大值")
    precision: Optional[int] = Field(None, description="精度")
    pattern: Optional[str] = Field(None, description="正则表达式")


# 实体字段模型
class EntityField(BaseModel):
    """实体字段"""
    name: str = Field(..., description="字段名称")
    displayName: str = Field(..., description="显示名称")
    type: str = Field(..., description="字段类型")
    required: bool = Field(default=False, description="是否必填")
    unique: bool = Field(default=False, description="是否唯一")
    defaultValue: Optional[Any] = Field(None, description="默认值")
    options: Optional[List[str]] = Field(None, description="选项列表")
    validation: Optional[FieldValidation] = Field(None, description="验证规则")


# 实体模型
class Entity(BaseModel):
    """实体"""
    name: str = Field(..., description="实体名称")
    displayName: str = Field(..., description="显示名称")
    description: str = Field(..., description="实体描述")
    fields: List[EntityField] = Field(..., description="字段列表")


# 工作流步骤模型
class WorkflowStep(BaseModel):
    """工作流步骤"""
    name: str = Field(..., description="步骤名称")
    type: str = Field(..., description="步骤类型")
    entity: Optional[str] = Field(None, description="关联实体")
    condition: Optional[str] = Field(None, description="条件表达式")
    endpoint: Optional[str] = Field(None, description="API端点")
    recipients: Optional[List[str]] = Field(None, description="通知接收者")


# 工作流模型
class Workflow(BaseModel):
    """工作流"""
    name: str = Field(..., description="工作流名称")
    description: str = Field(..., description="工作流描述")
    steps: List[WorkflowStep] = Field(..., description="步骤列表")


# 表单区域模型
class FormSection(BaseModel):
    """表单区域"""
    title: str = Field(..., description="区域标题")
    fields: List[str] = Field(..., description="字段列表")


# 表单模型
class Form(BaseModel):
    """表单"""
    name: str = Field(..., description="表单名称")
    entity: str = Field(..., description="关联实体")
    layout: str = Field(..., description="布局方式")
    sections: List[FormSection] = Field(..., description="区域列表")


# API模型
class API(BaseModel):
    """API"""
    path: str = Field(..., description="API路径")
    method: str = Field(..., description="HTTP方法")
    description: str = Field(..., description="API描述")


# 角色模型
class Role(BaseModel):
    """角色"""
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色代码")
    permissions: List[str] = Field(..., description="权限列表")


# 场景配置模型
class ScenarioConfig(BaseModel):
    """场景配置"""
    type: str = Field(..., description="场景类型")
    business_domain: str = Field(..., description="业务领域")
    target_users: List[str] = Field(..., description="目标用户")
    key_features: List[str] = Field(..., description="关键功能")
    example_instructions: List[str] = Field(..., description="示例指令")


# 模板配置模型
class TemplateConfig(BaseModel):
    """模板配置"""
    scenario: ScenarioConfig = Field(..., description="场景配置")
    entities: List[Entity] = Field(..., description="实体列表")
    workflows: List[Workflow] = Field(..., description="工作流列表")
    forms: List[Form] = Field(..., description="表单列表")
    apis: List[API] = Field(..., description="API列表")
    roles: List[Role] = Field(..., description="角色列表")


# 设置指南模型
class SetupGuide(BaseModel):
    """设置指南"""
    steps: List[str] = Field(..., description="设置步骤")
    prerequisites: List[str] = Field(..., description="前置条件")
    tips: List[str] = Field(..., description="提示信息")


# 模板详情模型
class TemplateDetail(TemplateBase):
    """模板详情"""
    version: str = Field(..., description="版本号")
    author: str = Field(..., description="作者")
    license: str = Field(..., description="许可证")
    config: TemplateConfig = Field(..., description="模板配置")
    setup_guide: SetupGuide = Field(..., description="设置指南")


# 模板详情响应数据模型
class TemplateDetailData(BaseModel):
    """模板详情响应数据"""
    template: TemplateDetail = Field(..., description="模板详情")


# 模板详情响应模型
class TemplateDetailResponse(BaseModel):
    """模板详情响应"""
    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="获取模板详情成功", description="响应消息")
    data: TemplateDetailData


# 错误响应数据模型
class TemplateErrorData(BaseModel):
    """模板错误响应数据"""
    error: str = Field(..., description="错误类型")
    details: str = Field(..., description="错误详情")


# 错误响应模型
class TemplateErrorResponse(BaseModel):
    """模板错误响应"""
    code: int = Field(..., description="响应状态码")
    message: str = Field(..., description="响应消息")
    data: TemplateErrorData
