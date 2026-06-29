"""
API路由管理模块完整测试
严格按照API文档进行全面测试
"""
import requests
import json
import time
import sys
import subprocess
import threading
from datetime import datetime


class APIRouteCompleteTest:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.token = None
        self.headers = {}
        self.test_results = []
        self.server_process = None
        
    def start_server(self):
        """启动后端服务器"""
        print("🚀 启动后端服务器...")
        try:
            import os
            import sys

            # 切换到backend目录
            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            os.chdir(backend_dir)

            # 启动服务器进程
            self.server_process = subprocess.Popen(
                [sys.executable, "-m", "app.main"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )

            # 等待服务器启动
            print("⏳ 等待服务器启动...")
            max_attempts = 20
            for attempt in range(max_attempts):
                time.sleep(2)
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=3)
                    if response.status_code == 200:
                        print("✅ 服务器启动成功")
                        return True
                except requests.exceptions.RequestException:
                    if attempt < max_attempts - 1:
                        print(f"⏳ 尝试连接服务器... ({attempt + 1}/{max_attempts})")
                    continue

            print("❌ 服务器启动超时")
            return False

        except Exception as e:
            print(f"❌ 启动服务器失败: {e}")
            return False
    
    def stop_server(self):
        """停止后端服务器"""
        if self.server_process:
            print("🛑 停止后端服务器...")
            self.server_process.terminate()
            self.server_process.wait()
            print("✅ 服务器已停止")
    
    def get_auth_token(self):
        """获取认证令牌"""
        print("🔐 获取认证令牌...")
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/developer",
                json={"password": "AILF_DEV_2024_SECURE"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["data"]["token"]
                self.headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
                print("✅ 认证令牌获取成功")
                return True
            else:
                print(f"❌ 认证失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 获取认证令牌失败: {e}")
            return False
    
    def test_register_route(self):
        """测试动态注册新的API路由"""
        print("\n1️⃣ 测试动态注册新的API路由")
        print("=" * 60)
        
        # 构建符合API文档的请求数据
        route_data = {
            "api_id": "product_create_api_test",
            "name": "商品创建API测试",
            "endpoint": "/api/products/test",
            "method": "POST",
            "description": "创建新的商品记录，支持商品基本信息和分类",
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
                    }
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
                }
            ],
            "responses": {
                "201": {
                    "description": "商品创建成功",
                    "response_schema": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "integer", "example": 201},
                            "message": {"type": "string", "example": "商品创建成功"}
                        }
                    }
                }
            },
            "form_config": {
                "auto_generate": True,
                "layout": {
                    "type": "grid",
                    "columns": 2
                }
            }
        }
        
        try:
            print("📤 发送路由注册请求...")
            response = requests.post(
                f"{self.base_url}/api/routes/register",
                json=route_data,
                headers=self.headers,
                timeout=30
            )
            
            print(f"📥 响应状态码: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                print("✅ 路由注册成功")
                print(f"📊 响应数据结构验证:")
                
                # 验证响应格式符合API文档
                required_fields = ["code", "message", "data", "meta"]
                for field in required_fields:
                    if field in data:
                        print(f"  ✅ {field}: 存在")
                    else:
                        print(f"  ❌ {field}: 缺失")
                
                # 验证data字段结构
                if "data" in data and "route" in data["data"]:
                    route = data["data"]["route"]
                    route_fields = ["id", "api_id", "name", "endpoint", "method", "status"]
                    for field in route_fields:
                        if field in route:
                            print(f"  ✅ route.{field}: {route[field]}")
                        else:
                            print(f"  ❌ route.{field}: 缺失")
                    
                    # 保存路由ID用于后续测试
                    self.route_id = route.get("id")
                
                self.test_results.append(("路由注册", True, "成功"))
                return True
                
            else:
                print(f"❌ 路由注册失败")
                print(f"响应内容: {response.text}")
                self.test_results.append(("路由注册", False, f"状态码: {response.status_code}"))
                return False
                
        except Exception as e:
            print(f"❌ 路由注册异常: {e}")
            self.test_results.append(("路由注册", False, str(e)))
            return False
    
    def test_get_routes_list(self):
        """测试获取API路由列表"""
        print("\n2️⃣ 测试获取API路由列表")
        print("=" * 60)
        
        try:
            # 测试基础查询
            print("📤 发送路由列表查询请求...")
            response = requests.get(
                f"{self.base_url}/api/routes",
                headers=self.headers,
                timeout=30
            )
            
            print(f"📥 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 路由列表获取成功")
                
                # 验证响应格式
                if "data" in data and "routes" in data["data"]:
                    routes = data["data"]["routes"]
                    print(f"📊 找到 {len(routes)} 个路由")
                    
                    if len(routes) > 0:
                        route = routes[0]
                        route_fields = ["id", "api_id", "name", "endpoint", "method", "status"]
                        for field in route_fields:
                            if field in route:
                                print(f"  ✅ route.{field}: 存在")
                            else:
                                print(f"  ❌ route.{field}: 缺失")
                
                # 测试带参数的查询
                print("\n📤 测试带参数的查询...")
                params = {
                    "status": "active",
                    "method": "POST",
                    "page": 1,
                    "limit": 10,
                    "include_stats": True
                }
                
                response = requests.get(
                    f"{self.base_url}/api/routes",
                    params=params,
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    print("✅ 带参数查询成功")
                    self.test_results.append(("路由列表查询", True, "成功"))
                    return True
                else:
                    print(f"❌ 带参数查询失败: {response.status_code}")
                    
            else:
                print(f"❌ 路由列表获取失败")
                print(f"响应内容: {response.text}")
                
            self.test_results.append(("路由列表查询", False, f"状态码: {response.status_code}"))
            return False
            
        except Exception as e:
            print(f"❌ 路由列表查询异常: {e}")
            self.test_results.append(("路由列表查询", False, str(e)))
            return False
    
    def test_get_route_detail(self):
        """测试获取路由详情"""
        print("\n3️⃣ 测试获取路由详情")
        print("=" * 60)

        if not hasattr(self, 'route_id') or not self.route_id:
            print("❌ 没有可用的路由ID，跳过测试")
            self.test_results.append(("路由详情查询", False, "缺少路由ID"))
            return False

        try:
            print(f"📤 查询路由详情: {self.route_id}")
            response = requests.get(
                f"{self.base_url}/api/routes/{self.route_id}",
                headers=self.headers,
                timeout=30
            )

            print(f"📥 响应状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("✅ 路由详情获取成功")

                # 验证响应格式
                if "data" in data:
                    route_data = data["data"]
                    detail_fields = ["id", "api_id", "name", "endpoint", "method", "handler"]
                    for field in detail_fields:
                        if field in route_data:
                            print(f"  ✅ {field}: 存在")
                        else:
                            print(f"  ❌ {field}: 缺失")

                self.test_results.append(("路由详情查询", True, "成功"))
                return True
            else:
                print(f"❌ 路由详情获取失败")
                print(f"响应内容: {response.text}")
                self.test_results.append(("路由详情查询", False, f"状态码: {response.status_code}"))
                return False

        except Exception as e:
            print(f"❌ 路由详情查询异常: {e}")
            self.test_results.append(("路由详情查询", False, str(e)))
            return False

    def test_update_route(self):
        """测试更新路由"""
        print("\n4️⃣ 测试更新路由")
        print("=" * 60)

        if not hasattr(self, 'route_id') or not self.route_id:
            print("❌ 没有可用的路由ID，跳过测试")
            self.test_results.append(("路由更新", False, "缺少路由ID"))
            return False

        update_data = {
            "name": "商品创建API测试（更新版）",
            "description": "创建新的商品记录，支持批量导入和自动分类",
            "handler": {
                "config": {
                    "entity": "product",
                    "operation": "create",
                    "allowed_fields": ["name", "price", "description", "category_id", "tags"],
                    "auto_categorize": True,
                    "batch_import": True
                }
            }
        }

        try:
            print(f"📤 更新路由: {self.route_id}")
            response = requests.put(
                f"{self.base_url}/api/routes/{self.route_id}",
                json=update_data,
                headers=self.headers,
                timeout=30
            )

            print(f"📥 响应状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("✅ 路由更新成功")

                # 验证更新结果
                if "data" in data and "route" in data["data"]:
                    route = data["data"]["route"]
                    if route.get("name") == update_data["name"]:
                        print("  ✅ 名称更新成功")
                    else:
                        print("  ❌ 名称更新失败")

                self.test_results.append(("路由更新", True, "成功"))
                return True
            else:
                print(f"❌ 路由更新失败")
                print(f"响应内容: {response.text}")
                self.test_results.append(("路由更新", False, f"状态码: {response.status_code}"))
                return False

        except Exception as e:
            print(f"❌ 路由更新异常: {e}")
            self.test_results.append(("路由更新", False, str(e)))
            return False

    def test_route_status_operations(self):
        """测试路由状态操作（激活/停用）"""
        print("\n5️⃣ 测试路由状态操作")
        print("=" * 60)

        if not hasattr(self, 'route_id') or not self.route_id:
            print("❌ 没有可用的路由ID，跳过测试")
            self.test_results.append(("路由状态操作", False, "缺少路由ID"))
            return False

        try:
            # 测试停用路由
            print("📤 停用路由...")
            response = requests.post(
                f"{self.base_url}/api/routes/{self.route_id}/deactivate",
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                print("✅ 路由停用成功")
            else:
                print(f"❌ 路由停用失败: {response.status_code}")

            # 测试激活路由
            print("📤 激活路由...")
            response = requests.post(
                f"{self.base_url}/api/routes/{self.route_id}/activate",
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                print("✅ 路由激活成功")
                self.test_results.append(("路由状态操作", True, "成功"))
                return True
            else:
                print(f"❌ 路由激活失败: {response.status_code}")
                self.test_results.append(("路由状态操作", False, f"激活失败: {response.status_code}"))
                return False

        except Exception as e:
            print(f"❌ 路由状态操作异常: {e}")
            self.test_results.append(("路由状态操作", False, str(e)))
            return False

    def test_route_health_check(self):
        """测试路由健康检查"""
        print("\n6️⃣ 测试路由健康检查")
        print("=" * 60)

        try:
            # 测试所有路由健康检查
            print("📤 检查所有路由健康状态...")
            response = requests.get(
                f"{self.base_url}/api/routes/health",
                headers=self.headers,
                timeout=30
            )

            print(f"📥 响应状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("✅ 路由健康检查成功")

                # 验证响应格式
                if "data" in data:
                    health_data = data["data"]
                    health_fields = ["overall_status", "summary", "system_metrics"]
                    for field in health_fields:
                        if field in health_data:
                            print(f"  ✅ {field}: 存在")
                        else:
                            print(f"  ❌ {field}: 缺失")

                self.test_results.append(("路由健康检查", True, "成功"))
                return True
            else:
                print(f"❌ 路由健康检查失败")
                print(f"响应内容: {response.text}")
                self.test_results.append(("路由健康检查", False, f"状态码: {response.status_code}"))
                return False

        except Exception as e:
            print(f"❌ 路由健康检查异常: {e}")
            self.test_results.append(("路由健康检查", False, str(e)))
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 API路由管理模块完整测试")
        print("=" * 80)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # 启动服务器
        if not self.start_server():
            print("❌ 服务器启动失败，测试终止")
            return False

        try:
            # 获取认证令牌
            if not self.get_auth_token():
                print("❌ 认证失败，测试终止")
                return False

            # 运行测试
            self.test_register_route()
            self.test_get_routes_list()
            self.test_get_route_detail()
            self.test_update_route()
            self.test_route_status_operations()
            self.test_route_health_check()

            # 输出测试结果
            self.print_test_summary()

        finally:
            # 停止服务器
            self.stop_server()

        return True
    
    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 80)
        print("📊 测试结果总结")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, passed, _ in self.test_results if passed)
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        print("\n详细结果:")
        for test_name, passed, message in self.test_results:
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"  {status} {test_name}: {message}")


if __name__ == "__main__":
    test = APIRouteCompleteTest()
    test.run_all_tests()
