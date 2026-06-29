"""
实体建模模块数据模型
严格按照API文档定义的请求响应格式
"""
from datetime import datetime
from typing import Any, Optional, List, Dict, Union
from pydantic import BaseModel, Field
from enum import Enum


# 字段类型枚举
class FieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    SELECT = "select"
    MULTISELECT = "multiselect"
    IMAGE = "image"
    FILE = "file"
    REFERENCE = "reference"


# 关系类型枚举
class RelationshipType(str, Enum):
    ONE_TO_ONE = "one-to-one"
    ONE_TO_MANY = "one-to-many"
    MANY_TO_MANY = "many-to-many"
    HIERARCHY = "hierarchy"


# 实体状态枚举
class EntityStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"


# 字段验证规则模型
class FieldValidation(BaseModel):
    """字段验证规则"""
    min: Optional[Union[int, float]] = Field(None, description="最小值")
    max: Optional[Union[int, float]] = Field(None, description="最大值")
    minLength: Optional[int] = Field(None, description="最小长度")
    maxLength: Optional[int] = Field(None, description="最大长度")
    pattern: Optional[str] = Field(None, description="正则表达式")
    precision: Optional[int] = Field(None, description="小数精度")
    minDate: Optional[str] = Field(None, description="最小日期")
    maxDate: Optional[str] = Field(None, description="最大日期")
    format: Optional[str] = Field(None, description="日期格式")


# 实体字段模型
class EntityField(BaseModel):
    """实体字段"""
    id: Optional[str] = Field(None, description="字段唯一标识符")
    name: str = Field(..., description="字段名称")
    displayName: str = Field(..., description="显示名称")
    type: FieldType = Field(..., description="字段类型")
    required: bool = Field(default=False, description="是否必填")
    unique: bool = Field(default=False, description="是否唯一")
    defaultValue: Optional[Any] = Field(None, description="默认值")
    validation: Optional[FieldValidation] = Field(None, description="验证规则")
    options: Optional[List[str]] = Field(None, description="选项列表")
    aliases: Optional[List[str]] = Field(None, description="字段别名列表")
    sort_order: Optional[int] = Field(default=0, description="排序顺序")


# 实体字段创建请求模型
class EntityFieldCreateRequest(BaseModel):
    """创建实体字段请求"""
    name: str = Field(..., description="字段名称")
    displayName: str = Field(..., description="显示名称")
    type: FieldType = Field(..., description="字段类型")
    required: bool = Field(default=False, description="是否必填")
    unique: bool = Field(default=False, description="是否唯一")
    defaultValue: Optional[Any] = Field(None, description="默认值")
    validation: Optional[FieldValidation] = Field(None, description="验证规则")
    options: Optional[List[str]] = Field(None, description="选项列表")
    aliases: Optional[List[str]] = Field(None, description="字段别名列表")


# 关系约束模型
class RelationshipConstraints(BaseModel):
    """关系约束"""
    cascadeDelete: bool = Field(default=False, description="级联删除")
    required: bool = Field(default=False, description="是否必需")
    unique: bool = Field(default=False, description="是否唯一")


# 实体关系模型
class EntityRelationship(BaseModel):
    """实体关系"""
    id: Optional[str] = Field(None, description="关系唯一标识符")
    name: str = Field(..., description="关系名称")
    sourceEntity: Optional[str] = Field(None, description="源实体名称")
    targetEntity: str = Field(..., description="目标实体名称")
    type: RelationshipType = Field(..., description="关系类型")
    foreignKey: Optional[str] = Field(None, description="外键字段")
    constraints: Optional[RelationshipConstraints] = Field(None, description="关系约束")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")


# 实体关系创建请求模型
class EntityRelationshipCreateRequest(BaseModel):
    """创建实体关系请求"""
    name: str = Field(..., description="关系名称")
    targetEntity: str = Field(..., description="目标实体名称")
    type: RelationshipType = Field(..., description="关系类型")
    foreignKey: Optional[str] = Field(None, description="外键字段")
    constraints: Optional[RelationshipConstraints] = Field(None, description="关系约束")


# 实体统计信息模型
class EntityStatistics(BaseModel):
    """实体统计信息"""
    record_count: int = Field(..., description="记录数量")
    field_count: int = Field(..., description="字段数量")
    relationship_count: int = Field(..., description="关系数量")
    last_updated: str = Field(..., description="最后更新时间")


