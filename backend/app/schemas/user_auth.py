"""
用户认证相关的Pydantic模型
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str
    email: Optional[EmailStr] = None
    password: str
    phone: Optional[str] = None
    real_name: Optional[str] = None
    role_id: Optional[str] = None

    class Config:
        # 允许额外字段，用于动态接收角色实体的字段
        extra = "allow"

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 20:
            raise ValueError('用户名长度必须在3-20字符之间')
        if not v.isalnum() and '_' not in v:
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6 or len(v) > 20:
            raise ValueError('密码长度必须在6-20字符之间')
        return v


class AdminCreateUserRequest(BaseModel):
    """管理员创建用户请求"""
    username: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    real_name: Optional[str] = None
    role_id: str  # 管理员创建用户时必须指定角色
    is_active: Optional[bool] = True

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 20:
            raise ValueError('用户名长度必须在3-20字符之间')
        if not v.isalnum() and '_' not in v:
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6 or len(v) > 20:
            raise ValueError('密码长度必须在6-20字符之间')
        return v


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str  # 用户名（主键）
    password: str


class RoleInfo(BaseModel):
    """角色信息"""
    id: int
    name: str
    level: int
    permissions: Optional[List[str]] = []


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    email: str
    real_name: Optional[str] = None
    role: RoleInfo


class APIInfo(BaseModel):
    """API信息"""
    endpoint: str
    method: str
    description: str
    resource: Optional[str] = None
    action: Optional[str] = None


class PermissionInfo(BaseModel):
    """权限信息"""
    apis: List[APIInfo]
    features: List[str]


class UserResponse(BaseModel):
    """用户注册响应"""
    code: int
    message: str
    data: Dict[str, Any]


class LoginResponse(BaseModel):
    """登录响应"""
    code: int
    message: str
    data: Dict[str, Any]


class UserProfileResponse(BaseModel):
    """用户资料响应"""
    code: int
    message: str
    data: Dict[str, Any]


class PermissionsResponse(BaseModel):
    """权限查询响应"""
    code: int
    message: str
    data: Dict[str, Any]


class TokenRefreshResponse(BaseModel):
    """Token刷新响应"""
    code: int
    message: str
    data: Dict[str, Any]


class UserTokenRefreshRequest(BaseModel):
    """用户刷新令牌请求"""
    refresh_token: Optional[str] = None


class UserUpdateRequest(BaseModel):
    """用户信息更新请求"""
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class PasswordChangeRequest(BaseModel):
    """密码修改请求"""
    old_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6 or len(v) > 20:
            raise ValueError('新密码长度必须在6-20字符之间')
        return v
