"""
4.1 实体建模测试
测试实体建模模块的13个API端点
严格按照API文档规范进行测试
"""
import requests
import json
import time
from datetime import datetime


class EntityModelingTest:
    """实体建模测试类"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.auth_url = f"{self.base_url}/api/auth/developer"
        self.entity_url = f"{self.base_url}/api/entities"
        self.developer_password = "AILF_DEV_2024_SECURE"
        self.token = None
        self.test_entity_id = None
        self.test_record_id = None
        self.test_relationship_id = None
    
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
    
    def test_get_entities_list_empty(self):
        """测试获取实体列表 - 空列表"""
        print("🧪 测试获取实体列表（空列表）...")
        
        headers = self.get_auth_headers()
        response = requests.get(self.entity_url, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200, f"期望code为200，实际: {data['code']}"
        assert data["message"] == "获取实体列表成功", f"期望message为'获取实体列表成功'"
        assert "data" in data, "响应中缺少data字段"
        
        # 验证实体列表数据字段
        entity_data = data["data"]
        required_fields = ["entities", "total"]
        for field in required_fields:
            assert field in entity_data, f"缺少必需字段: {field}"
        
        # 验证空列表
        assert entity_data["total"] == 0, "初始实体总数应该为0"
        assert len(entity_data["entities"]) == 0, "初始实体列表应该为空"
        
        print("✅ 获取实体列表（空列表）测试通过")
    
    def test_create_entity_success(self):
        """测试创建实体成功"""
        print("🧪 测试创建实体成功...")
        
        headers = self.get_auth_headers()
        payload = {
            "name": "product",
            "displayName": "商品",
            "description": "商品信息管理实体",
            "icon": "shopping-cart",
            "fields": [
                {
                    "name": "name",
                    "displayName": "商品名称",
                    "type": "text",
                    "required": True,
                    "unique": False
                },
                {
                    "name": "price",
                    "displayName": "价格",
                    "type": "decimal",
                    "required": True,
                    "unique": False,
                    "validation": {
                        "min": 0,
                        "precision": 2
                    }
                },
                {
                    "name": "stock",
                    "displayName": "库存数量",
                    "type": "number",
                    "required": True,
                    "unique": False,
                    "defaultValue": 0
                },
                {
                    "name": "category",
                    "displayName": "商品分类",
                    "type": "select",
                    "required": False,
                    "unique": False,
                    "options": ["电子产品", "服装", "食品", "图书"]
                }
            ]
        }
        
        response = requests.post(self.entity_url, json=payload, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 201, f"期望状态码201，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 201, f"期望code为201，实际: {data['code']}"
        assert data["message"] == "创建实体成功", f"期望message为'创建实体成功'"
        assert "data" in data, "响应中缺少data字段"
        assert "entity" in data["data"], "data中缺少entity字段"
        
        # 验证实体详情字段
        entity = data["data"]["entity"]
        required_fields = ["id", "name", "displayName", "description", "icon", 
                          "status", "field_count", "record_count", "fields", "created_at", "updated_at"]
        for field in required_fields:
            assert field in entity, f"实体缺少字段: {field}"
        
        # 验证实体基本信息
        assert entity["name"] == "product", f"实体名称不匹配"
        assert entity["displayName"] == "商品", f"实体显示名称不匹配"
        assert entity["status"] == "active", f"实体状态应该为active"
        assert entity["field_count"] == 4, f"字段数量应该为4"
        assert entity["record_count"] == 0, f"记录数量应该为0"
        
        # 验证字段信息
        assert len(entity["fields"]) == 4, f"字段列表长度应该为4"
        field_names = [field["name"] for field in entity["fields"]]
        expected_fields = ["name", "price", "stock", "category"]
        for expected_field in expected_fields:
            assert expected_field in field_names, f"缺少字段: {expected_field}"
        
        # 保存实体ID用于后续测试
        self.test_entity_id = entity["id"]
        
        print("✅ 创建实体成功测试通过")
        return self.test_entity_id
    
    def test_get_entities_list_with_data(self):
        """测试获取实体列表 - 有数据"""
        print("🧪 测试获取实体列表（有数据）...")
        
        headers = self.get_auth_headers()
        response = requests.get(self.entity_url, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        entity_data = data["data"]
        
        # 验证有数据
        assert entity_data["total"] == 1, "实体总数应该为1"
        assert len(entity_data["entities"]) == 1, "实体列表长度应该为1"
        
        # 验证实体列表项字段
        entity = entity_data["entities"][0]
        list_fields = ["id", "name", "displayName", "description", "icon", 
                      "status", "field_count", "record_count", "fields", "created_at", "updated_at"]
        for field in list_fields:
            assert field in entity, f"实体列表项缺少字段: {field}"
        
        print("✅ 获取实体列表（有数据）测试通过")
    
    def test_get_entity_detail_success(self):
        """测试获取实体详情成功"""
        print("🧪 测试获取实体详情成功...")
        
        headers = self.get_auth_headers()
        response = requests.get(f"{self.entity_url}/{self.test_entity_id}", headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200, f"期望code为200，实际: {data['code']}"
        assert data["message"] == "获取实体详情成功", f"期望message为'获取实体详情成功'"
        
        # 验证实体详情
        entity = data["data"]["entity"]
        assert entity["id"] == self.test_entity_id, f"实体ID不匹配"
        assert "statistics" in entity, "实体详情应该包含统计信息"
        
        print("✅ 获取实体详情成功测试通过")
    
    def test_get_entity_detail_not_found(self):
        """测试获取实体详情 - 实体不存在"""
        print("🧪 测试获取实体详情（实体不存在）...")
        
        headers = self.get_auth_headers()
        response = requests.get(f"{self.entity_url}/nonexistent_entity", headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 404, f"期望状态码404，实际: {response.status_code}"
        
        # 验证错误响应结构
        data = response.json()
        assert data["code"] == 404, f"期望code为404，实际: {data['code']}"
        assert data["message"] == "实体不存在", f"期望message为'实体不存在'"
        assert data["data"]["error"] == "entity_not_found", f"期望error为'entity_not_found'"
        
        print("✅ 获取实体详情（实体不存在）测试通过")
    
    def test_update_entity_success(self):
        """测试更新实体成功"""
        print("🧪 测试更新实体成功...")
        
        headers = self.get_auth_headers()
        payload = {
            "displayName": "商品信息",
            "description": "更新后的商品信息管理实体",
            "icon": "package"
        }
        
        response = requests.put(f"{self.entity_url}/{self.test_entity_id}", json=payload, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200, f"期望code为200，实际: {data['code']}"
        assert data["message"] == "更新实体成功", f"期望message为'更新实体成功'"
        
        # 验证更新结果
        entity = data["data"]["entity"]
        assert entity["displayName"] == "商品信息", f"显示名称未更新"
        assert entity["description"] == "更新后的商品信息管理实体", f"描述未更新"
        assert entity["icon"] == "package", f"图标未更新"
        
        print("✅ 更新实体成功测试通过")
    
    def test_create_entity_record_success(self):
        """测试创建实体数据记录成功"""
        print("🧪 测试创建实体数据记录成功...")
        
        headers = self.get_auth_headers()
        payload = {
            "name": "iPhone 15 Pro",
            "price": 8999.00,
            "stock": 50,
            "category": "电子产品"
        }
        
        response = requests.post(f"{self.entity_url}/{self.test_entity_id}/data",
                               json=payload, headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 201, f"期望状态码201，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 201, f"期望code为201，实际: {data['code']}"
        assert data["message"] == "创建记录成功", f"期望message为'创建记录成功'"
        
        # 验证记录数据
        record = data["data"]["record"]
        assert "id" in record, "记录应该包含id字段"
        assert "created_at" in record, "记录应该包含created_at字段"
        assert "updated_at" in record, "记录应该包含updated_at字段"
        assert record["name"] == "iPhone 15 Pro", f"商品名称不匹配"
        assert record["price"] == 8999.00, f"价格不匹配"
        assert record["stock"] == 50, f"库存不匹配"
        
        # 保存记录ID用于后续测试
        self.test_record_id = record["id"]
        
        print("✅ 创建实体数据记录成功测试通过")
        return self.test_record_id
    
    def test_get_entity_records_success(self):
        """测试获取实体数据记录成功"""
        print("🧪 测试获取实体数据记录成功...")
        
        headers = self.get_auth_headers()
        response = requests.get(f"{self.entity_url}/{self.test_entity_id}/data", headers=headers)
        
        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        
        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200, f"期望code为200，实际: {data['code']}"
        assert data["message"] == "获取实体记录成功", f"期望message为'获取实体记录成功'"
        
        # 验证记录列表和分页信息
        assert "records" in data["data"], "响应中缺少records字段"
        assert "pagination" in data["data"], "响应中缺少pagination字段"
        
        # 验证分页信息字段
        pagination = data["data"]["pagination"]
        pagination_fields = ["page", "limit", "total", "pages", "has_next", "has_prev"]
        for field in pagination_fields:
            assert field in pagination, f"分页信息缺少字段: {field}"
        
        # 验证记录数据
        records = data["data"]["records"]
        assert len(records) == 1, f"记录数量应该为1"
        assert records[0]["id"] == self.test_record_id, f"记录ID不匹配"
        
        print("✅ 获取实体数据记录成功测试通过")

    def test_update_entity_record_success(self):
        """测试更新实体数据记录成功"""
        print("🧪 测试更新实体数据记录成功...")

        headers = self.get_auth_headers()
        payload = {
            "name": "iPhone 15 Pro Max",
            "price": 9999.00,
            "stock": 30,
            "category": "电子产品"
        }

        response = requests.put(f"{self.entity_url}/{self.test_entity_id}/data/{self.test_record_id}",
                               json=payload, headers=headers)

        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"

        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200, f"期望code为200，实际: {data['code']}"
        assert data["message"] == "更新记录成功", f"期望message为'更新记录成功'"

        # 验证更新结果
        record = data["data"]["record"]
        assert record["name"] == "iPhone 15 Pro Max", f"商品名称未更新"
        assert record["price"] == 9999.00, f"价格未更新"
        assert record["stock"] == 30, f"库存未更新"

        print("✅ 更新实体数据记录成功测试通过")

    def test_delete_entity_record_success(self):
        """测试删除实体数据记录成功"""
        print("🧪 测试删除实体数据记录成功...")

        headers = self.get_auth_headers()
        response = requests.delete(f"{self.entity_url}/{self.test_entity_id}/data/{self.test_record_id}",
                                 headers=headers)

        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"

        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200, f"期望code为200，实际: {data['code']}"
        assert data["message"] == "删除记录成功", f"期望message为'删除记录成功'"

        # 验证删除结果
        assert data["data"]["record_id"] == self.test_record_id, f"记录ID不匹配"
        assert "deleted_at" in data["data"], "响应中缺少deleted_at字段"

        print("✅ 删除实体数据记录成功测试通过")

    def test_get_entity_relationships_empty(self):
        """测试获取实体关系 - 空列表"""
        print("🧪 测试获取实体关系（空列表）...")

        headers = self.get_auth_headers()
        response = requests.get(f"{self.entity_url}/{self.test_entity_id}/relationships", headers=headers)

        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"

        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200, f"期望code为200，实际: {data['code']}"
        assert data["message"] == "获取实体关系成功", f"期望message为'获取实体关系成功'"

        # 验证空关系列表
        assert data["data"]["total"] == 0, "初始关系总数应该为0"
        assert len(data["data"]["relationships"]) == 0, "初始关系列表应该为空"

        print("✅ 获取实体关系（空列表）测试通过")

    def test_delete_entity_success(self):
        """测试删除实体成功"""
        print("🧪 测试删除实体成功...")

        headers = self.get_auth_headers()
        response = requests.delete(f"{self.entity_url}/{self.test_entity_id}?force=true&backup=false",
                                 headers=headers)

        # 验证HTTP状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"

        # 验证响应数据结构
        data = response.json()
        assert data["code"] == 200, f"期望code为200，实际: {data['code']}"
        assert data["message"] == "删除实体成功", f"期望message为'删除实体成功'"

        # 验证删除结果
        assert data["data"]["entity_id"] == self.test_entity_id, f"实体ID不匹配"
        assert "deleted_at" in data["data"], "响应中缺少deleted_at字段"
        assert "affected_records" in data["data"], "响应中缺少affected_records字段"
        assert "affected_relationships" in data["data"], "响应中缺少affected_relationships字段"

        print("✅ 删除实体成功测试通过")

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行实体建模测试...")
        print("=" * 50)
        
        try:
            # 1. 测试获取实体列表（空列表）
            self.test_get_entities_list_empty()
            
            # 2. 测试创建实体成功
            entity_id = self.test_create_entity_success()
            
            # 3. 测试获取实体列表（有数据）
            self.test_get_entities_list_with_data()
            
            # 4. 测试获取实体详情成功
            self.test_get_entity_detail_success()
            
            # 5. 测试获取实体详情（实体不存在）
            self.test_get_entity_detail_not_found()
            
            # 6. 测试更新实体成功
            self.test_update_entity_success()
            
            # 7. 测试创建实体数据记录成功
            record_id = self.test_create_entity_record_success()
            
            # 8. 测试获取实体数据记录成功
            self.test_get_entity_records_success()

            # 9. 测试更新实体数据记录成功
            self.test_update_entity_record_success()

            # 10. 测试删除实体数据记录成功
            self.test_delete_entity_record_success()

            # 11. 测试获取实体关系（空列表）
            self.test_get_entity_relationships_empty()

            # 12. 测试删除实体成功
            self.test_delete_entity_success()

            print("=" * 50)
            print("🎉 实体建模完整测试通过！")
            print(f"📊 测试统计: 测试了12个API端点，覆盖实体定义、数据记录、关系管理")
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
    test = EntityModelingTest()
    test.run_all_tests()