# 实体基础信息模型
class EntityBase(BaseModel):
    """实体基础信息"""
    name: str = Field(..., description="实体名称")
    displayName: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="实体描述")
    icon: Optional[str] = Field(None, description="图标")
    isRole: Optional[bool] = Field(False, description="是否为角色实体")
    scenarioId: Optional[str] = Field(None, description="关联的场景ID")


# 实体创建请求模型
class EntityCreateRequest(EntityBase):
    """创建实体请求"""
    fields: List[EntityFieldCreateRequest] = Field(..., description="字段列表")


# 实体更新请求模型
class EntityUpdateRequest(BaseModel):
    """更新实体请求"""
    displayName: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="实体描述")
    icon: Optional[str] = Field(None, description="图标")
    isRole: Optional[bool] = Field(None, description="是否为角色实体")
    fields: Optional[List[EntityFieldCreateRequest]] = Field(None, description="字段列表")


# 实体完整信息模型
class Entity(EntityBase):
    """实体完整信息"""
    id: str = Field(..., description="实体唯一标识符")
    status: EntityStatus = Field(default=EntityStatus.ACTIVE, description="实体状态")
    field_count: Optional[int] = Field(None, description="字段数量")
    record_count: Optional[int] = Field(None, description="记录数量")
    fields: Optional[List[EntityField]] = Field(None, description="字段列表")
    relationships: Optional[List[EntityRelationship]] = Field(None, description="关系列表")
    statistics: Optional[EntityStatistics] = Field(None, description="统计信息")
    created_at: str = Field(..., description="创建时间（ISO 8601格式）")
    updated_at: str = Field(..., description="更新时间（ISO 8601格式）")


# 实体列表项模型
class EntityListItem(BaseModel):
    """实体列表项"""
    id: str = Field(..., description="实体唯一标识符")
    name: str = Field(..., description="实体名称")
    displayName: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="实体描述")
    icon: Optional[str] = Field(None, description="图标")
    isRole: Optional[bool] = Field(False, description="是否为角色实体")
    status: EntityStatus = Field(..., description="实体状态")
    field_count: int = Field(..., description="字段数量")
    record_count: int = Field(..., description="记录数量")
    fields: Optional[List[EntityField]] = Field(None, description="字段列表")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


# 分页信息模型
class PaginationInfo(BaseModel):
    """分页信息"""
    page: int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页数量")
    total: int = Field(..., description="总记录数")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


# 实体数据记录模型
class EntityRecord(BaseModel):
    """实体数据记录"""
    id: str = Field(..., description="记录唯一标识符")
    data: Dict[str, Any] = Field(..., description="记录数据")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


# 响应数据模型
class EntityListData(BaseModel):
    """实体列表响应数据"""
    entities: List[EntityListItem] = Field(..., description="实体列表")
    total: int = Field(..., description="总数量")


class EntityDetailData(BaseModel):
    """实体详情响应数据"""
    entity: Entity = Field(..., description="实体详情")


class EntityRecordListData(BaseModel):
    """实体记录列表响应数据"""
    records: List[Dict[str, Any]] = Field(..., description="记录列表")
    pagination: PaginationInfo = Field(..., description="分页信息")


class EntityRecordData(BaseModel):
    """实体记录响应数据"""
    record: Dict[str, Any] = Field(..., description="记录数据")


class EntityRelationshipListData(BaseModel):
    """实体关系列表响应数据"""
    relationships: List[EntityRelationship] = Field(..., description="关系列表")
    total: int = Field(..., description="总数量")


class EntityRelationshipData(BaseModel):
    """实体关系响应数据"""
    relationship: EntityRelationship = Field(..., description="关系数据")


# 响应模型
class EntityResponse(BaseModel):
    """实体响应"""
    code: int = Field(..., description="响应状态码")
    message: str = Field(..., description="响应消息")
    data: Union[EntityDetailData, EntityListData, EntityRecordListData, 
                EntityRecordData, EntityRelationshipListData, EntityRelationshipData, Dict[str, Any]]


# 错误响应数据模型
class EntityErrorData(BaseModel):
    """实体错误响应数据"""
    error: str = Field(..., description="错误类型")
    details: Union[str, Dict[str, Any]] = Field(..., description="错误详情")


# 错误响应模型
class EntityErrorResponse(BaseModel):
    """实体错误响应"""
    code: int = Field(..., description="响应状态码")
    message: str = Field(..., description="响应消息")
    data: EntityErrorData
