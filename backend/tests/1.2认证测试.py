"""
1.2 认证测试
测试验证开发者令牌API - POST /api/auth/developer/verify-token
严格按照API文档规范进行测试
"""
import requests
import json
import time
from datetime import datetime


class TokenVerificationTest:
    """令牌验证测试类"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.auth_url = f"{self.base_url}/api/auth/developer"
        self.verify_url = f"{self.base_url}/api/auth/developer/verify-token"
        self.developer_password = "AILF_DEV_2024_SECURE"
    
    def get_valid_token(self):
        """获取有效的JWT token"""
        payload = {"password": self.developer_password}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(self.auth_url, json=payload, headers=headers)
        assert response.status_code == 200, f"获取token失败，状态码: {response.status_code}"
        return response.json()["data"]["token"]
    
    def test_verify_token_success(self):
        """测试令牌验证成功 - 有效token"""
        print("🧪 测试令牌验证成功...")
        
        # 获取有效token
        token = self.get_valid_token()
        
        # 验证token
        payload = {"token": token}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(self.verify_url, json=payload, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200, f"期望code为200，实际: {data['code']}"
        assert data["message"] == "令牌有效", f"期望message为'令牌有效'，实际: {data['message']}"
        assert "data" in data, "响应中缺少data字段"
        
        # 验证token验证数据字段
        verify_data = data["data"]
        required_fields = ["valid", "user_type", "issued_at", "expires_at", "remaining_time"]
        for field in required_fields:
            assert field in verify_data, f"缺少必需字段: {field}"
        
        # 验证字段值
        assert verify_data["valid"] is True, f"期望valid为True，实际: {verify_data['valid']}"
        assert verify_data["user_type"] == "developer", f"期望user_type为'developer'，实际: {verify_data['user_type']}"
        assert isinstance(verify_data["remaining_time"], int), "remaining_time应该是整数类型"
        assert verify_data["remaining_time"] > 0, f"remaining_time应该大于0，实际: {verify_data['remaining_time']}"
        
        # 验证时间格式（ISO 8601）
        try:
            datetime.fromisoformat(verify_data["issued_at"].replace('Z', '+00:00'))
            datetime.fromisoformat(verify_data["expires_at"].replace('Z', '+00:00'))
        except ValueError as e:
            raise AssertionError(f"时间格式不符合ISO 8601标准: {e}")
        
        print("✅ 令牌验证成功测试通过")
        return token
    
    def test_verify_token_without_authorization_header(self):
        """测试令牌验证 - 不带Authorization头"""
        print("🧪 测试不带Authorization头...")
        
        token = self.get_valid_token()
        
        payload = {"token": token}
        headers = {"Content-Type": "application/json"}
        # 不包含Authorization头
        
        response = requests.post(self.verify_url, json=payload, headers=headers)
        
        # 验证仍然成功（根据API文档，Authorization头是可选的）
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        print("✅ 不带Authorization头测试通过")
    
    def test_verify_token_invalid_format(self):
        """测试令牌验证失败 - 无效token格式"""
        print("🧪 测试无效token格式...")
        
        payload = {"token": "invalid_token_format"}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(self.verify_url, json=payload, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 401, f"期望状态码401，实际: {response.status_code}"
        
        # 验证错误响应结构
        data = response.json()
        assert data["code"] == 401, f"期望code为401，实际: {data['code']}"
        assert data["message"] == "令牌无效", f"期望message为'令牌无效'，实际: {data['message']}"
        assert "data" in data, "响应中缺少data字段"
        
        # 验证错误数据
        error_data = data["data"]
        assert error_data["valid"] is False, f"期望valid为False，实际: {error_data['valid']}"
        assert error_data["error"] == "token_invalid", f"期望error为'token_invalid'，实际: {error_data['error']}"
        assert "details" in error_data, "错误数据中缺少details字段"
        
        print("✅ 无效token格式测试通过")
    
    def test_verify_token_empty_token(self):
        """测试令牌验证失败 - 空token"""
        print("🧪 测试空token...")
        
        payload = {"token": ""}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(self.verify_url, json=payload, headers=headers)
        
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
        assert "token" in error_data["details"], "details中缺少token字段"
        assert "令牌格式不正确" in error_data["details"]["token"], "token错误信息不正确"
        
        print("✅ 空token测试通过")
    
    def test_verify_token_missing_token_field(self):
        """测试令牌验证失败 - 缺少token字段"""
        print("🧪 测试缺少token字段...")
        
        payload = {}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(self.verify_url, json=payload, headers=headers)
        
        # FastAPI会返回422 Unprocessable Entity
        assert response.status_code == 422, f"期望状态码422，实际: {response.status_code}"
        
        print("✅ 缺少token字段测试通过")
    
    def test_verify_token_malformed_jwt(self):
        """测试令牌验证失败 - 格式错误的JWT"""
        print("🧪 测试格式错误的JWT...")
        
        malformed_tokens = [
            "not.a.jwt",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # 只有header
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ",  # 缺少signature
            "invalid.jwt.format.with.too.many.parts.here"
        ]
        
        for i, malformed_token in enumerate(malformed_tokens):
            payload = {"token": malformed_token}
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(self.verify_url, json=payload, headers=headers)
            
            assert response.status_code == 401, f"测试{i+1}: 期望状态码401，实际: {response.status_code}"
            data = response.json()
            assert data["data"]["valid"] is False, f"测试{i+1}: 期望valid为False"
            assert data["data"]["error"] == "token_invalid", f"测试{i+1}: 期望error为'token_invalid'"
        
        print("✅ 格式错误的JWT测试通过")
    
    def test_verify_token_remaining_time_accuracy(self):
        """测试剩余时间计算准确性"""
        print("🧪 测试剩余时间计算准确性...")
        
        token = self.get_valid_token()
        
        # 立即验证token
        payload = {"token": token}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(self.verify_url, json=payload, headers=headers)
        
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        data = response.json()
        remaining_time = data["data"]["remaining_time"]
        
        # 剩余时间应该接近3600秒（1小时），允许几秒的误差
        assert 3590 <= remaining_time <= 3600, f"剩余时间不准确: {remaining_time}"
        
        print(f"✅ 剩余时间计算准确性测试通过 (剩余: {remaining_time}秒)")
    
    def test_verify_token_response_time(self):
        """测试令牌验证响应时间（性能测试）"""
        print("🧪 测试令牌验证响应时间...")
        
        token = self.get_valid_token()
        
        payload = {"token": token}
        headers = {"Content-Type": "application/json"}
        
        start_time = time.time()
        response = requests.post(self.verify_url, json=payload, headers=headers)
        end_time = time.time()
        
        # 验证响应成功
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证响应时间小于0.5秒
        response_time = end_time - start_time
        assert response_time < 0.5, f"令牌验证响应时间过长: {response_time}秒"
        
        print(f"✅ 令牌验证响应时间测试通过 ({response_time:.3f}秒)")
    
    def test_verify_token_consistency(self):
        """测试令牌验证一致性 - 同一token多次验证应返回相同结果"""
        print("🧪 测试令牌验证一致性...")
        
        token = self.get_valid_token()
        
        # 连续验证同一token多次
        responses = []
        for i in range(3):
            payload = {"token": token}
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(self.verify_url, json=payload, headers=headers)
            responses.append(response.json())
            time.sleep(0.1)  # 短暂延迟
        
        # 验证所有响应都成功
        for i, response_data in enumerate(responses):
            assert response_data["code"] == 200, f"第{i+1}次验证失败"
            assert response_data["data"]["valid"] is True, f"第{i+1}次验证valid不为True"
            assert response_data["data"]["user_type"] == "developer", f"第{i+1}次验证user_type不正确"
        
        # 验证issued_at和expires_at保持一致
        first_response = responses[0]["data"]
        for i, response_data in enumerate(responses[1:], 2):
            assert response_data["data"]["issued_at"] == first_response["issued_at"], f"第{i}次验证issued_at不一致"
            assert response_data["data"]["expires_at"] == first_response["expires_at"], f"第{i}次验证expires_at不一致"
        
        print("✅ 令牌验证一致性测试通过")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行令牌验证测试...")
        print("=" * 50)
        
        try:
            # 运行所有测试
            self.test_verify_token_success()
            self.test_verify_token_without_authorization_header()
            self.test_verify_token_invalid_format()
            self.test_verify_token_empty_token()
            self.test_verify_token_missing_token_field()
            self.test_verify_token_malformed_jwt()
            self.test_verify_token_remaining_time_accuracy()
            self.test_verify_token_response_time()
            self.test_verify_token_consistency()
            
            print("=" * 50)
            print("🎉 所有令牌验证测试通过！")
            return True
            
        except AssertionError as e:
            print(f"❌ 测试失败: {e}")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ 连接失败: 请确保服务器在 http://localhost:5000 运行")
            return False
        except Exception as e:
            print(f"❌ 未知错误: {e}")
            return False


if __name__ == "__main__":
    test = TokenVerificationTest()
    test.run_all_tests()
