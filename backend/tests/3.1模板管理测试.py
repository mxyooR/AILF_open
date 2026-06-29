"""
3.1 模板管理测试
测试模板管理模块的2个API端点
严格按照API文档规范进行测试
"""
import requests
import json
import time
from datetime import datetime


class TemplateManagementTest:
    """模板管理测试类"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.auth_url = f"{self.base_url}/api/auth/developer"
        self.template_url = f"{self.base_url}/api/templates"
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
    
    def test_get_templates_list_basic(self):
        """测试获取模板列表 - 基础功能"""
        print("🧪 测试获取模板列表（基础功能）...")
        
        headers = self.get_auth_headers()
        response = requests.get(self.template_url, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200, f"期望code为200，实际: {data['code']}"
        assert data["message"] == "获取模板列表成功", f"期望message为'获取模板列表成功'"
        assert "data" in data, "响应中缺少data字段"
        
        # 验证模板列表数据字段
        template_data = data["data"]
        required_fields = ["templates", "total", "categories"]
        for field in required_fields:
            assert field in template_data, f"缺少必需字段: {field}"
        
        # 验证模板列表不为空
        assert len(template_data["templates"]) > 0, "模板列表不能为空"
        assert template_data["total"] > 0, "模板总数应该大于0"
        assert len(template_data["categories"]) > 0, "分类列表不能为空"
        
        # 验证模板项字段
        template = template_data["templates"][0]
        template_fields = ["key", "name", "description", "category", "difficulty", 
                          "estimated_setup_time", "features", "tags", "created_at", "updated_at"]
        for field in template_fields:
            assert field in template, f"模板项缺少字段: {field}"
        
        # 验证分类统计字段
        category = template_data["categories"][0]
        category_fields = ["key", "name", "count"]
        for field in category_fields:
            assert field in category, f"分类统计缺少字段: {field}"
        
        print("✅ 获取模板列表（基础功能）测试通过")
        return template_data["templates"][0]["key"]  # 返回第一个模板的key用于后续测试
    
    def test_get_templates_list_with_preview(self):
        """测试获取模板列表 - 包含预览信息"""
        print("🧪 测试获取模板列表（包含预览信息）...")
        
        headers = self.get_auth_headers()
        response = requests.get(f"{self.template_url}?include_preview=true", headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        template_data = data["data"]
        
        # 验证模板包含预览信息
        template = template_data["templates"][0]
        assert "preview" in template, "模板项应该包含preview字段"
        
        # 验证预览信息字段
        preview = template["preview"]
        preview_fields = ["entities", "workflows", "forms", "apis"]
        for field in preview_fields:
            assert field in preview, f"预览信息缺少字段: {field}"
            assert isinstance(preview[field], int), f"预览信息字段{field}应该是整数"
        
        print("✅ 获取模板列表（包含预览信息）测试通过")
    
    def test_get_templates_list_with_category_filter(self):
        """测试获取模板列表 - 分类筛选"""
        print("🧪 测试获取模板列表（分类筛选）...")
        
        headers = self.get_auth_headers()
        
        # 测试有效分类筛选
        response = requests.get(f"{self.template_url}?category=business", headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证筛选结果
        data = response.json()
        template_data = data["data"]
        
        # 验证所有返回的模板都属于指定分类
        for template in template_data["templates"]:
            assert template["category"] == "business", f"模板分类不匹配，期望business，实际: {template['category']}"
        
        print("✅ 获取模板列表（分类筛选）测试通过")
    
    def test_get_templates_list_invalid_category(self):
        """测试获取模板列表 - 无效分类"""
        print("🧪 测试获取模板列表（无效分类）...")
        
        headers = self.get_auth_headers()
        response = requests.get(f"{self.template_url}?category=invalid_category", headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 400, f"期望状态码400，实际: {response.status_code}"
        
        # 验证错误响应结构
        data = response.json()
        assert data["code"] == 400, f"期望code为400，实际: {data['code']}"
        assert data["message"] == "无效的分类参数", f"期望message为'无效的分类参数'"
        assert data["data"]["error"] == "invalid_category", f"期望error为'invalid_category'"
        
        print("✅ 获取模板列表（无效分类）测试通过")
    
    def test_get_template_detail_success(self, template_key):
        """测试获取模板详情成功"""
        print("🧪 测试获取模板详情成功...")
        
        headers = self.get_auth_headers()
        response = requests.get(f"{self.template_url}/{template_key}", headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200, f"期望code为200，实际: {data['code']}"
        assert data["message"] == "获取模板详情成功", f"期望message为'获取模板详情成功'"
        assert "data" in data, "响应中缺少data字段"
        assert "template" in data["data"], "data中缺少template字段"
        
        # 验证模板详情字段
        template = data["data"]["template"]
        detail_fields = ["key", "name", "description", "category", "difficulty", 
                        "estimated_setup_time", "version", "author", "license",
                        "features", "tags", "created_at", "updated_at", 
                        "config", "setup_guide"]
        for field in detail_fields:
            assert field in template, f"模板详情缺少字段: {field}"
        
        # 验证配置字段
        config = template["config"]
        config_fields = ["scenario", "entities", "workflows", "forms", "apis", "roles"]
        for field in config_fields:
            assert field in config, f"配置缺少字段: {field}"
        
        # 验证设置指南字段
        setup_guide = template["setup_guide"]
        guide_fields = ["steps", "prerequisites", "tips"]
        for field in guide_fields:
            assert field in setup_guide, f"设置指南缺少字段: {field}"
        
        # 验证模板key匹配
        assert template["key"] == template_key, f"模板key不匹配，期望: {template_key}，实际: {template['key']}"
        
        print("✅ 获取模板详情成功测试通过")
    
    def test_get_template_detail_not_found(self):
        """测试获取模板详情 - 模板不存在"""
        print("🧪 测试获取模板详情（模板不存在）...")
        
        headers = self.get_auth_headers()
        response = requests.get(f"{self.template_url}/nonexistent_template", headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 404, f"期望状态码404，实际: {response.status_code}"
        
        # 验证错误响应结构
        data = response.json()
        assert data["code"] == 404, f"期望code为404，实际: {data['code']}"
        assert data["message"] == "模板不存在", f"期望message为'模板不存在'"
        assert data["data"]["error"] == "template_not_found", f"期望error为'template_not_found'"
        
        print("✅ 获取模板详情（模板不存在）测试通过")
    
    def test_template_data_consistency(self):
        """测试模板数据一致性"""
        print("🧪 测试模板数据一致性...")
        
        headers = self.get_auth_headers()
        
        # 获取模板列表
        list_response = requests.get(self.template_url, headers=headers)
        list_data = list_response.json()["data"]
        
        # 获取第一个模板的详情
        template_key = list_data["templates"][0]["key"]
        detail_response = requests.get(f"{self.template_url}/{template_key}", headers=headers)
        detail_data = detail_response.json()["data"]["template"]
        
        # 验证基础信息一致性
        list_template = list_data["templates"][0]
        consistency_fields = ["key", "name", "description", "category", "difficulty", 
                             "estimated_setup_time", "features", "tags", "created_at", "updated_at"]
        
        for field in consistency_fields:
            assert list_template[field] == detail_data[field], f"字段{field}在列表和详情中不一致"
        
        print("✅ 模板数据一致性测试通过")
    
    def test_response_time_performance(self):
        """测试响应时间性能"""
        print("🧪 测试响应时间性能...")
        
        headers = self.get_auth_headers()
        
        # 测试模板列表响应时间
        start_time = time.time()
        response = requests.get(self.template_url, headers=headers)
        end_time = time.time()
        
        assert response.status_code == 200, "模板列表请求应该成功"
        list_response_time = end_time - start_time
        assert list_response_time < 5.0, f"模板列表响应时间过长: {list_response_time}秒"
        
        # 测试模板详情响应时间
        template_key = response.json()["data"]["templates"][0]["key"]
        start_time = time.time()
        response = requests.get(f"{self.template_url}/{template_key}", headers=headers)
        end_time = time.time()
        
        assert response.status_code == 200, "模板详情请求应该成功"
        detail_response_time = end_time - start_time
        assert detail_response_time < 5.0, f"模板详情响应时间过长: {detail_response_time}秒"
        
        print(f"✅ 响应时间性能测试通过 (列表: {list_response_time:.3f}秒, 详情: {detail_response_time:.3f}秒)")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行模板管理测试...")
        print("=" * 50)
        
        try:
            # 1. 测试获取模板列表（基础功能）
            template_key = self.test_get_templates_list_basic()
            
            # 2. 测试获取模板列表（包含预览信息）
            self.test_get_templates_list_with_preview()
            
            # 3. 测试获取模板列表（分类筛选）
            self.test_get_templates_list_with_category_filter()
            
            # 4. 测试获取模板列表（无效分类）
            self.test_get_templates_list_invalid_category()
            
            # 5. 测试获取模板详情成功
            self.test_get_template_detail_success(template_key)
            
            # 6. 测试获取模板详情（模板不存在）
            self.test_get_template_detail_not_found()
            
            # 7. 测试模板数据一致性
            self.test_template_data_consistency()
            
            # 8. 测试响应时间性能
            self.test_response_time_performance()
            
            print("=" * 50)
            print("🎉 所有模板管理测试通过！")
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
    test = TemplateManagementTest()
    test.run_all_tests()
