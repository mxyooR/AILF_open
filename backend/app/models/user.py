"""
用户数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from app.core.database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    real_name = Column(String(50), nullable=True, comment="真实姓名")
    phone = Column(String(20), nullable=True, comment="手机号")
    
    # 角色关联
    role_id = Column(String(50), ForeignKey("roles.id"), nullable=False, comment="角色ID")
    role = relationship("RoleDBModel", backref="users")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_verified = Column(Boolean, default=False, comment="是否已验证邮箱")
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    
    # 扩展字段
    avatar_url = Column(String(255), nullable=True, comment="头像URL")
    bio = Column(Text, nullable=True, comment="个人简介")
    settings = Column(Text, nullable=True, comment="用户设置(JSON)")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "real_name": self.real_name,
            "phone": self.phone,
            "role_id": self.role_id,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "avatar_url": self.avatar_url,
            "bio": self.bio
        }
    
    def has_permission(self, permission: str) -> bool:
        """检查用户是否有指定权限"""
        if not self.role:
            return False
        
        role_permissions = self.role.permissions or []
        return permission in role_permissions
    
    def can_access_api(self, endpoint: str, method: str) -> bool:
        """检查用户是否可以访问指定API"""
        if not self.role:
            return False
        
        # 基于角色权限的简单权限检查
        # 获取角色的权限列表
        role_permissions = [p.name for p in self.role.permissions] if self.role else []
        
        # 所有用户都可以访问的API
        public_apis = [
            ("GET", "/api/user/me"),
            ("POST", "/api/user/logout"),
            ("GET", "/health")
        ]
        
        if (method, endpoint) in public_apis:
            return True
        
        # 检查是否有超级权限
        if "*:*" in role_permissions:
            return True

        # 根据端点检查权限
        # 这里可以根据实际需要扩展更复杂的权限检查逻辑
        endpoint_permission_map = {
            ("POST", "/api/command"): ["ai:command", "user:*"],
            ("GET", "/api/user/permissions"): ["user:read", "user:*"],
            ("GET", "/api/users"): ["users:read", "users:*"],
            ("POST", "/api/users"): ["users:create", "users:*"],
            ("PUT", "/api/users"): ["users:update", "users:*"],
            ("DELETE", "/api/users"): ["users:delete", "users:*"],
            ("GET", "/api/roles"): ["roles:read", "roles:*"]
        }

        required_permissions = endpoint_permission_map.get((method, endpoint), [])

        # 检查是否有任何一个所需权限
        for required_perm in required_permissions:
            if required_perm in role_permissions:
                return True

        return False


class UserSession(Base):
    """用户会话模型"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True, comment="会话ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    token_hash = Column(String(255), nullable=False, comment="Token哈希")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    last_used = Column(DateTime, default=datetime.utcnow, comment="最后使用时间")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 关联
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"
    
    def is_expired(self) -> bool:
        """检查会话是否已过期"""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "is_active": self.is_active,
            "is_expired": self.is_expired()
        }


class UserLoginLog(Base):
    """用户登录日志模型"""
    __tablename__ = "user_login_logs"
    
    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="用户ID")
    username = Column(String(50), nullable=False, comment="用户名")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    
    # 登录结果
    success = Column(Boolean, nullable=False, comment="是否成功")
    failure_reason = Column(String(100), nullable=True, comment="失败原因")
    
    # 时间字段
    login_time = Column(DateTime, default=datetime.utcnow, comment="登录时间")
    
    # 关联
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserLoginLog(id={self.id}, username='{self.username}', success={self.success})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "ip_address": self.ip_address,
            "success": self.success,
            "failure_reason": self.failure_reason,
            "login_time": self.login_time.isoformat() if self.login_time else None
        }
