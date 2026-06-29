"""
2.1 场景管理测试
测试场景管理模块的5个API端点
严格按照API文档规范进行测试
"""
import requests
import json
import time
from datetime import datetime


class ScenarioManagementTest:
    """场景管理测试类"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.auth_url = f"{self.base_url}/api/auth/developer"
        self.scenario_url = f"{self.base_url}/api/scenario"
        self.developer_password = "AILF_DEV_2024_SECURE"
        self.token = None
    
    def get_auth_token(self):
        """获取认证token"""
        if self.token:
            return self.token
        
        payload = {"password": self.developer_password}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(self.auth_url, json=payload, headers=headers)
        assert response.status_code == 200, f"获取token失败，状态码: {response.status_code}"
        
        self.token = response.json()["data"]["token"]
        return self.token
    
    def get_auth_headers(self):
        """获取认证请求头"""
        token = self.get_auth_token()
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    
    def test_get_active_scenario_no_scenario(self):
        """测试获取活跃场景 - 无场景情况"""
        print("🧪 测试获取活跃场景（无场景）...")
        
        headers = self.get_auth_headers()
        response = requests.get(f"{self.scenario_url}", headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 404, f"期望状态码404，实际: {response.status_code}"
        
        # 验证错误响应结构
        data = response.json()
        assert data["code"] == 404, f"期望code为404，实际: {data['code']}"
        assert data["message"] == "未找到活跃的场景配置", f"期望message为'未找到活跃的场景配置'，实际: {data['message']}"
        assert data["data"]["error"] == "no_active_scenario", f"期望error为'no_active_scenario'"
        
        print("✅ 获取活跃场景（无场景）测试通过")
    
    def test_create_scenario_success(self):
        """测试创建场景成功"""
        print("🧪 测试创建场景成功...")
        
        payload = {
            "name": f"测试电商系统_{int(time.time())}",
            "type": "ecommerce",
            "description": "用于测试的电商管理系统",
            "config": {
                "business_domain": "电子商务",
                "target_users": ["管理员", "销售人员", "客服"],
                "key_features": ["商品管理", "订单处理", "用户管理"],
                "example_instructions": ["查看今日订单", "新增商品：咖啡豆", "查询用户信息"],
                "custom_settings": {
                    "support_multi_currency": True,
                    "default_language": "zh-CN"
                }
            }
        }
        
        headers = self.get_auth_headers()
        response = requests.post(self.scenario_url, json=payload, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 201, f"期望状态码201，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 201, f"期望code为201，实际: {data['code']}"
        assert data["message"] == "场景配置创建成功", f"期望message为'场景配置创建成功'"
        assert "data" in data, "响应中缺少data字段"
        
        # 验证场景数据字段
        scenario = data["data"]["scenario"]
        required_fields = ["id", "name", "type", "description", "status", "created_at", "updated_at", "config"]
        for field in required_fields:
            assert field in scenario, f"缺少必需字段: {field}"
        
        # 验证字段值
        assert scenario["name"] == payload["name"], f"场景名称不匹配"
        assert scenario["type"] == payload["type"], f"场景类型不匹配"
        assert scenario["status"] == "active", f"期望status为'active'"
        assert scenario["config"]["business_domain"] == payload["config"]["business_domain"], f"业务领域不匹配"
        
        print("✅ 创建场景成功测试通过")
        return scenario["id"]
    
    def test_get_active_scenario_success(self):
        """测试获取活跃场景成功"""
        print("🧪 测试获取活跃场景成功...")
        
        headers = self.get_auth_headers()
        response = requests.get(f"{self.scenario_url}?include_details=true", headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200, f"期望code为200，实际: {data['code']}"
        assert data["message"] == "获取场景配置成功", f"期望message为'获取场景配置成功'"
        assert "data" in data, "响应中缺少data字段"
        assert "scenario" in data["data"], "data中缺少scenario字段"
        
        scenario = data["data"]["scenario"]
        assert scenario["status"] == "active", f"期望status为'active'"
        
        print("✅ 获取活跃场景成功测试通过")
        return scenario["id"]
    
    def test_get_scenario_by_id_success(self, scenario_id):
        """测试根据ID获取场景成功"""
        print("🧪 测试根据ID获取场景成功...")
        
        headers = self.get_auth_headers()
        response = requests.get(f"{self.scenario_url}/{scenario_id}", headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200, f"期望code为200，实际: {data['code']}"
        assert data["message"] == "获取场景配置成功", f"期望message为'获取场景配置成功'"
        assert data["data"]["scenario"]["id"] == scenario_id, f"场景ID不匹配"
        
        print("✅ 根据ID获取场景成功测试通过")
    
    def test_get_scenario_by_id_not_found(self):
        """测试根据ID获取场景 - 场景不存在"""
        print("🧪 测试根据ID获取场景（不存在）...")
        
        headers = self.get_auth_headers()
        response = requests.get(f"{self.scenario_url}/nonexistent_scenario", headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 404, f"期望状态码404，实际: {response.status_code}"
        
        # 验证错误响应结构
        data = response.json()
        assert data["code"] == 404, f"期望code为404，实际: {data['code']}"
        assert data["message"] == "场景配置不存在", f"期望message为'场景配置不存在'"
        assert data["data"]["error"] == "scenario_not_found", f"期望error为'scenario_not_found'"
        
        print("✅ 根据ID获取场景（不存在）测试通过")
    
    def test_validate_scenario_success(self, scenario_id):
        """测试验证场景成功"""
        print("🧪 测试验证场景成功...")
        
        payload = {
            "scenario_id": scenario_id,
            "check_dependencies": True,
            "check_completeness": True
        }
        
        headers = self.get_auth_headers()
        response = requests.post(f"{self.scenario_url}/validate", json=payload, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200, f"期望code为200，实际: {data['code']}"
        assert data["message"] == "场景配置验证通过", f"期望message为'场景配置验证通过'"
        
        # 验证验证数据字段
        validate_data = data["data"]
        required_fields = ["valid", "scenario_id", "checks", "warnings", "suggestions"]
        for field in required_fields:
            assert field in validate_data, f"缺少必需字段: {field}"
        
        assert validate_data["valid"] is True, f"期望valid为True"
        assert validate_data["scenario_id"] == scenario_id, f"场景ID不匹配"
        
        # 验证检查结果
        checks = validate_data["checks"]
        check_fields = ["basic_info", "entities", "workflows", "forms", "permissions"]
        for field in check_fields:
            assert field in checks, f"checks中缺少字段: {field}"
        
        print("✅ 验证场景成功测试通过")
    
    def test_validate_scenario_not_found(self):
        """测试验证场景 - 场景不存在"""
        print("🧪 测试验证场景（场景不存在）...")
        
        payload = {
            "scenario_id": "nonexistent_scenario",
            "check_dependencies": True,
            "check_completeness": True
        }
        
        headers = self.get_auth_headers()
        response = requests.post(f"{self.scenario_url}/validate", json=payload, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 404, f"期望状态码404，实际: {response.status_code}"
        
        # 验证错误响应结构
        data = response.json()
        assert data["code"] == 404, f"期望code为404，实际: {data['code']}"
        assert data["message"] == "场景配置不存在", f"期望message为'场景配置不存在'"
        
        print("✅ 验证场景（场景不存在）测试通过")
    
    def test_create_from_template_success(self):
        """测试从模板创建场景成功"""
        print("🧪 测试从模板创建场景成功...")
        
        payload = {
            "template_key": "ecommerce_basic",
            "name": f"我的电商系统_{int(time.time())}",
            "description": "基于基础电商模板的定制系统",
            "customizations": {
                "support_multi_currency": True,
                "default_language": "zh-CN"
            }
        }
        
        headers = self.get_auth_headers()
        response = requests.post(f"{self.scenario_url}/from-template", json=payload, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 201, f"期望状态码201，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 201, f"期望code为201，实际: {data['code']}"
        assert data["message"] == "基于模板创建场景成功", f"期望message为'基于模板创建场景成功'"
        
        # 验证场景数据
        scenario = data["data"]["scenario"]
        assert scenario["name"] == payload["name"], f"场景名称不匹配"
        assert scenario["type"] == "ecommerce", f"期望type为'ecommerce'"
        assert scenario["template_key"] == payload["template_key"], f"模板key不匹配"
        assert scenario["status"] == "active", f"期望status为'active'"
        
        # 验证自定义配置
        custom_settings = scenario["config"]["custom_settings"]
        assert custom_settings["support_multi_currency"] is True, f"自定义配置未生效"
        
        print("✅ 从模板创建场景成功测试通过")
        return scenario["id"]
    
    def test_create_from_template_not_found(self):
        """测试从模板创建场景 - 模板不存在"""
        print("🧪 测试从模板创建场景（模板不存在）...")
        
        payload = {
            "template_key": "nonexistent_template",
            "name": "测试场景",
            "description": "测试描述"
        }
        
        headers = self.get_auth_headers()
        response = requests.post(f"{self.scenario_url}/from-template", json=payload, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 404, f"期望状态码404，实际: {response.status_code}"
        
        # 验证错误响应结构
        data = response.json()
        assert data["code"] == 404, f"期望code为404，实际: {data['code']}"
        assert data["message"] == "模板不存在", f"期望message为'模板不存在'"
        assert data["data"]["error"] == "template_not_found", f"期望error为'template_not_found'"
        
        print("✅ 从模板创建场景（模板不存在）测试通过")
    
    def test_create_scenario_duplicate_name(self, existing_name):
        """测试创建场景 - 名称重复"""
        print("🧪 测试创建场景（名称重复）...")

        payload = {
            "name": existing_name,  # 使用已存在的名称
            "type": "restaurant",
            "description": "重复名称测试",
            "config": {
                "business_domain": "餐饮服务",
                "target_users": ["店长"],
                "key_features": ["菜品管理"],
                "example_instructions": ["查看当前订单", "新增菜单项：拿铁"]
            }
        }
        
        headers = self.get_auth_headers()
        response = requests.post(self.scenario_url, json=payload, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 409, f"期望状态码409，实际: {response.status_code}"
        
        # 验证错误响应结构
        data = response.json()
        assert data["code"] == 409, f"期望code为409，实际: {data['code']}"
        assert data["message"] == "场景名称重复", f"期望message为'场景名称重复'"
        assert data["data"]["error"] == "duplicate_scenario", f"期望error为'duplicate_scenario'"
        
        print("✅ 创建场景（名称重复）测试通过")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行场景管理测试...")
        print("=" * 50)

        try:
            # 1. 测试获取活跃场景（无场景）
            self.test_get_active_scenario_no_scenario()

            # 2. 测试创建场景成功
            scenario_id = self.test_create_scenario_success()

            # 获取创建的场景名称用于重复测试
            headers = self.get_auth_headers()
            resp = requests.get(f"{self.scenario_url}/{scenario_id}", headers=headers)
            existing_name = resp.json()["data"]["scenario"]["name"]

            # 3. 测试获取活跃场景成功
            active_scenario_id = self.test_get_active_scenario_success()

            # 4. 测试根据ID获取场景成功
            self.test_get_scenario_by_id_success(scenario_id)

            # 5. 测试根据ID获取场景（不存在）
            self.test_get_scenario_by_id_not_found()

            # 6. 测试验证场景成功
            self.test_validate_scenario_success(scenario_id)

            # 7. 测试验证场景（场景不存在）
            self.test_validate_scenario_not_found()

            # 8. 测试从模板创建场景成功
            template_scenario_id = self.test_create_from_template_success()

            # 9. 测试从模板创建场景（模板不存在）
            self.test_create_from_template_not_found()

            # 10. 测试创建场景（名称重复）
            self.test_create_scenario_duplicate_name(existing_name)
            
            print("=" * 50)
            print("🎉 所有场景管理测试通过！")
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
    test = ScenarioManagementTest()
    test.run_all_tests()
