"""
API路由管理模块完全符合性测试
严格按照API文档验证所有响应格式和字段
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List


class APIComplianceTest:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.token = None
        self.headers = {}
        self.test_results = []
        self.route_id = None
        
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
                return False
                
        except Exception as e:
            print(f"❌ 获取认证令牌失败: {e}")
            return False
    
    def validate_standard_response(self, response_data: Dict[str, Any], test_name: str) -> bool:
        """验证标准响应格式"""
        print(f"🔍 验证 {test_name} 的响应格式...")
        
        # 验证顶级字段
        required_fields = ["code", "message", "data", "meta"]
        for field in required_fields:
            if field not in response_data:
                print(f"  ❌ 缺少必需字段: {field}")
                return False
            print(f"  ✅ {field}: 存在")
        
        # 验证meta字段结构
        meta = response_data.get("meta", {})
        meta_fields = ["timestamp", "request_id", "execution_time", "api_version"]
        for field in meta_fields:
            if field not in meta:
                print(f"  ❌ meta缺少字段: {field}")
                return False
            print(f"  ✅ meta.{field}: {meta[field]}")
        
        # 验证时间戳格式
        timestamp = meta.get("timestamp", "")
        if not timestamp.endswith("Z") or "T" not in timestamp:
            print(f"  ❌ 时间戳格式不正确: {timestamp}")
            return False
        print(f"  ✅ 时间戳格式正确: {timestamp}")
        
        # 验证API版本
        api_version = meta.get("api_version", "")
        if api_version != "1.0.0":
            print(f"  ❌ API版本不正确: {api_version}")
            return False
        print(f"  ✅ API版本正确: {api_version}")
        
        return True
    
    def test_route_registration_compliance(self):
        """测试路由注册的完全符合性"""
        print("\n1️⃣ 测试路由注册API完全符合性")
        print("=" * 80)
        
        # 构建完全符合API文档的请求数据
        route_data = {
            "api_id": f"compliance_test_api_{int(time.time())}",
            "name": "符合性测试API",
            "endpoint": f"/api/compliance/test/{int(time.time())}",
            "method": "POST",
            "description": "用于测试API文档符合性的测试API",
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
                },
                {
                    "name": "category_id",
                    "type": "integer",
                    "location": "body",
                    "required": True,
                    "description": "商品分类ID"
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
                                            "price": {"type": "number"},
                                            "description": {"type": "string"},
                                            "category": {"type": "object"},
                                            "created_at": {"type": "string", "format": "datetime"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "400": {
                    "description": "请求参数验证失败",
                    "response_schema": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "integer", "example": 400},
                            "message": {"type": "string", "example": "参数验证失败"},
                            "data": {
                                "type": "object",
                                "properties": {
                                    "error_type": {"type": "string"},
                                    "details": {"type": "object"}
                                }
                            }
                        }
                    }
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
                        "fields": ["name", "category_id"]
                    },
                    {
                        "title": "详细信息",
                        "fields": ["price", "description"]
                    }
                ]
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
            
            if response.status_code != 201:
                print(f"❌ 状态码不符合文档要求，期望201，实际{response.status_code}")
                print(f"响应内容: {response.text}")
                self.test_results.append(("路由注册符合性", False, f"状态码错误: {response.status_code}"))
                return False
            
            data = response.json()
            
            # 验证标准响应格式
            if not self.validate_standard_response(data, "路由注册"):
                self.test_results.append(("路由注册符合性", False, "响应格式不符合标准"))
                return False
            
            # 验证路由注册特定的响应结构
            print("🔍 验证路由注册特定响应结构...")
            
            # 验证data.route字段
            if "route" not in data["data"]:
                print("  ❌ 缺少data.route字段")
                self.test_results.append(("路由注册符合性", False, "缺少route字段"))
                return False
            
            route = data["data"]["route"]
            route_required_fields = [
                "id", "api_id", "name", "endpoint", "method", 
                "description", "auth_required", "status", "handler",
                "access_url", "created_at", "updated_at"
            ]
            
            for field in route_required_fields:
                if field not in route:
                    print(f"  ❌ route缺少字段: {field}")
                    self.test_results.append(("路由注册符合性", False, f"route缺少字段: {field}"))
                    return False
                print(f"  ✅ route.{field}: 存在")
            
            # 保存路由ID用于后续测试
            self.route_id = route["id"]
            
            # 验证handler结构
            handler = route.get("handler", {})
            if "type" not in handler or "config" not in handler:
                print("  ❌ handler结构不完整")
                self.test_results.append(("路由注册符合性", False, "handler结构不完整"))
                return False
            
            # 验证时间格式
            created_at = route.get("created_at", "")
            if not created_at.endswith("Z") or "T" not in created_at:
                print(f"  ❌ created_at时间格式不正确: {created_at}")
                self.test_results.append(("路由注册符合性", False, "时间格式不正确"))
                return False
            
            print("✅ 路由注册完全符合API文档要求")
            self.test_results.append(("路由注册符合性", True, "完全符合"))
            return True
            
        except Exception as e:
            print(f"❌ 路由注册测试异常: {e}")
            self.test_results.append(("路由注册符合性", False, str(e)))
            return False
    
    def run_all_compliance_tests(self):
        """运行所有符合性测试"""
        print("🧪 API路由管理模块完全符合性测试")
        print("=" * 100)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        
        # 检查服务器状态
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code != 200:
                print("❌ 服务器不可用，测试终止")
                return False
            print("✅ 服务器运行正常")
        except Exception as e:
            print(f"❌ 服务器连接失败: {e}")
            return False
        
        # 获取认证令牌
        if not self.get_auth_token():
            print("❌ 认证失败，测试终止")
            return False
        
        # 运行符合性测试
        self.test_route_registration_compliance()
        self.test_route_list_compliance()
        self.test_health_check_compliance()

        # 输出测试结果
        self.print_compliance_summary()

        return True

    def test_route_list_compliance(self):
        """测试路由列表API的完全符合性"""
        print("\n2️⃣ 测试路由列表API完全符合性")
        print("=" * 80)

        try:
            print("📤 发送路由列表查询请求...")
            response = requests.get(
                f"{self.base_url}/api/routes",
                headers=self.headers,
                timeout=30
            )

            print(f"📥 响应状态码: {response.status_code}")

            if response.status_code != 200:
                print(f"❌ 状态码不符合文档要求，期望200，实际{response.status_code}")
                self.test_results.append(("路由列表符合性", False, f"状态码错误: {response.status_code}"))
                return False

            data = response.json()

            # 验证标准响应格式
            if not self.validate_standard_response(data, "路由列表"):
                self.test_results.append(("路由列表符合性", False, "响应格式不符合标准"))
                return False

            # 验证路由列表特定的响应结构
            print("🔍 验证路由列表特定响应结构...")

            # 验证data字段结构
            data_obj = data.get("data", {})
            required_data_fields = ["routes", "pagination", "summary", "filters_applied"]

            for field in required_data_fields:
                if field not in data_obj:
                    print(f"  ❌ data缺少字段: {field}")
                    self.test_results.append(("路由列表符合性", False, f"data缺少字段: {field}"))
                    return False
                print(f"  ✅ data.{field}: 存在")

            # 验证routes数组结构
            routes = data_obj.get("routes", [])
            if not isinstance(routes, list):
                print("  ❌ routes不是数组类型")
                self.test_results.append(("路由列表符合性", False, "routes不是数组"))
                return False

            if len(routes) > 0:
                route = routes[0]
                route_fields = [
                    "id", "api_id", "name", "endpoint", "method",
                    "description", "auth_required", "status", "handler",
                    "access_url", "created_at", "updated_at"
                ]

                for field in route_fields:
                    if field not in route:
                        print(f"  ❌ route[0]缺少字段: {field}")
                        self.test_results.append(("路由列表符合性", False, f"route缺少字段: {field}"))
                        return False
                    print(f"  ✅ route[0].{field}: 存在")

                # 验证handler结构
                handler = route.get("handler", {})
                handler_fields = ["type", "display_name", "config"]
                for field in handler_fields:
                    if field not in handler:
                        print(f"  ❌ handler缺少字段: {field}")
                        self.test_results.append(("路由列表符合性", False, f"handler缺少字段: {field}"))
                        return False
                    print(f"  ✅ handler.{field}: 存在")

            # 验证pagination结构
            pagination = data_obj.get("pagination", {})
            pagination_fields = ["page", "limit", "total", "pages", "has_next", "has_prev"]

            for field in pagination_fields:
                if field not in pagination:
                    print(f"  ❌ pagination缺少字段: {field}")
                    self.test_results.append(("路由列表符合性", False, f"pagination缺少字段: {field}"))
                    return False
                print(f"  ✅ pagination.{field}: {pagination[field]}")

            # 验证summary结构
            summary = data_obj.get("summary", {})
            summary_fields = [
                "total_routes", "active_routes", "inactive_routes",
                "total_calls", "total_successful_calls", "overall_success_rate",
                "avg_response_time", "healthy_routes", "warning_routes", "unhealthy_routes"
            ]

            for field in summary_fields:
                if field not in summary:
                    print(f"  ❌ summary缺少字段: {field}")
                    self.test_results.append(("路由列表符合性", False, f"summary缺少字段: {field}"))
                    return False
                print(f"  ✅ summary.{field}: {summary[field]}")

            print("✅ 路由列表完全符合API文档要求")
            self.test_results.append(("路由列表符合性", True, "完全符合"))
            return True

        except Exception as e:
            print(f"❌ 路由列表测试异常: {e}")
            self.test_results.append(("路由列表符合性", False, str(e)))
            return False

    def test_health_check_compliance(self):
        """测试健康检查API的完全符合性"""
        print("\n3️⃣ 测试健康检查API完全符合性")
        print("=" * 80)

        try:
            print("📤 发送健康检查请求...")
            response = requests.get(
                f"{self.base_url}/api/routes/health?detailed=true&include_inactive=false",
                headers=self.headers,
                timeout=30
            )

            print(f"📥 响应状态码: {response.status_code}")

            if response.status_code != 200:
                print(f"❌ 状态码不符合文档要求，期望200，实际{response.status_code}")
                self.test_results.append(("健康检查符合性", False, f"状态码错误: {response.status_code}"))
                return False

            data = response.json()

            # 验证标准响应格式
            if not self.validate_standard_response(data, "健康检查"):
                self.test_results.append(("健康检查符合性", False, "响应格式不符合标准"))
                return False

            # 验证健康检查特定的响应结构
            print("🔍 验证健康检查特定响应结构...")

            # 验证data字段结构
            data_obj = data.get("data", {})
            required_data_fields = [
                "overall_status", "health_score", "summary", "system_metrics",
                "route_status", "performance_analysis", "recommendations",
                "alerts", "trends"
            ]

            for field in required_data_fields:
                if field not in data_obj:
                    print(f"  ❌ data缺少字段: {field}")
                    self.test_results.append(("健康检查符合性", False, f"data缺少字段: {field}"))
                    return False
                print(f"  ✅ data.{field}: 存在")

            # 验证overall_status值
            overall_status = data_obj.get("overall_status", "")
            valid_statuses = ["healthy", "warning", "unhealthy"]
            if overall_status not in valid_statuses:
                print(f"  ❌ overall_status值不正确: {overall_status}")
                self.test_results.append(("健康检查符合性", False, f"overall_status值错误: {overall_status}"))
                return False
            print(f"  ✅ overall_status值正确: {overall_status}")

            # 验证summary结构
            summary = data_obj.get("summary", {})
            summary_fields = [
                "total_routes", "active_routes", "inactive_routes",
                "healthy_routes", "warning_routes", "unhealthy_routes"
            ]

            for field in summary_fields:
                if field not in summary:
                    print(f"  ❌ summary缺少字段: {field}")
                    self.test_results.append(("健康检查符合性", False, f"summary缺少字段: {field}"))
                    return False
                print(f"  ✅ summary.{field}: {summary[field]}")

            # 验证system_metrics结构
            system_metrics = data_obj.get("system_metrics", {})
            metrics_fields = [
                "total_requests_24h", "successful_requests_24h", "failed_requests_24h",
                "overall_success_rate", "overall_error_rate", "avg_response_time",
                "median_response_time", "p95_response_time", "total_uptime",
                "active_connections", "requests_per_second"
            ]

            for field in metrics_fields:
                if field not in system_metrics:
                    print(f"  ❌ system_metrics缺少字段: {field}")
                    self.test_results.append(("健康检查符合性", False, f"system_metrics缺少字段: {field}"))
                    return False
                print(f"  ✅ system_metrics.{field}: {system_metrics[field]}")

            # 验证route_status数组
            route_status = data_obj.get("route_status", [])
            if not isinstance(route_status, list):
                print("  ❌ route_status不是数组类型")
                self.test_results.append(("健康检查符合性", False, "route_status不是数组"))
                return False

            if len(route_status) > 0:
                route = route_status[0]
                route_status_fields = [
                    "id", "api_id", "name", "endpoint", "method", "status",
                    "health", "health_score", "success_rate", "avg_response_time",
                    "last_check", "uptime"
                ]

                for field in route_status_fields:
                    if field not in route:
                        print(f"  ❌ route_status[0]缺少字段: {field}")
                        self.test_results.append(("健康检查符合性", False, f"route_status缺少字段: {field}"))
                        return False
                    print(f"  ✅ route_status[0].{field}: 存在")

            print("✅ 健康检查完全符合API文档要求")
            self.test_results.append(("健康检查符合性", True, "完全符合"))
            return True

        except Exception as e:
            print(f"❌ 健康检查测试异常: {e}")
            self.test_results.append(("健康检查符合性", False, str(e)))
            return False
    
    def print_compliance_summary(self):
        """打印符合性测试总结"""
        print("\n" + "=" * 100)
        print("📊 API文档符合性测试结果总结")
        print("=" * 100)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, passed, _ in self.test_results if passed)
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"符合率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        print("\n详细结果:")
        for test_name, passed, message in self.test_results:
            status = "✅ 符合" if passed else "❌ 不符合"
            print(f"  {status} {test_name}: {message}")
        
        if failed_tests == 0:
            print("\n🎉 恭喜！API完全符合文档要求！")
        else:
            print(f"\n⚠️  发现 {failed_tests} 个不符合项，需要修复")


if __name__ == "__main__":
    print("请确保后端服务器正在运行:")
    print("在backend目录下运行: python -m app.main")
    print("=" * 100)
    
    test = APIComplianceTest()
    test.run_all_compliance_tests()
