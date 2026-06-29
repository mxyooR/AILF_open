"""
1.1 登录测试
测试开发者认证API - POST /api/auth/developer
严格按照API文档规范进行测试
"""
import requests
import json
import time
import base64
from datetime import datetime


class DeveloperLoginTest:
    """开发者登录测试类"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.auth_url = f"{self.base_url}/api/auth/developer"
        self.developer_password = "AILF_DEV_2024_SECURE"
    
    def test_login_success(self):
        """测试开发者认证成功 - 正确密码"""
        print("🧪 测试开发者认证成功...")
        
        payload = {"password": self.developer_password}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(self.auth_url, json=payload, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200, f"期望code为200，实际: {data['code']}"
        assert data["message"] == "认证成功", f"期望message为'认证成功'，实际: {data['message']}"
        assert "data" in data, "响应中缺少data字段"
        
        # 验证token数据字段
        token_data = data["data"]
        required_fields = ["token", "expires_in", "token_type", "issued_at", "expires_at"]
        for field in required_fields:
            assert field in token_data, f"缺少必需字段: {field}"
        
        # 验证字段值
        assert token_data["token_type"] == "Bearer", f"期望token_type为'Bearer'，实际: {token_data['token_type']}"
        assert token_data["expires_in"] == 3600, f"期望expires_in为3600，实际: {token_data['expires_in']}"
        assert isinstance(token_data["token"], str), "token应该是字符串类型"
        assert len(token_data["token"]) > 0, "token不能为空"
        
        # 验证时间格式（ISO 8601）
        try:
            datetime.fromisoformat(token_data["issued_at"].replace('Z', '+00:00'))
            datetime.fromisoformat(token_data["expires_at"].replace('Z', '+00:00'))
        except ValueError as e:
            raise AssertionError(f"时间格式不符合ISO 8601标准: {e}")
        
        print("✅ 开发者认证成功测试通过")
        return token_data["token"]
    
    def test_login_wrong_password(self):
        """测试开发者认证失败 - 错误密码"""
        print("🧪 测试错误密码...")
        
        payload = {"password": "wrong_password"}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(self.auth_url, json=payload, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 401, f"期望状态码401，实际: {response.status_code}"
        
        # 验证错误响应结构
        data = response.json()
        assert data["code"] == 401, f"期望code为401，实际: {data['code']}"
        assert data["message"] == "密码错误", f"期望message为'密码错误'，实际: {data['message']}"
        assert "data" in data, "响应中缺少data字段"
        
        # 验证错误数据
        error_data = data["data"]
        assert error_data["error"] == "invalid_password", f"期望error为'invalid_password'，实际: {error_data['error']}"
        assert error_data["details"] == "提供的密码不正确", f"期望details为'提供的密码不正确'，实际: {error_data['details']}"
        
        print("✅ 错误密码测试通过")
    
    def test_login_empty_password(self):
        """测试开发者认证失败 - 空密码"""
        print("🧪 测试空密码...")
        
        payload = {"password": ""}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(self.auth_url, json=payload, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 400, f"期望状态码400，实际: {response.status_code}"
        
        # 验证错误响应结构
        data = response.json()
        assert data["code"] == 400, f"期望code为400，实际: {data['code']}"
        assert data["message"] == "请求参数错误", f"期望message为'请求参数错误'，实际: {data['message']}"
        assert "data" in data, "响应中缺少data字段"
        
        # 验证错误数据
        error_data = data["data"]
        assert error_data["error"] == "validation_error", f"期望error为'validation_error'，实际: {error_data['error']}"
        assert "details" in error_data, "错误数据中缺少details字段"
        assert "password" in error_data["details"], "details中缺少password字段"
        assert "密码不能为空" in error_data["details"]["password"], "密码错误信息不正确"
        
        print("✅ 空密码测试通过")
    
    def test_login_missing_password_field(self):
        """测试开发者认证失败 - 缺少password字段"""
        print("🧪 测试缺少password字段...")
        
        payload = {}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(self.auth_url, json=payload, headers=headers)
        
        # FastAPI会返回422 Unprocessable Entity
        assert response.status_code == 422, f"期望状态码422，实际: {response.status_code}"
        
        print("✅ 缺少password字段测试通过")
    
    def test_login_invalid_json(self):
        """测试开发者认证失败 - 无效JSON格式"""
        print("🧪 测试无效JSON格式...")
        
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(self.auth_url, data="invalid json", headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 422, f"期望状态码422，实际: {response.status_code}"
        
        print("✅ 无效JSON格式测试通过")
    
    def test_login_response_time(self):
        """测试响应时间（性能测试）"""
        print("🧪 测试响应时间...")
        
        payload = {"password": self.developer_password}
        headers = {"Content-Type": "application/json"}
        
        start_time = time.time()
        response = requests.post(self.auth_url, json=payload, headers=headers)
        end_time = time.time()
        
        # 验证响应成功
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证响应时间小于1秒
        response_time = end_time - start_time
        assert response_time < 1.0, f"响应时间过长: {response_time}秒"
        
        print(f"✅ 响应时间测试通过 ({response_time:.3f}秒)")
    
    def test_login_token_format(self):
        """测试JWT token格式"""
        print("🧪 测试JWT token格式...")
        
        payload = {"password": self.developer_password}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(self.auth_url, json=payload, headers=headers)
        
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        token = response.json()["data"]["token"]
        
        # JWT token应该包含三个部分，用.分隔
        parts = token.split('.')
        assert len(parts) == 3, f"JWT token格式不正确，应该包含三个部分，实际: {len(parts)}"
        
        # 每个部分都应该是base64编码的字符串
        for i, part in enumerate(parts):
            try:
                # 添加必要的padding
                padded = part + '=' * (4 - len(part) % 4)
                base64.urlsafe_b64decode(padded)
            except Exception as e:
                raise AssertionError(f"JWT token第{i+1}部分不是有效的base64编码: {e}")
        
        print("✅ JWT token格式测试通过")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行开发者登录测试...")
        print("=" * 50)
        
        try:
            # 运行所有测试
            token = self.test_login_success()
            self.test_login_wrong_password()
            self.test_login_empty_password()
            self.test_login_missing_password_field()
            self.test_login_invalid_json()
            self.test_login_response_time()
            self.test_login_token_format()
            
            print("=" * 50)
            print("🎉 所有登录测试通过！")
            return token
            
        except AssertionError as e:
            print(f"❌ 测试失败: {e}")
            return None
        except requests.exceptions.ConnectionError:
            print("❌ 连接失败: 请确保服务器在 http://localhost:5000 运行")
            return None
        except Exception as e:
            print(f"❌ 未知错误: {e}")
            return None


if __name__ == "__main__":
    test = DeveloperLoginTest()
    test.run_all_tests()
