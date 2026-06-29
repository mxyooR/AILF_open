"""
Auth Core Package
统一导出 JWT 处理器与开发者认证依赖，避免多份实现逻辑不一致。
"""

from .jwt_handler import JWTHandler, jwt_handler, verify_developer_token

__all__ = ["JWTHandler", "jwt_handler", "verify_developer_token"]

