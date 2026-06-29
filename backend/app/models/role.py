"""
角色管理数据库模型
支持动态数据库表生成和角色权限管理
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.core.database import Base


class Role(Base):
    """简化的角色模型，用于用户认证"""
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True, comment="角色ID")
    name = Column(String(50), unique=True, nullable=False, comment="角色名称")
    description = Column(Text, nullable=True, comment="角色描述")
    permissions = Column(JSON, nullable=True, comment="权限列表")
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 时间字段
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 注意：这个Role类主要用于简单的角色定义，不直接关联用户
    # 用户关联使用RoleDBModel

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions or [],
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class RoleStatus(Enum):
    """角色状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    LOCKED = "locked"


# 角色权限关联表（多对多关系）
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', String(50), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', String(50), ForeignKey('permissions.id'), primary_key=True),
    Column('granted_at', DateTime, default=func.now()),
    Column('granted_by', String(50), nullable=True),
    extend_existing=True
)

# 用户角色关联表（多对多关系）
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String(50), primary_key=True),  # 移除外键约束，因为users表不存在
    Column('role_id', String(50), ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime, default=func.now()),
    Column('assigned_by', String(50), nullable=True),
    Column('expires_at', DateTime, nullable=True),
    extend_existing=True
)


class RoleDBModel(Base):
    """角色数据库模型"""
    __tablename__ = 'roles'

    # 基本信息
    id = Column(String(50), primary_key=True, comment="角色唯一标识符")
    name = Column(String(100), nullable=False, comment="角色名称")
    code = Column(String(50), nullable=False, unique=True, comment="角色代码（唯一标识）")
    description = Column(Text, nullable=True, comment="角色描述")
    status = Column(String(20), nullable=False, default=RoleStatus.ACTIVE.value, comment="角色状态")
    
    # 元数据和配置
    role_metadata = Column(JSON, nullable=True, comment="角色元数据")
    
    # 统计信息
    user_count = Column(Integer, default=0, comment="关联用户数量")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(50), nullable=True, comment="创建者")
    updated_by = Column(String(50), nullable=True, comment="更新者")
    
    # 关系定义
    permissions = relationship(
        "PermissionDBModel",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin"  # 修改为selectin，返回列表而不是查询对象
    )
    # api_permissions = relationship("app.models.permission_control.RoleAPIPermissionDBModel", back_populates="role")
    
    # 索引
    __table_args__ = (
        {'comment': '角色表'}
    )


class PermissionDBModel(Base):
    """权限数据库模型"""
    __tablename__ = 'permissions'
    
    # 基本信息
    id = Column(String(50), primary_key=True, comment="权限唯一标识符")
    name = Column(String(100), nullable=False, unique=True, comment="权限名称（如：products:read）")
    description = Column(Text, nullable=True, comment="权限描述")
    resource = Column(String(50), nullable=False, comment="资源名称")
    action = Column(String(50), nullable=False, comment="操作类型")
    
    # 权限配置
    is_system = Column(Boolean, default=False, comment="是否为系统权限")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 元数据
    permission_metadata = Column(JSON, nullable=True, comment="权限元数据")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系定义
    roles = relationship(
        "RoleDBModel",
        secondary=role_permissions,
        back_populates="permissions",
        lazy="dynamic"
    )
    
    # 索引
    __table_args__ = (
        {'comment': '权限表'}
    )


class RolePermissionLogDBModel(Base):
    """角色权限操作日志模型"""
    __tablename__ = 'role_permission_logs'
    
    # 基本信息
    id = Column(String(50), primary_key=True, comment="日志唯一标识符")
    role_id = Column(String(50), ForeignKey('roles.id'), nullable=False, comment="角色ID")
    permission_id = Column(String(50), ForeignKey('permissions.id'), nullable=False, comment="权限ID")
    
    # 操作信息
    operation = Column(String(20), nullable=False, comment="操作类型（grant/revoke）")
    operator_id = Column(String(50), nullable=True, comment="操作者ID")
    operator_name = Column(String(100), nullable=True, comment="操作者名称")
    
    # 操作详情
    reason = Column(Text, nullable=True, comment="操作原因")
    operation_metadata = Column(JSON, nullable=True, comment="操作元数据")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="操作时间")
    
    # 关系定义
    role = relationship("RoleDBModel", backref="permission_logs")
    permission = relationship("PermissionDBModel", backref="role_logs")
    
    # 索引
    __table_args__ = (
        {'comment': '角色权限操作日志表'}
    )


class UserRoleLogDBModel(Base):
    """用户角色分配日志模型"""
    __tablename__ = 'user_role_logs'
    
    # 基本信息
    id = Column(String(50), primary_key=True, comment="日志唯一标识符")
    user_id = Column(String(50), nullable=False, comment="用户ID")
    role_id = Column(String(50), ForeignKey('roles.id'), nullable=False, comment="角色ID")
    
    # 操作信息
    operation = Column(String(20), nullable=False, comment="操作类型（assign/unassign）")
    operator_id = Column(String(50), nullable=True, comment="操作者ID")
    operator_name = Column(String(100), nullable=True, comment="操作者名称")
    
    # 操作详情
    reason = Column(Text, nullable=True, comment="操作原因")
    expires_at = Column(DateTime, nullable=True, comment="角色过期时间")
    operation_metadata = Column(JSON, nullable=True, comment="操作元数据")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="操作时间")
    
    # 关系定义
    role = relationship("RoleDBModel", backref="user_logs")
    
    # 索引
    __table_args__ = (
        {'comment': '用户角色分配日志表'}
    )


# 动态数据库表生成函数
def create_role_tables(engine):
    """
    动态创建角色相关的数据库表
    
    Args:
        engine: SQLAlchemy引擎实例
    """
    try:
        # 创建所有角色相关的表
        Base.metadata.create_all(
            engine, 
            tables=[
                RoleDBModel.__table__,
                PermissionDBModel.__table__,
                role_permissions,
                user_roles,
                RolePermissionLogDBModel.__table__,
                UserRoleLogDBModel.__table__
            ]
        )
        from app.core.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("✅ 角色管理数据库表创建成功")
        return True
    except Exception as e:
        from app.core.logging_config import get_logger
        logger = get_logger(__name__)
        logger.error(f"❌ 角色管理数据库表创建失败: {e}")
        return False



