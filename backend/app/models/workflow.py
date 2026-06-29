"""
工作流数据库模型 (基于API文档)
只包含工作流定义表，节点信息存储在JSON字段中
完全符合API文档第五部分的数据结构要求
"""
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class WorkflowStatus(enum.Enum):
    """工作流状态枚举 (基于API文档)"""
    DRAFT = "DRAFT"          # 草稿
    ACTIVE = "ACTIVE"        # 活跃
    INACTIVE = "INACTIVE"    # 非活跃
    ARCHIVED = "ARCHIVED"    # 已归档


class WorkflowDBModel(Base):
    """工作流定义表 (基于API文档)"""
    __tablename__ = "workflows"

    # 基本信息 (基于API文档)
    id = Column(String(50), primary_key=True, comment="工作流唯一标识符")
    name = Column(String(200), nullable=False, comment="工作流名称")
    description = Column(Text, comment="工作流描述")
    business_scenario = Column(String(100), comment="业务场景标识")
    status = Column(String(20), nullable=False, default="DRAFT", comment="工作流状态")

    # AI指导配置 (基于API文档)
    user_intents = Column(JSON, comment="用户意图列表")
    trigger_keywords = Column(JSON, comment="触发关键词列表")
    inputs = Column(JSON, comment="工作流输入定义")

    # 节点定义 (基于API文档，JSON存储)
    nodes = Column(JSON, comment="工作流节点定义")

    # 元数据 (基于API文档，使用workflow_metadata避免SQLAlchemy保留字冲突)
    workflow_metadata = Column(JSON, comment="工作流元数据")

    # 创建者信息
    created_by = Column(String(50), comment="创建者ID")

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<WorkflowDBModel(id='{self.id}', name='{self.name}', status='{self.status}')>"
