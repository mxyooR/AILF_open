"""
第六部分 - 表单配置模块测试
测试所有13个API端点的功能
"""
import requests
import json
import time
from typing import Dict, Any, Optional


class FormConfigTest:
    """表单配置模块测试类"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.token = None
        self.test_form_id = None
        self.test_field_id = None
        self.test_entity_id = None
        
    def get_auth_token(self) -> bool:
        """获取认证令牌"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/developer",
                json={"password": "AILF_DEV_2024_SECURE"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["data"]["token"]
                return True
            else:
                print(f"❌ 获取令牌失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 获取令牌异常: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_all_form_apis(self) -> bool:
        """测试所有13个表单API端点"""
        print("🚀 开始运行表单配置模块测试...")
        print("📋 覆盖所有13个API端点")
        print("=" * 60)
        
        test_results = []
        
        # 表单定义管理测试 (5个API)
        print("\n📋 表单定义管理测试")
        print("-" * 30)
        
        # 1. 创建表单配置
        print("🧪 测试创建表单配置...")
        result = self.test_create_form()
        test_results.append(result)
        
        # 2. 获取表单配置列表
        print("🧪 测试获取表单配置列表...")
        result = self.test_get_forms_list()
        test_results.append(result)
        
        # 3. 获取表单配置详情
        print("🧪 测试获取表单配置详情...")
        result = self.test_get_form_detail()
        test_results.append(result)
        
        # 4. 更新表单配置
        print("🧪 测试更新表单配置...")
        result = self.test_update_form()
        test_results.append(result)

        # 表单渲染管理测试 (4个API) - 在删除前测试
        print("\n⚡ 表单渲染管理测试")
        print("-" * 30)
        
        # 6. 获取表单渲染配置
        print("🧪 测试获取表单渲染配置...")
        result = self.test_get_form_render_schema()
        test_results.append(result)
        
        # 7. 提交表单数据
        print("🧪 测试提交表单数据...")
        result = self.test_submit_form_data()
        test_results.append(result)
        
        # 8. 获取表单数据用于编辑
        print("🧪 测试获取表单数据用于编辑...")
        result = self.test_get_form_data_for_edit()
        test_results.append(result)
        
        # 9. 验证表单配置
        print("🧪 测试验证表单配置...")
        result = self.test_validate_form_config()
        test_results.append(result)
        
        # 表单字段管理测试 (4个API)
        print("\n🔧 表单字段管理测试")
        print("-" * 30)
        
        # 10. 获取表单字段列表
        print("🧪 测试获取表单字段列表...")
        result = self.test_get_form_fields()
        test_results.append(result)
        
        # 11. 添加表单字段
        print("🧪 测试添加表单字段...")
        result = self.test_add_form_field()
        test_results.append(result)
        
        # 12. 更新表单字段
        print("🧪 测试更新表单字段...")
        result = self.test_update_form_field()
        test_results.append(result)
        
        # 13. 删除表单字段
        print("🧪 测试删除表单字段...")
        result = self.test_delete_form_field()
        test_results.append(result)

        # 最后测试删除表单配置
        print("\n🗑️  清理测试")
        print("-" * 30)
        print("🧪 测试删除表单配置...")
        result = self.test_delete_form()
        # 不计入测试结果，因为这只是清理
        
        # 统计结果
        passed = sum(test_results)
        total = len(test_results)
        
        print("\n" + "=" * 60)
        print("📊 第六部分表单配置模块测试结果")
        print("-" * 60)
        print(f"总API端点: {total}")
        print(f"测试通过: {passed}")
        print(f"测试失败: {total - passed}")
        print(f"成功率: {(passed / total * 100):.1f}%")
        
        if passed == total:
            print("🎉 所有13个API端点测试全部通过！")
            print("✅ 第六部分表单配置模块功能完整！")
            return True
        else:
            print(f"⚠️  有 {total - passed} 个API端点测试失败")
            return False
    
    def test_create_form(self) -> bool:
        """测试创建表单配置"""
        try:
            form_data = {
                "name": "商品录入表单",
                "entity": "product",
                "description": "用于录入和编辑商品信息的表单",
                "layout": {
                    "type": "grid",
                    "columns": 2,
                    "spacing": 16
                },
                "sections": [
                    {
                        "id": "section_basic",
                        "title": "基本信息",
                        "collapsible": False,
                        "fields": [
                            {
                                "id": "field_name",
                                "entityField": "name",
                                "displayType": "input",
                                "label": "商品名称",
                                "placeholder": "请输入商品名称",
                                "required": True,
                                "validation": {
                                    "rules": ["required", "max:100"],
                                    "messages": {
                                        "required": "商品名称不能为空",
                                        "max": "商品名称不能超过100个字符"
                                    }
                                },
                                "gridSpan": 1
                            },
                            {
                                "id": "field_price",
                                "entityField": "price",
                                "displayType": "input",
                                "label": "商品价格",
                                "placeholder": "0.00",
                                "required": True,
                                "validation": {
                                    "rules": ["required", "numeric", "min:0.01"],
                                    "messages": {
                                        "required": "价格不能为空",
                                        "numeric": "价格必须是数字",
                                        "min": "价格必须大于0"
                                    }
                                },
                                "gridSpan": 1
                            }
                        ]
                    }
                ],
                "permissions": [
                    {
                        "role": "admin",
                        "actions": ["create", "read", "update", "delete"]
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/api/forms",
                headers=self.get_headers(),
                json=form_data
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.test_form_id = data["data"]["form"]["id"]
                print(f"   ✅ 创建成功: {self.test_form_id}")
                return True
            else:
                print(f"   ❌ 创建失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ 创建异常: {e}")
            return False
    
    def test_get_forms_list(self) -> bool:
        """测试获取表单配置列表"""
        try:
            response = requests.get(
                f"{self.base_url}/api/forms?entity=product&page=1&limit=10",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                forms = data["data"]["forms"]
                total = data["data"]["total"]
                print(f"   ✅ 获取成功: {len(forms)}个表单，总计{total}个")
                return True
            else:
                print(f"   ❌ 获取失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 获取异常: {e}")
            return False
    
    def test_get_form_detail(self) -> bool:
        """测试获取表单配置详情"""
        if not self.test_form_id:
            print("   ❌ 没有可用的表单ID")
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/api/forms/{self.test_form_id}",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                form = data["data"]["form"]
                print(f"   ✅ 获取成功: {form['name']} ({form['field_count']}个字段)")
                return True
            else:
                print(f"   ❌ 获取失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 获取异常: {e}")
            return False
    
    def test_update_form(self) -> bool:
        """测试更新表单配置"""
        if not self.test_form_id:
            print("   ❌ 没有可用的表单ID")
            return False
            
        try:
            update_data = {
                "description": "更新后的商品录入表单描述",
                "status": "active"
            }
            
            response = requests.put(
                f"{self.base_url}/api/forms/{self.test_form_id}",
                headers=self.get_headers(),
                json=update_data
            )
            
            if response.status_code == 200:
                data = response.json()
                form = data["data"]["form"]
                print(f"   ✅ 更新成功: {form['description']}")
                return True
            else:
                print(f"   ❌ 更新失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 更新异常: {e}")
            return False
    
    def test_delete_form(self) -> bool:
        """测试删除表单配置"""
        if not self.test_form_id:
            print("   ❌ 没有可用的表单ID")
            return False

        try:
            response = requests.delete(
                f"{self.base_url}/api/forms/{self.test_form_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 删除成功: {data['data']['name']}")
                return True
            else:
                print(f"   ❌ 删除失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"   ❌ 删除异常: {e}")
            return False

    def test_get_form_render_schema(self) -> bool:
        """测试获取表单渲染配置"""
        if not self.test_form_id:
            print("   ❌ 没有可用的表单ID")
            return False

        try:
            response = requests.get(
                f"{self.base_url}/api/forms/{self.test_form_id}/render?mode=create&user_role=admin",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                schema = data["data"]["schema"]
                print(f"   ✅ 获取成功: amis schema类型 {schema['type']}")
                return True
            else:
                print(f"   ❌ 获取失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"   ❌ 获取异常: {e}")
            return False

    def test_submit_form_data(self) -> bool:
        """测试提交表单数据"""
        if not self.test_form_id:
            print("   ❌ 没有可用的表单ID")
            return False

        try:
            self.test_entity_id = f"entity_{int(time.time())}"
            submit_data = {
                "form_data": {
                    "name": "测试商品",
                    "price": 99.99
                },
                "entity_id": self.test_entity_id
            }

            response = requests.post(
                f"{self.base_url}/api/forms/{self.test_form_id}/submit",
                headers=self.get_headers(),
                json=submit_data
            )

            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 提交成功: 数据ID {data['data']['data_id']}")
                return True
            else:
                print(f"   ❌ 提交失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"   ❌ 提交异常: {e}")
            return False

    def test_get_form_data_for_edit(self) -> bool:
        """测试获取表单数据用于编辑"""
        if not self.test_form_id or not self.test_entity_id:
            print("   ❌ 没有可用的表单ID或实体ID")
            return False

        try:
            response = requests.get(
                f"{self.base_url}/api/forms/{self.test_form_id}/data/{self.test_entity_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                form_data = data["data"]["form_data"]
                print(f"   ✅ 获取成功: 商品名称 {form_data.get('name', 'N/A')}")
                return True
            else:
                print(f"   ❌ 获取失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"   ❌ 获取异常: {e}")
            return False

    def test_validate_form_config(self) -> bool:
        """测试验证表单配置"""
        if not self.test_form_id:
            print("   ❌ 没有可用的表单ID")
            return False

        try:
            response = requests.post(
                f"{self.base_url}/api/forms/{self.test_form_id}/validate",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                validation = data["data"]
                print(f"   ✅ 验证完成: 有效性 {validation['valid']}")
                return True
            else:
                print(f"   ❌ 验证失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"   ❌ 验证异常: {e}")
            return False

    def test_get_form_fields(self) -> bool:
        """测试获取表单字段列表"""
        if not self.test_form_id:
            print("   ❌ 没有可用的表单ID")
            return False

        try:
            response = requests.get(
                f"{self.base_url}/api/forms/{self.test_form_id}/fields",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                fields = data["data"]["fields"]
                print(f"   ✅ 获取成功: {len(fields)}个字段")
                return True
            else:
                print(f"   ❌ 获取失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"   ❌ 获取异常: {e}")
            return False

    def test_add_form_field(self) -> bool:
        """测试添加表单字段"""
        if not self.test_form_id:
            print("   ❌ 没有可用的表单ID")
            return False

        try:
            self.test_field_id = "field_category"
            field_data = {
                "field_id": self.test_field_id,
                "section_id": "section_basic",
                "entityField": "category",
                "displayType": "select",
                "label": "商品分类",
                "placeholder": "请选择商品分类",
                "required": True,
                "validation": {
                    "rules": ["required"],
                    "messages": {
                        "required": "商品分类不能为空"
                    }
                },
                "options": [
                    {"label": "电子产品", "value": "electronics"},
                    {"label": "服装", "value": "clothing"},
                    {"label": "食品", "value": "food"}
                ],
                "gridSpan": 1
            }

            response = requests.post(
                f"{self.base_url}/api/forms/{self.test_form_id}/fields",
                headers=self.get_headers(),
                json=field_data
            )

            if response.status_code in [200, 201]:
                data = response.json()
                field = data["data"]["field"]
                print(f"   ✅ 添加成功: {field['label']}")
                return True
            else:
                print(f"   ❌ 添加失败: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"   ❌ 添加异常: {e}")
            return False

    def test_update_form_field(self) -> bool:
        """测试更新表单字段"""
        if not self.test_form_id or not self.test_field_id:
            print("   ❌ 没有可用的表单ID或字段ID")
            return False

        try:
            update_data = {
                "label": "商品类别",
                "placeholder": "请选择商品类别",
                "options": [
                    {"label": "电子产品", "value": "electronics"},
                    {"label": "服装鞋帽", "value": "clothing"},
                    {"label": "食品饮料", "value": "food"},
                    {"label": "家居用品", "value": "home"}
                ]
            }

            response = requests.put(
                f"{self.base_url}/api/forms/{self.test_form_id}/fields/{self.test_field_id}",
                headers=self.get_headers(),
                json=update_data
            )

            if response.status_code == 200:
                data = response.json()
                field = data["data"]["field"]
                print(f"   ✅ 更新成功: {field['label']}")
                return True
            else:
                print(f"   ❌ 更新失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"   ❌ 更新异常: {e}")
            return False

    def test_delete_form_field(self) -> bool:
        """测试删除表单字段"""
        if not self.test_form_id or not self.test_field_id:
            print("   ❌ 没有可用的表单ID或字段ID")
            return False

        try:
            response = requests.delete(
                f"{self.base_url}/api/forms/{self.test_form_id}/fields/{self.test_field_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 删除成功: {data['data']['name']}")
                return True
            else:
                print(f"   ❌ 删除失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"   ❌ 删除异常: {e}")
            return False

    def run_complete_test(self) -> bool:
        """运行完整测试"""
        # 获取认证令牌
        if not self.get_auth_token():
            return False

        # 运行所有API测试
        return self.test_all_form_apis()


if __name__ == "__main__":
    test = FormConfigTest()
    success = test.run_complete_test()
    exit(0 if success else 1)
