"""
认证模块数据模型
严格按照API文档定义的请求响应格式
"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# 通用响应模型
class APIResponse(BaseModel):
    """统一API响应格式"""
    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[Any] = Field(default=None, description="响应数据")


# 开发者认证请求模型
class DeveloperAuthRequest(BaseModel):
    """开发者认证请求"""
    password: str = Field(..., description="开发者密码")


# 开发者认证响应数据模型
class DeveloperAuthData(BaseModel):
    """开发者认证响应数据"""
    token: str = Field(..., description="JWT访问令牌")
    refresh_token: str = Field(..., description="JWT刷新令牌")
    expires_in: int = Field(..., description="令牌有效期（秒）")
    token_type: str = Field(default="Bearer", description="令牌类型")
    issued_at: str = Field(..., description="令牌签发时间（ISO 8601格式）")
    expires_at: str = Field(..., description="令牌过期时间（ISO 8601格式）")


# 开发者认证响应模型
class DeveloperAuthResponse(APIResponse):
    """开发者认证响应"""
    data: DeveloperAuthData


# 令牌刷新请求模型
class TokenRefreshRequest(BaseModel):
    """令牌刷新请求"""
    refresh_token: str = Field(..., description="需要刷新的JWT令牌")


# 令牌验证请求模型
class TokenVerifyRequest(BaseModel):
    """令牌验证请求"""
    token: str = Field(..., description="需要验证的JWT令牌")


# 令牌验证响应数据模型（成功）
class TokenVerifySuccessData(BaseModel):
    """令牌验证成功响应数据"""
    valid: bool = Field(default=True, description="令牌是否有效")
    user_type: str = Field(default="developer", description="用户类型")
    issued_at: str = Field(..., description="令牌签发时间（ISO 8601格式）")
    expires_at: str = Field(..., description="令牌过期时间（ISO 8601格式）")
    remaining_time: int = Field(..., description="剩余有效时间（秒）")


# 令牌验证响应数据模型（失败）
class TokenVerifyFailData(BaseModel):
    """令牌验证失败响应数据"""
    valid: bool = Field(default=False, description="令牌是否有效")
    error: str = Field(..., description="错误类型")
    details: str = Field(..., description="错误详情")


# 令牌验证响应模型
class TokenVerifyResponse(APIResponse):
    """令牌验证响应"""
    data: Optional[TokenVerifySuccessData | TokenVerifyFailData] = None


# 错误响应数据模型
class ErrorData(BaseModel):
    """错误响应数据"""
    error: str = Field(..., description="错误类型")
    details: Any = Field(..., description="错误详情")


# 错误响应模型
class ErrorResponse(APIResponse):
    """错误响应"""
    data: ErrorData
