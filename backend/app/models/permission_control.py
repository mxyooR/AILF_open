"""
权限控制模型
定义API映射、权限配置和权限检查相关的数据结构
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class APIEndpointDBModel(Base):
    """API端点模型 - 定义系统中所有的API端点"""
    __tablename__ = "api_endpoints"
    
    # 基本信息
    id = Column(String(50), primary_key=True, comment="API端点唯一标识符")
    name = Column(String(100), nullable=False, comment="API端点名称")
    endpoint = Column(String(200), nullable=False, comment="API端点路径")
    method = Column(String(10), nullable=False, comment="HTTP方法")
    
    # 权限信息
    resource = Column(String(50), nullable=False, comment="资源名称")
    action = Column(String(50), nullable=False, comment="操作类型")
    permission = Column(String(100), nullable=False, comment="所需权限")
    
    # 配置信息
    description = Column(Text, nullable=True, comment="API描述")
    is_public = Column(Boolean, default=False, comment="是否为公开API")
    is_active = Column(Boolean, default=True, comment="是否启用")
    min_role_level = Column(Integer, default=1, comment="最低角色级别要求")
    
    # 元数据
    api_metadata = Column(JSON, nullable=True, comment="API元数据")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    role_api_permissions = relationship("RoleAPIPermissionDBModel", back_populates="api_endpoint")


class RoleAPIPermissionDBModel(Base):
    """角色API权限模型 - 定义角色对API的访问权限"""
    __tablename__ = "role_api_permissions"
    
    # 主键
    id = Column(String(50), primary_key=True, comment="权限记录唯一标识符")
    
    # 外键关联
    role_id = Column(String(50), ForeignKey('roles.id'), nullable=False, comment="角色ID")
    api_id = Column(String(50), ForeignKey('api_endpoints.id'), nullable=False, comment="API端点ID")
    
    # 权限信息
    permission_name = Column(String(100), nullable=False, comment="权限名称")
    is_granted = Column(Boolean, default=True, comment="是否授予权限")
    
    # 条件权限
    conditions = Column(JSON, nullable=True, comment="权限条件")
    
    # 操作信息
    granted_by = Column(String(50), nullable=True, comment="授权人ID")
    granted_at = Column(DateTime, default=func.now(), comment="授权时间")
    expires_at = Column(DateTime, nullable=True, comment="权限过期时间")
    
    # 元数据
    permission_metadata = Column(JSON, nullable=True, comment="权限元数据")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    # role = relationship("RoleDBModel", back_populates="api_permissions")
    api_endpoint = relationship("APIEndpointDBModel", back_populates="role_api_permissions")


class PermissionCheckLogDBModel(Base):
    """权限检查日志模型 - 记录权限检查历史"""
    __tablename__ = "permission_check_logs"
    
    # 基本信息
    id = Column(String(50), primary_key=True, comment="日志唯一标识符")
    user_id = Column(String(50), nullable=False, comment="用户ID")
    
    # 检查信息
    resource = Column(String(50), nullable=False, comment="请求资源")
    action = Column(String(50), nullable=False, comment="请求操作")
    permission_required = Column(String(100), nullable=False, comment="所需权限")
    
    # 检查结果
    is_allowed = Column(Boolean, nullable=False, comment="是否允许访问")
    granted_by_role = Column(String(50), nullable=True, comment="授权角色")
    denial_reason = Column(Text, nullable=True, comment="拒绝原因")
    
    # 上下文信息
    request_context = Column(JSON, nullable=True, comment="请求上下文")
    user_roles = Column(JSON, nullable=True, comment="用户角色列表")
    
    # 时间戳
    checked_at = Column(DateTime, default=func.now(), comment="检查时间")
    
    # 请求信息
    ip_address = Column(String(45), nullable=True, comment="请求IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")


def create_permission_control_tables(engine):
    """创建权限控制相关的数据库表"""
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)
    
    try:
        logger.info("创建权限控制数据库表...")
        
        # 创建表
        Base.metadata.create_all(engine, tables=[
            APIEndpointDBModel.__table__,
            RoleAPIPermissionDBModel.__table__,
            PermissionCheckLogDBModel.__table__
        ])
        
        logger.info("✅ 权限控制数据库表创建成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 权限控制数据库表创建失败: {e}")
        return False


def init_default_api_endpoints(db):
    """初始化默认的API端点配置"""
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)
    
    try:
        logger.info("初始化默认API端点配置...")
        
        # 检查是否已有API端点数据
        existing_count = db.query(APIEndpointDBModel).count()
        if existing_count > 0:
            logger.info(f"✅ API端点数据已存在 ({existing_count} 个)")
            return True
        
        # 默认API端点配置
        default_apis = [
            # 前端实际使用的API端点
            {
                "id": "user_profile_api",
                "name": "用户资料管理API",
                "endpoint": "/api/users/profile",
                "method": "GET",
                "resource": "users",
                "action": "profile",
                "permission": "users:profile",
                "description": "获取和管理用户资料信息",
                "is_public": False,
                "min_role_level": 1
            },
            {
                "id": "doc_test_api",
                "name": "文档测试API",
                "endpoint": "/api/doc/test",
                "method": "GET",
                "resource": "doc",
                "action": "test",
                "permission": "doc:test",
                "description": "文档测试和验证功能",
                "is_public": False,
                "min_role_level": 1
            },
            # 测试API定义已删除
        ]
        
        # 创建API端点记录
        created_count = 0
        for api_data in default_apis:
            api_endpoint = APIEndpointDBModel(**api_data)
            db.add(api_endpoint)
            created_count += 1
        
        db.commit()
        logger.info(f"✅ 成功创建 {created_count} 个默认API端点")
        return True
        
    except Exception as e:
        logger.error(f"❌ 初始化默认API端点失败: {e}")
        db.rollback()
        return False
