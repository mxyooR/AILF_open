"""
实体建模数据库模型
定义实体、字段、关系、数据记录等数据库表结构
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, JSON, TIMESTAMP, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.core.database import Base


class EntityDBModel(Base):
    """实体数据库模型"""
    __tablename__ = "entities"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text)
    icon = Column(String(100))
    status = Column(String(20), default="active")
    is_role = Column(Boolean, default=False, comment="是否为角色实体")
    field_count = Column(Integer, default=0)
    record_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    # 关系
    fields = relationship("EntityFieldDBModel", back_populates="entity", cascade="all, delete-orphan")
    source_relationships = relationship("EntityRelationshipDBModel", 
                                      foreign_keys="EntityRelationshipDBModel.source_entity_id",
                                      back_populates="source_entity", 
                                      cascade="all, delete-orphan")
    target_relationships = relationship("EntityRelationshipDBModel", 
                                      foreign_keys="EntityRelationshipDBModel.target_entity_id",
                                      back_populates="target_entity")
    # 注意：records关系已移除，实体数据现在存储在独立的entity_{name}表中
    
    # 索引
    __table_args__ = (
        Index('idx_entities_name', 'name'),
        Index('idx_entities_status', 'status'),
    )


class EntityFieldDBModel(Base):
    """实体字段数据库模型"""
    __tablename__ = "entity_fields"
    
    id = Column(String(50), primary_key=True)
    entity_id = Column(String(50), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    display_name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)
    required = Column(Boolean, default=False)
    unique_field = Column(Boolean, default=False)
    default_value = Column(Text)
    validation = Column(JSON)
    options = Column(JSON)
    aliases = Column(JSON)
    sort_order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    # 关系
    entity = relationship("EntityDBModel", back_populates="fields")
    
    # 索引
    __table_args__ = (
        Index('idx_entity_fields_entity', 'entity_id'),
        Index('idx_entity_fields_type', 'type'),
        Index('unique_field_name_per_entity', 'entity_id', 'name', unique=True),
    )


class EntityRelationshipDBModel(Base):
    """实体关系数据库模型"""
    __tablename__ = "entity_relationships"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    source_entity_id = Column(String(50), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    target_entity_id = Column(String(50), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # one-to-one, one-to-many, many-to-many, hierarchy
    foreign_key = Column(String(100))
    constraints = Column(JSON)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    # 关系
    source_entity = relationship("EntityDBModel", 
                               foreign_keys=[source_entity_id],
                               back_populates="source_relationships")
    target_entity = relationship("EntityDBModel", 
                               foreign_keys=[target_entity_id],
                               back_populates="target_relationships")
    
    # 索引
    __table_args__ = (
        Index('idx_relationships_source', 'source_entity_id'),
        Index('idx_relationships_target', 'target_entity_id'),
        Index('idx_relationships_type', 'type'),
    )


# 注意：EntityRecordDBModel已废弃
# 实体数据现在存储在独立的entity_{name}表中，由EntityService动态创建和管理
# 保留此注释以便了解历史设计


# 字段类型枚举
FIELD_TYPES = [
    "text",        # 文本字段
    "number",      # 数字字段
    "decimal",     # 小数字段
    "boolean",     # 布尔字段
    "date",        # 日期字段
    "datetime",    # 日期时间字段
    "email",       # 邮箱字段
    "phone",       # 电话字段
    "select",      # 单选字段
    "multiselect", # 多选字段
    "image",       # 图片字段
    "file",        # 文件字段
]

# 关系类型枚举
RELATIONSHIP_TYPES = [
    "one-to-one",    # 一对一关系
    "one-to-many",   # 一对多关系
    "many-to-many",  # 多对多关系
    "hierarchy",     # 层级关系
]

# 实体状态枚举
ENTITY_STATUS = [
    "active",      # 活跃状态
    "inactive",    # 非活跃状态
    "draft",       # 草稿状态
    "archived",    # 已归档状态
]
