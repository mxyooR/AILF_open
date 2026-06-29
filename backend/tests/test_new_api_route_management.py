"""
API路由管理模块完整测试
符合新API文档要求，测试所有8个端点和新功能
"""
import requests
import json
import time
import sys
from typing import Dict, Any


class APIRouteManagementTester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.token = None
        self.headers = None
        self.test_results = []
        self.created_routes = []  # 存储创建的路由ID用于清理
        
    def get_auth_token(self) -> str:
        """获取认证令牌"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/developer",
                json={"password": "AILF_DEV_2024_SECURE"}
            )
            if response.status_code == 200:
                token = response.json()["data"]["token"]
                self.headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                return token
            else:
                raise Exception(f"认证失败: {response.text}")
        except Exception as e:
            print(f"❌ 获取认证令牌失败: {e}")
            sys.exit(1)

    def validate_standard_response(self, response: requests.Response, expected_code: int) -> Dict[str, Any]:
        """验证统一响应格式"""
        try:
            data = response.json()
            
            # 验证基本结构
            required_fields = ["code", "message", "data", "meta"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 验证meta字段结构
            meta_fields = ["timestamp", "request_id", "api_version"]
            for field in meta_fields:
                if field not in data["meta"]:
                    raise ValueError(f"meta中缺少必需字段: {field}")
            
            # 验证状态码
            if data["code"] != expected_code:
                raise ValueError(f"响应码不匹配: 期望{expected_code}, 得到{data['code']}")
            
            return data
            
        except json.JSONDecodeError:
            raise ValueError("响应不是有效的JSON格式")

    def test_register_route(self) -> str:
        """测试1: 动态注册新的API路由"""
        print("\n1️⃣ 测试动态注册新的API路由 (POST /api/routes/register)")
        print("=" * 60)
        
        # 测试用例1: 完整的路由注册
        route_data = {
            "api_id": "test_product_create_api",
            "name": "测试商品创建API", 
            "endpoint": "/api/test/products",
            "method": "POST",
            "description": "创建新商品的测试API，支持商品基本信息录入",
            "auth_required": True,
            "handler": {
                "type": "entity_crud",
                "config": {
                    "entity": "product",
                    "operation": "create",
                    "allowed_fields": ["name", "price", "description", "category_id"],
                    "validation_rules": {
                        "name": "required|max:100",
                        "price": "required|numeric|min:0.01"
                    },
                    "relations": ["category"],
                    "auto_timestamps": True
                }
            },
            "parameters": [
                {
                    "name": "name",
                    "type": "string",
                    "location": "body",
                    "required": True,
                    "description": "商品名称",
                    "validation": {
                        "max_length": 100,
                        "min_length": 2
                    }
                },
                {
                    "name": "price",
                    "type": "number",
                    "location": "body",
                    "required": True,
                    "description": "商品价格",
                    "validation": {
                        "min": 0.01,
                        "max": 999999.99
                    }
                },
                {
                    "name": "description",
                    "type": "string",
                    "location": "body",
                    "required": False,
                    "description": "商品描述"
                }
            ],
            "responses": {
                "201": {
                    "description": "商品创建成功",
                    "response_schema": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "integer", "example": 201},
                            "message": {"type": "string", "example": "商品创建成功"},
                            "data": {
                                "type": "object",
                                "properties": {
                                    "product": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string"},
                                            "name": {"type": "string"},
                                            "price": {"type": "number"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "headers": {}
                },
                "400": {
                    "description": "请求参数验证失败",
                    "response_schema": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "integer", "example": 400},
                            "message": {"type": "string"},
                            "data": {"type": "object"}
                        }
                    },
                    "headers": {}
                }
            },
            "form_config": {
                "auto_generate": True,
                "layout": {
                    "type": "grid",
                    "columns": 2,
                    "spacing": 16
                },
                "sections": [
                    {
                        "title": "基本信息",
                        "fields": ["name", "price"]
                    },
                    {
                        "title": "详细信息",
                        "fields": ["description"]
                    }
                ]
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/routes/register",
                json=route_data,
                headers=self.headers
            )
            
            print(f"📤 发送请求: POST /api/routes/register")
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 201:
                data = self.validate_standard_response(response, 201)
                
                # 验证响应数据结构
                required_data_fields = ["route", "form", "statistics"]
                for field in required_data_fields:
                    if field not in data["data"]:
                        raise ValueError(f"响应data中缺少字段: {field}")
                
                route_info = data["data"]["route"]
                route_id = route_info["id"]
                self.created_routes.append(route_id)
                
                print(f"✅ 路由注册成功")
                print(f"   📋 路由ID: {route_id}")
                print(f"   📋 路由名称: {route_info['name']}")
                print(f"   📋 访问URL: {route_info.get('access_url', 'N/A')}")
                print(f"   📋 关联表单: {data['data']['form']['name']}")
                print(f"   📋 表单字段数: {data['data']['form']['field_count']}")
                print(f"   ⏱️  处理时间: {data['meta'].get('execution_time', 'N/A')}ms")
                
                self.test_results.append({
                    "test": "register_route",
                    "status": "PASS",
                    "message": "API路由注册成功，响应格式正确"
                })
                
                return route_id
                
            else:
                error_data = response.json()
                print(f"❌ 路由注册失败")
                print(f"   错误信息: {error_data.get('message', 'Unknown error')}")
                self.test_results.append({
                    "test": "register_route", 
                    "status": "FAIL",
                    "message": f"状态码: {response.status_code}, 错误: {error_data}"
                })
                return None
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            self.test_results.append({
                "test": "register_route",
                "status": "ERROR", 
                "message": str(e)
            })
            return None

    def test_route_conflict(self):
        """测试路由冲突检测"""
        print("\n   测试路由冲突检测...")
        
        # 尝试注册相同的路由
        duplicate_route = {
            "api_id": "test_product_create_api_duplicate",
            "name": "重复的商品API",
            "endpoint": "/api/test/products",  # 相同的端点
            "method": "POST",  # 相同的方法
            "description": "应该失败的重复路由",
            "auth_required": True,
            "handler": {
                "type": "entity_crud",
                "config": {
                    "entity": "product",
                    "operation": "create"
                }
            },
            "parameters": [],
            "responses": {
                "201": {
                    "description": "成功",
                    "response_schema": {"type": "object"},
                    "headers": {}
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/routes/register",
                json=duplicate_route,
                headers=self.headers
            )
            
            if response.status_code == 409:
                error_data = response.json()
                print(f"✅ 路由冲突检测正常工作")
                print(f"   错误类型: {error_data['data']['error_type']}")
                print(f"   冲突端点: {error_data['data']['details']['conflicting_endpoint']}")
                
                self.test_results.append({
                    "test": "route_conflict_detection",
                    "status": "PASS",
                    "message": "路由冲突检测正常"
                })
            else:
                print(f"❌ 路由冲突检测失败，应该返回409状态码")
                self.test_results.append({
                    "test": "route_conflict_detection",
                    "status": "FAIL", 
                    "message": f"期望409状态码，得到{response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ 路由冲突测试异常: {e}")
            self.test_results.append({
                "test": "route_conflict_detection",
                "status": "ERROR",
                "message": str(e)
            })

    def test_get_routes_list(self):
        """测试2: 获取API路由列表"""
        print("\n2️⃣ 测试获取API路由列表 (GET /api/routes)")
        print("=" * 60)
        
        # 测试基础查询
        try:
            response = requests.get(
                f"{self.base_url}/api/routes",
                headers=self.headers
            )
            
            print(f"📤 发送请求: GET /api/routes")
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = self.validate_standard_response(response, 200)
                
                # 验证响应数据结构
                required_fields = ["routes", "pagination", "summary"]
                for field in required_fields:
                    if field not in data["data"]:
                        raise ValueError(f"响应data中缺少字段: {field}")
                
                routes = data["data"]["routes"]
                pagination = data["data"]["pagination"]
                summary = data["data"]["summary"]
                
                print(f"✅ 获取路由列表成功")
                print(f"   📋 路由总数: {pagination['total']}")
                print(f"   📋 当前页面: {pagination['page']}/{pagination['pages']}")
                print(f"   📋 活跃路由: {summary['active_routes']}")
                print(f"   📋 非活跃路由: {summary['inactive_routes']}")
                print(f"   ⏱️  处理时间: {data['meta'].get('execution_time', 'N/A')}ms")
                
                # 验证路由项结构
                if routes:
                    first_route = routes[0]
                    required_route_fields = ["id", "api_id", "name", "endpoint", "method", "status", "handler"]
                    for field in required_route_fields:
                        if field not in first_route:
                            raise ValueError(f"路由项中缺少字段: {field}")
                    
                    print(f"   📋 示例路由: {first_route['name']} ({first_route['method']} {first_route['endpoint']})")
                    if "statistics" in first_route:
                        stats = first_route["statistics"]
                        print(f"   📊 调用统计: {stats.get('call_count', 0)}次, 成功率: {stats.get('success_rate', 0)}%")
                
                self.test_results.append({
                    "test": "get_routes_list",
                    "status": "PASS",
                    "message": f"成功获取{len(routes)}个路由"
                })
                
            else:
                error_data = response.json()
                print(f"❌ 获取路由列表失败")
                print(f"   错误信息: {error_data.get('message', 'Unknown error')}")
                self.test_results.append({
                    "test": "get_routes_list",
                    "status": "FAIL",
                    "message": f"状态码: {response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            self.test_results.append({
                "test": "get_routes_list",
                "status": "ERROR",
                "message": str(e)
            })

    def test_advanced_filtering(self):
        """测试高级筛选功能"""
        print("\n   测试高级筛选和排序...")
        
        # 测试各种筛选参数
        filter_tests = [
            {"status": "active", "desc": "按状态筛选"},
            {"method": "POST", "desc": "按HTTP方法筛选"},
            {"handler_type": "entity_crud", "desc": "按处理器类型筛选"},
            {"search": "商品", "desc": "按名称搜索"},
            {"sort": "name", "order": "asc", "desc": "按名称排序"},
            {"include_stats": "true", "include_forms": "true", "desc": "包含统计和表单信息"}
        ]
        
        for filter_test in filter_tests:
            desc = filter_test.pop("desc")
            try:
                response = requests.get(
                    f"{self.base_url}/api/routes",
                    params=filter_test,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ {desc}: 返回{len(data['data']['routes'])}个结果")
                    
                    # 验证筛选条件是否被应用
                    if "filters_applied" in data["data"]:
                        applied = data["data"]["filters_applied"]
                        print(f"      应用的筛选: {applied}")
                else:
                    print(f"   ❌ {desc}: 状态码{response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {desc}: 异常{e}")

    def test_get_route_detail(self, route_id: str):
        """测试3: 获取路由详情"""
        print("\n3️⃣ 测试获取路由详情 (GET /api/routes/{route_id})")
        print("=" * 60)
        
        if not route_id:
            print("⚠️ 跳过路由详情测试 - 没有有效的路由ID")
            return
        
        try:
            response = requests.get(
                f"{self.base_url}/api/routes/{route_id}",
                headers=self.headers
            )
            
            print(f"📤 发送请求: GET /api/routes/{route_id}")
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = self.validate_standard_response(response, 200)
                
                # 验证路由详情结构
                route_detail = data["data"]
                print(f"✅ 获取路由详情成功")
                print(f"   📋 路由名称: {route_detail.get('name', 'N/A')}")
                print(f"   📋 API端点: {route_detail.get('endpoint', 'N/A')}")
                print(f"   📋 HTTP方法: {route_detail.get('method', 'N/A')}")
                print(f"   📋 处理器类型: {route_detail.get('handler', {}).get('type', 'N/A')}")
                print(f"   ⏱️  处理时间: {data['meta'].get('execution_time', 'N/A')}ms")
                
                self.test_results.append({
                    "test": "get_route_detail",
                    "status": "PASS",
                    "message": "成功获取路由详情"
                })
                
            else:
                error_data = response.json()
                print(f"❌ 获取路由详情失败")
                print(f"   错误信息: {error_data.get('message', 'Unknown error')}")
                self.test_results.append({
                    "test": "get_route_detail",
                    "status": "FAIL",
                    "message": f"状态码: {response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            self.test_results.append({
                "test": "get_route_detail",
                "status": "ERROR",
                "message": str(e)
            })

    def test_update_route(self, route_id: str):
        """测试4: 更新路由"""
        print("\n4️⃣ 测试更新路由 (PUT /api/routes/{route_id})")
        print("=" * 60)
        
        if not route_id:
            print("⚠️ 跳过路由更新测试 - 没有有效的路由ID")
            return
        
        update_data = {
            "name": "测试商品创建API（已更新）",
            "description": "更新后的商品创建API，支持更多字段",
            "handler": {
                "config": {
                    "entity": "product",
                    "operation": "create",
                    "allowed_fields": ["name", "price", "description", "category_id", "brand_id"],
                    "validation_rules": {
                        "name": "required|max:100|unique:products,name",
                        "price": "required|numeric|min:0.01",
                        "brand_id": "exists:brands,id"
                    },
                    "batch_support": True
                }
            }
        }
        
        try:
            response = requests.put(
                f"{self.base_url}/api/routes/{route_id}",
                json=update_data,
                headers=self.headers
            )
            
            print(f"📤 发送请求: PUT /api/routes/{route_id}")
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = self.validate_standard_response(response, 200)
                
                # 验证更新响应结构
                required_fields = ["route", "changes", "version"]
                for field in required_fields:
                    if field not in data["data"]:
                        print(f"⚠️ 响应data中缺少字段: {field}")
                
                route_info = data["data"]["route"]
                changes = data["data"].get("changes", {})
                
                print(f"✅ 路由更新成功")
                print(f"   📋 更新后名称: {route_info['name']}")
                print(f"   📋 更新字段: {changes.get('updated_fields', [])}")
                print(f"   📋 版本号: {data['data'].get('version', {}).get('current', 'N/A')}")
                print(f"   ⏱️  处理时间: {data['meta'].get('execution_time', 'N/A')}ms")
                
                self.test_results.append({
                    "test": "update_route",
                    "status": "PASS", 
                    "message": "路由更新成功"
                })
                
            else:
                error_data = response.json()
                print(f"❌ 路由更新失败")
                print(f"   错误信息: {error_data.get('message', 'Unknown error')}")
                self.test_results.append({
                    "test": "update_route",
                    "status": "FAIL",
                    "message": f"状态码: {response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            self.test_results.append({
                "test": "update_route",
                "status": "ERROR",
                "message": str(e)
            })

    def test_activate_route(self, route_id: str):
        """测试5: 激活路由"""
        print("\n5️⃣ 测试激活路由 (POST /api/routes/{route_id}/activate)")
        print("=" * 60)
        
        if not route_id:
            print("⚠️ 跳过路由激活测试 - 没有有效的路由ID")
            return
        
        try:
            response = requests.post(
                f"{self.base_url}/api/routes/{route_id}/activate",
                params={"health_check": "true", "warm_up": "true"},
                headers=self.headers
            )
            
            print(f"📤 发送请求: POST /api/routes/{route_id}/activate")
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = self.validate_standard_response(response, 200)
                
                # 验证激活响应结构
                required_fields = ["route", "activation_details", "access_info"]
                for field in required_fields:
                    if field not in data["data"]:
                        print(f"⚠️ 响应data中缺少字段: {field}")
                
                route_info = data["data"]["route"]
                activation_details = data["data"].get("activation_details", {})
                access_info = data["data"].get("access_info", {})
                
                print(f"✅ 路由激活成功")
                print(f"   📋 路由状态: {route_info['status']}")
                print(f"   📋 激活时间: {route_info.get('activated_at', 'N/A')}")
                print(f"   📋 健康检查: {activation_details.get('health_check', {}).get('status', 'N/A')}")
                print(f"   📋 预热状态: {activation_details.get('warm_up', {}).get('status', 'N/A')}")
                print(f"   📋 访问URL: {access_info.get('url', 'N/A')}")
                print(f"   ⏱️  处理时间: {data['meta'].get('execution_time', 'N/A')}ms")
                
                self.test_results.append({
                    "test": "activate_route",
                    "status": "PASS",
                    "message": "路由激活成功"
                })
                
            else:
                error_data = response.json()
                print(f"❌ 路由激活失败")
                print(f"   错误信息: {error_data.get('message', 'Unknown error')}")
                self.test_results.append({
                    "test": "activate_route",
                    "status": "FAIL",
                    "message": f"状态码: {response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            self.test_results.append({
                "test": "activate_route",
                "status": "ERROR",
                "message": str(e)
            })

    def test_deactivate_route(self, route_id: str):
        """测试6: 停用路由"""
        print("\n6️⃣ 测试停用路由 (POST /api/routes/{route_id}/deactivate)")
        print("=" * 60)
        
        if not route_id:
            print("⚠️ 跳过路由停用测试 - 没有有效的路由ID")
            return
        
        try:
            response = requests.post(
                f"{self.base_url}/api/routes/{route_id}/deactivate", 
                params={"graceful": "true", "timeout": "30"},
                headers=self.headers
            )
            
            print(f"📤 发送请求: POST /api/routes/{route_id}/deactivate")
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = self.validate_standard_response(response, 200)
                
                # 验证停用响应结构
                required_fields = ["route", "deactivation_details", "final_statistics"]
                for field in required_fields:
                    if field not in data["data"]:
                        print(f"⚠️ 响应data中缺少字段: {field}")
                
                route_info = data["data"]["route"]
                deactivation_details = data["data"].get("deactivation_details", {})
                final_stats = data["data"].get("final_statistics", {})
                
                print(f"✅ 路由停用成功")
                print(f"   📋 路由状态: {route_info['status']}")
                print(f"   📋 停用时间: {route_info.get('deactivated_at', 'N/A')}")
                print(f"   📋 停用模式: {deactivation_details.get('mode', 'N/A')}")
                print(f"   📋 处理请求数: {deactivation_details.get('active_requests_handled', 0)}")
                print(f"   📋 最终成功率: {final_stats.get('final_success_rate', 0)}%")
                print(f"   ⏱️  处理时间: {data['meta'].get('execution_time', 'N/A')}ms")
                
                self.test_results.append({
                    "test": "deactivate_route",
                    "status": "PASS",
                    "message": "路由停用成功"
                })
                
            else:
                error_data = response.json()
                print(f"❌ 路由停用失败")
                print(f"   错误信息: {error_data.get('message', 'Unknown error')}")
                self.test_results.append({
                    "test": "deactivate_route",
                    "status": "FAIL",
                    "message": f"状态码: {response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            self.test_results.append({
                "test": "deactivate_route",
                "status": "ERROR",
                "message": str(e)
            })

    def test_get_route_status(self, route_id: str):
        """测试7: 获取路由状态"""
        print("\n7️⃣ 测试获取路由状态 (GET /api/routes/{route_id}/status)")
        print("=" * 60)
        
        if not route_id:
            print("⚠️ 跳过路由状态测试 - 没有有效的路由ID")
            return
        
        try:
            response = requests.get(
                f"{self.base_url}/api/routes/{route_id}/status",
                params={"period": "24h", "include_trends": "true", "include_errors": "true"},
                headers=self.headers
            )
            
            print(f"📤 发送请求: GET /api/routes/{route_id}/status")
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = self.validate_standard_response(response, 200)
                
                # 验证状态响应结构
                required_fields = ["route", "statistics", "performance"]
                for field in required_fields:
                    if field not in data["data"]:
                        print(f"⚠️ 响应data中缺少字段: {field}")
                
                route_info = data["data"]["route"]
                statistics = data["data"].get("statistics", {})
                performance = data["data"].get("performance", {})
                
                print(f"✅ 获取路由状态成功")
                print(f"   📋 路由名称: {route_info.get('name', 'N/A')}")
                print(f"   📋 当前状态: {route_info.get('status', 'N/A')}")
                print(f"   📊 调用总数: {statistics.get('total_calls', 0)}")
                print(f"   📊 成功率: {statistics.get('success_rate', 0)}%")
                print(f"   📊 平均响应时间: {statistics.get('avg_response_time', 0)}ms")
                print(f"   📊 健康状态: {performance.get('health_status', 'N/A')}")
                print(f"   📊 健康评分: {performance.get('health_score', 0)}")
                
                # 检查趋势数据
                if "trends" in data["data"]:
                    trends = data["data"]["trends"]
                    print(f"   📈 包含趋势数据: {len(trends.get('hourly_calls', []))}小时数据")
                
                # 检查错误分析
                if "error_analysis" in data["data"]:
                    error_analysis = data["data"]["error_analysis"]
                    print(f"   🚨 近期错误: {len(error_analysis.get('recent_errors', []))}个")
                
                print(f"   ⏱️  处理时间: {data['meta'].get('execution_time', 'N/A')}ms")
                
                self.test_results.append({
                    "test": "get_route_status",
                    "status": "PASS",
                    "message": "成功获取路由状态"
                })
                
            else:
                error_data = response.json()
                print(f"❌ 获取路由状态失败")
                print(f"   错误信息: {error_data.get('message', 'Unknown error')}")
                self.test_results.append({
                    "test": "get_route_status",
                    "status": "FAIL",
                    "message": f"状态码: {response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            self.test_results.append({
                "test": "get_route_status",
                "status": "ERROR",
                "message": str(e)
            })

    def test_check_routes_health(self):
        """测试8: 检查所有路由健康状态"""
        print("\n8️⃣ 测试检查所有路由健康状态 (GET /api/routes/health)")
        print("=" * 60)
        
        try:
            response = requests.get(
                f"{self.base_url}/api/routes/health",
                params={"detailed": "true", "include_inactive": "false"},
                headers=self.headers
            )
            
            print(f"📤 发送请求: GET /api/routes/health")
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = self.validate_standard_response(response, 200)
                
                # 验证健康检查响应结构
                required_fields = ["overall_status", "health_score", "summary", "system_metrics"]
                for field in required_fields:
                    if field not in data["data"]:
                        print(f"⚠️ 响应data中缺少字段: {field}")
                
                overall_status = data["data"]["overall_status"]
                health_score = data["data"]["health_score"]
                summary = data["data"].get("summary", {})
                system_metrics = data["data"].get("system_metrics", {})
                
                print(f"✅ 系统健康检查完成")
                print(f"   📊 整体状态: {overall_status}")
                print(f"   📊 健康评分: {health_score}")
                print(f"   📊 总路由数: {summary.get('total_routes', 0)}")
                print(f"   📊 健康路由: {summary.get('healthy_routes', 0)}")
                print(f"   📊 警告路由: {summary.get('warning_routes', 0)}")
                print(f"   📊 不健康路由: {summary.get('unhealthy_routes', 0)}")
                print(f"   📊 系统成功率: {system_metrics.get('overall_success_rate', 0):.1f}%")
                print(f"   📊 平均响应时间: {system_metrics.get('avg_response_time', 0)}ms")
                print(f"   📊 每秒请求数: {system_metrics.get('requests_per_second', 0):.1f}")
                
                # 检查推荐信息
                if "recommendations" in data["data"]:
                    recommendations = data["data"]["recommendations"]
                    print(f"   💡 优化建议: {len(recommendations)}条")
                    for rec in recommendations[:2]:  # 显示前2条建议
                        print(f"      - {rec.get('description', 'N/A')}")
                
                print(f"   ⏱️  检查耗时: {data['meta'].get('execution_time', 'N/A')}ms")
                
                self.test_results.append({
                    "test": "check_routes_health",
                    "status": "PASS",
                    "message": f"系统健康检查完成，整体状态: {overall_status}"
                })
                
            else:
                error_data = response.json()
                print(f"❌ 健康检查失败")
                print(f"   错误信息: {error_data.get('message', 'Unknown error')}")
                self.test_results.append({
                    "test": "check_routes_health",
                    "status": "FAIL",
                    "message": f"状态码: {response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            self.test_results.append({
                "test": "check_routes_health",
                "status": "ERROR",
                "message": str(e)
            })

    def test_delete_route(self, route_id: str):
        """测试删除路由"""
        print("\n9️⃣ 测试删除路由 (DELETE /api/routes/{route_id})")
        print("=" * 60)
        
        if not route_id:
            print("⚠️ 跳过路由删除测试 - 没有有效的路由ID")
            return
        
        try:
            # 首先测试安全删除（应该失败，因为路由可能在使用中）
            response = requests.delete(
                f"{self.base_url}/api/routes/{route_id}",
                params={"force": "false", "backup": "true"},
                headers=self.headers
            )
            
            print(f"📤 发送请求: DELETE /api/routes/{route_id} (安全删除)")
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 409:
                # 期望的冲突响应
                error_data = response.json()
                print(f"✅ 安全删除检测正常工作")
                print(f"   错误类型: {error_data['data']['error_type']}")
                print(f"   建议操作: 强制删除")
                
                # 现在进行强制删除
                print(f"\n   执行强制删除...")
                response2 = requests.delete(
                    f"{self.base_url}/api/routes/{route_id}",
                    params={"force": "true", "backup": "true", "cascade": "true"},
                    headers=self.headers
                )
                
                if response2.status_code == 200:
                    data = self.validate_standard_response(response2, 200)
                    
                    # 验证删除响应结构
                    required_fields = ["deleted_route", "cleanup_summary", "affected_objects"]
                    for field in required_fields:
                        if field not in data["data"]:
                            print(f"⚠️ 响应data中缺少字段: {field}")
                    
                    deleted_route = data["data"]["deleted_route"]
                    cleanup_summary = data["data"].get("cleanup_summary", {})
                    
                    print(f"✅ 路由强制删除成功")
                    print(f"   📋 删除路由: {deleted_route['name']}")
                    print(f"   📋 删除时间: {deleted_route.get('deleted_at', 'N/A')}")
                    print(f"   📋 数据库清理: {cleanup_summary.get('database_record_deleted', False)}")
                    print(f"   📋 缓存清理: {cleanup_summary.get('cache_cleared', False)}")
                    print(f"   📋 备份创建: {cleanup_summary.get('backup_created', False)}")
                    
                    if "backup" in data["data"]:
                        backup_info = data["data"]["backup"]
                        print(f"   💾 备份位置: {backup_info.get('location', 'N/A')}")
                    
                    print(f"   ⏱️  处理时间: {data['meta'].get('execution_time', 'N/A')}ms")
                    
                    self.test_results.append({
                        "test": "delete_route",
                        "status": "PASS",
                        "message": "路由删除成功，安全检查和强制删除都正常工作"
                    })
                else:
                    print(f"❌ 强制删除失败: {response2.status_code}")
                    self.test_results.append({
                        "test": "delete_route",
                        "status": "FAIL",
                        "message": f"强制删除失败，状态码: {response2.status_code}"
                    })
                    
            elif response.status_code == 200:
                # 直接删除成功
                data = self.validate_standard_response(response, 200) 
                print(f"✅ 路由删除成功")
                self.test_results.append({
                    "test": "delete_route",
                    "status": "PASS",
                    "message": "路由删除成功"
                })
            else:
                error_data = response.json()
                print(f"❌ 路由删除失败")
                print(f"   错误信息: {error_data.get('message', 'Unknown error')}")
                self.test_results.append({
                    "test": "delete_route",
                    "status": "FAIL",
                    "message": f"状态码: {response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            self.test_results.append({
                "test": "delete_route",
                "status": "ERROR",
                "message": str(e)
            })

    def cleanup_test_routes(self):
        """清理测试创建的路由"""
        print("\n🧹 清理测试数据...")
        
        for route_id in self.created_routes:
            try:
                response = requests.delete(
                    f"{self.base_url}/api/routes/{route_id}",
                    params={"force": "true"},
                    headers=self.headers
                )
                if response.status_code == 200:
                    print(f"   ✅ 已清理路由: {route_id}")
                else:
                    print(f"   ⚠️ 清理路由失败: {route_id}")
            except Exception as e:
                print(f"   ❌ 清理路由异常: {route_id} - {e}")

    def print_test_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 80)
        print("🎯 API路由管理模块测试报告")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        error_tests = len([t for t in self.test_results if t["status"] == "ERROR"])
        
        print(f"📊 测试统计:")
        print(f"   总测试数: {total_tests}")
        print(f"   通过数: {passed_tests} ✅")
        print(f"   失败数: {failed_tests} ❌")
        print(f"   异常数: {error_tests} ⚠️")
        print(f"   成功率: {passed_tests/total_tests*100:.1f}%")
        
        print(f"\n📋 详细结果:")
        for i, result in enumerate(self.test_results, 1):
            status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️"}[result["status"]]
            print(f"   {i:2d}. {result['test']}: {status_icon} {result['status']}")
            if result["status"] != "PASS":
                print(f"       {result['message']}")
        
        # 总体评估
        if passed_tests == total_tests:
            print(f"\n🎉 恭喜！所有测试都已通过，API路由管理模块完全符合新文档要求！")
        elif passed_tests >= total_tests * 0.8:
            print(f"\n👍 大部分测试通过，API路由管理模块基本符合新文档要求，请修复剩余问题。")
        else:
            print(f"\n⚠️  多个测试失败，API路由管理模块需要进一步调整以符合新文档要求。")

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行API路由管理模块完整测试")
        print("符合新API文档要求，测试所有功能和响应格式")
        print("=" * 80)
        
        # 获取认证
        self.token = self.get_auth_token()
        print(f"🔑 认证成功，开始测试...")
        
        # 执行测试序列
        route_id = self.test_register_route()
        self.test_route_conflict()
        
        self.test_get_routes_list()
        self.test_advanced_filtering()
        
        self.test_get_route_detail(route_id)
        self.test_update_route(route_id)
        self.test_activate_route(route_id)
        self.test_deactivate_route(route_id)
        self.test_get_route_status(route_id)
        self.test_check_routes_health()
        self.test_delete_route(route_id)
        
        # 清理和总结
        self.cleanup_test_routes()
        self.print_test_summary()


def main():
    """主函数"""
    print("🎯 API路由管理模块完整测试程序")
    print("=" * 80)
    
    tester = APIRouteManagementTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main() 