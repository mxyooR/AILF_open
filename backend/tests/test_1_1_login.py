"""
1.1 登录测试
测试开发者认证API - POST /api/auth/developer
严格按照API文档规范进行测试
"""
import pytest
import sys
import os

# 添加app目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from fastapi.testclient import TestClient
from app.main import create_app
from app.config import settings

# 创建测试客户端
app = create_app()
client = TestClient(app)


class TestDeveloperLogin:
    """开发者登录测试类"""
    
    def test_login_success(self):
        """测试开发者认证成功 - 正确密码"""
        response = client.post(
            "/api/auth/developer",
            json={"password": settings.DEVELOPER_PASSWORD}
        )
        
        # 验证HTTP状态码
        assert response.status_code == 200
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "认证成功"
        assert "data" in data
        
        # 验证token数据字段
        token_data = data["data"]
        required_fields = ["token", "expires_in", "token_type", "issued_at", "expires_at"]
        for field in required_fields:
            assert field in token_data, f"缺少必需字段: {field}"
        
        # 验证字段值
        assert token_data["token_type"] == "Bearer"
        assert token_data["expires_in"] == 3600  # 1小时 = 3600秒
        assert isinstance(token_data["token"], str)
        assert len(token_data["token"]) > 0
        
        # 验证时间格式（ISO 8601）
        import datetime
        try:
            datetime.datetime.fromisoformat(token_data["issued_at"].replace('Z', '+00:00'))
            datetime.datetime.fromisoformat(token_data["expires_at"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("时间格式不符合ISO 8601标准")
    
    def test_login_wrong_password(self):
        """测试开发者认证失败 - 错误密码"""
        response = client.post(
            "/api/auth/developer",
            json={"password": "wrong_password"}
        )
        
        # 验证HTTP状态码
        assert response.status_code == 401
        
        # 验证错误响应结构
        data = response.json()
        assert data["code"] == 401
        assert data["message"] == "密码错误"
        assert "data" in data
        
        # 验证错误数据
        error_data = data["data"]
        assert error_data["error"] == "invalid_password"
        assert error_data["details"] == "提供的密码不正确"
    
    def test_login_empty_password(self):
        """测试开发者认证失败 - 空密码"""
        response = client.post(
            "/api/auth/developer",
            json={"password": ""}
        )
        
        # 验证HTTP状态码
        assert response.status_code == 400
        
        # 验证错误响应结构
        data = response.json()
        assert data["code"] == 400
        assert data["message"] == "请求参数错误"
        assert "data" in data
        
        # 验证错误数据
        error_data = data["data"]
        assert error_data["error"] == "validation_error"
        assert "details" in error_data
        assert "password" in error_data["details"]
        assert "密码不能为空" in error_data["details"]["password"]
    
    def test_login_missing_password_field(self):
        """测试开发者认证失败 - 缺少password字段"""
        response = client.post(
            "/api/auth/developer",
            json={}
        )
        
        # 验证HTTP状态码（FastAPI会返回422 Unprocessable Entity）
        assert response.status_code == 422
    
    def test_login_invalid_json(self):
        """测试开发者认证失败 - 无效JSON格式"""
        response = client.post(
            "/api/auth/developer",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # 验证HTTP状态码
        assert response.status_code == 422
    
    def test_login_content_type_validation(self):
        """测试Content-Type验证"""
        # 正确的Content-Type
        response = client.post(
            "/api/auth/developer",
            json={"password": settings.DEVELOPER_PASSWORD}
        )
        assert response.status_code == 200
        
        # 验证请求头中包含正确的Content-Type
        # 注意：TestClient会自动设置Content-Type为application/json
    
    def test_login_response_time(self):
        """测试响应时间（性能测试）"""
        import time
        
        start_time = time.time()
        response = client.post(
            "/api/auth/developer",
            json={"password": settings.DEVELOPER_PASSWORD}
        )
        end_time = time.time()
        
        # 验证响应成功
        assert response.status_code == 200
        
        # 验证响应时间小于1秒
        response_time = end_time - start_time
        assert response_time < 1.0, f"响应时间过长: {response_time}秒"
    
    def test_login_token_format(self):
        """测试JWT token格式"""
        response = client.post(
            "/api/auth/developer",
            json={"password": settings.DEVELOPER_PASSWORD}
        )
        
        assert response.status_code == 200
        token = response.json()["data"]["token"]
        
        # JWT token应该包含三个部分，用.分隔
        parts = token.split('.')
        assert len(parts) == 3, "JWT token格式不正确，应该包含三个部分"
        
        # 每个部分都应该是base64编码的字符串
        import base64
        for i, part in enumerate(parts):
            try:
                # 添加必要的padding
                padded = part + '=' * (4 - len(part) % 4)
                base64.urlsafe_b64decode(padded)
            except Exception:
                pytest.fail(f"JWT token第{i+1}部分不是有效的base64编码")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
