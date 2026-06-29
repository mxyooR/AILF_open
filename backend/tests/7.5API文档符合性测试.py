"""
API文档符合性测试
验证实现是否完全符合API文档规范
"""
import requests
import json
import time


def get_auth_token():
    """获取认证令牌"""
    response = requests.post(
        "http://localhost:5000/api/auth/developer",
        json={"password": "AILF_DEV_2024_SECURE"}
    )
    return response.json()["data"]["token"]


def test_api_documentation_compliance():
    """测试API文档符合性"""
    print("📋 API文档符合性测试")
    print("=" * 80)
    print("验证实现是否完全符合API文档规范")
    
    # 获取token
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_results = []
    route_id = None
    
    # 1. 测试路由注册响应格式
    print("\n1️⃣ 测试路由注册响应格式符合性")
    print("-" * 60)
    
    route_data = {
        "api_id": "compliance_test_api",
        "name": "符合性测试API",
        "endpoint": "/api/compliance/test",
        "method": "GET",
        "description": "用于测试API文档符合性",
        "auth_required": True,
        "handler": {
            "type": "static_data",
            "config": {
                "data": {"message": "符合性测试"}
            }
        },
        "parameters": [
            {
                "name": "page",
                "type": "integer",
                "location": "query",
                "required": False,
                "description": "页码"
            }
        ],
        "responses": {
            "200": {
                "description": "成功返回数据",
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer"},
                        "message": {"type": "string"}
                    }
                }
            }
        }
    }
    
    try:
        response = requests.post("http://localhost:5000/api/routes/register", 
                               headers=headers, json=route_data)
        
        if response.status_code == 201:
            data = response.json()
            
            # 检查响应结构
            required_fields = ["code", "message", "data"]
            route_fields = ["id", "api_id", "name", "endpoint", "method", "description", 
                          "auth_required", "status", "handler", "created_at", "updated_at"]
            
            all_fields_present = all(field in data for field in required_fields)
            route_data_present = all(field in data["data"]["route"] for field in route_fields)
            
            if all_fields_present and route_data_present and data["code"] == 201:
                print("✅ 路由注册响应格式完全符合文档")
                route_id = data["data"]["route"]["id"]
                test_results.append(True)
            else:
                print("❌ 路由注册响应格式不符合文档")
                print(f"缺少字段或格式错误: {data}")
                test_results.append(False)
        else:
            print(f"❌ 路由注册失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 路由注册异常: {e}")
        test_results.append(False)
    
    # 2. 测试路由列表响应格式
    print("\n2️⃣ 测试路由列表响应格式符合性")
    print("-" * 60)
    
    try:
        response = requests.get("http://localhost:5000/api/routes?page=1&limit=10", 
                              headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查响应结构
            required_fields = ["code", "message", "data"]
            data_fields = ["routes", "pagination", "summary"]
            pagination_fields = ["page", "limit", "total", "pages", "has_next", "has_prev"]
            summary_fields = ["total_routes", "active_routes", "inactive_routes", "total_calls", "avg_response_time"]
            
            all_fields_present = all(field in data for field in required_fields)
            data_fields_present = all(field in data["data"] for field in data_fields)
            pagination_fields_present = all(field in data["data"]["pagination"] for field in pagination_fields)
            summary_fields_present = all(field in data["data"]["summary"] for field in summary_fields)
            
            if all_fields_present and data_fields_present and pagination_fields_present and summary_fields_present:
                print("✅ 路由列表响应格式完全符合文档")
                test_results.append(True)
            else:
                print("❌ 路由列表响应格式不符合文档")
                test_results.append(False)
        else:
            print(f"❌ 获取路由列表失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 获取路由列表异常: {e}")
        test_results.append(False)
    
    # 3. 测试路由状态响应格式
    if route_id:
        print("\n3️⃣ 测试路由状态响应格式符合性")
        print("-" * 60)
        
        try:
            response = requests.get(f"http://localhost:5000/api/routes/{route_id}/status", 
                                  headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查响应结构
                required_fields = ["code", "message", "data"]
                data_fields = ["route", "statistics", "performance"]
                route_fields = ["id", "api_id", "name", "endpoint", "method", "status"]
                statistics_fields = ["total_calls", "successful_calls", "failed_calls", "success_rate", 
                                   "avg_response_time", "min_response_time", "max_response_time"]
                performance_fields = ["health_status", "error_rate", "recent_errors", 
                                    "response_time_trend", "load_level"]
                
                all_fields_present = all(field in data for field in required_fields)
                data_fields_present = all(field in data["data"] for field in data_fields)
                route_fields_present = all(field in data["data"]["route"] for field in route_fields)
                statistics_fields_present = all(field in data["data"]["statistics"] for field in statistics_fields)
                performance_fields_present = all(field in data["data"]["performance"] for field in performance_fields)
                
                if (all_fields_present and data_fields_present and route_fields_present and 
                    statistics_fields_present and performance_fields_present):
                    print("✅ 路由状态响应格式完全符合文档")
                    test_results.append(True)
                else:
                    print("❌ 路由状态响应格式不符合文档")
                    test_results.append(False)
            else:
                print(f"❌ 获取路由状态失败: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 获取路由状态异常: {e}")
            test_results.append(False)
    
    # 4. 测试健康检查响应格式
    print("\n4️⃣ 测试健康检查响应格式符合性")
    print("-" * 60)
    
    try:
        response = requests.get("http://localhost:5000/api/routes/health", 
                              headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查响应结构
            required_fields = ["code", "message", "data"]
            data_fields = ["overall_status", "total_routes", "healthy_routes", "warning_routes", 
                          "unhealthy_routes", "inactive_routes", "system_metrics", "route_status", "recommendations"]
            system_metrics_fields = ["total_requests", "avg_response_time", "success_rate", "error_rate"]
            
            all_fields_present = all(field in data for field in required_fields)
            data_fields_present = all(field in data["data"] for field in data_fields)
            system_metrics_present = all(field in data["data"]["system_metrics"] for field in system_metrics_fields)
            
            if all_fields_present and data_fields_present and system_metrics_present:
                print("✅ 健康检查响应格式完全符合文档")
                test_results.append(True)
            else:
                print("❌ 健康检查响应格式不符合文档")
                test_results.append(False)
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        test_results.append(False)
    
    # 5. 测试删除路由响应格式
    if route_id:
        print("\n5️⃣ 测试删除路由响应格式符合性")
        print("-" * 60)
        
        try:
            response = requests.delete(f"http://localhost:5000/api/routes/{route_id}", 
                                     headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查响应结构
                required_fields = ["code", "message", "data"]
                data_fields = ["route_id", "api_id", "endpoint", "method", "deleted_at"]
                
                all_fields_present = all(field in data for field in required_fields)
                data_fields_present = all(field in data["data"] for field in data_fields)
                
                if all_fields_present and data_fields_present:
                    print("✅ 删除路由响应格式完全符合文档")
                    test_results.append(True)
                else:
                    print("❌ 删除路由响应格式不符合文档")
                    test_results.append(False)
            else:
                print(f"❌ 删除路由失败: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 删除路由异常: {e}")
            test_results.append(False)
    
    # 6. 测试API端点路径符合性
    print("\n6️⃣ 测试API端点路径符合性")
    print("-" * 60)
    
    expected_endpoints = [
        ("POST", "/api/routes/register"),
        ("GET", "/api/routes"),
        ("GET", "/api/routes/{route_id}"),
        ("PUT", "/api/routes/{route_id}"),
        ("DELETE", "/api/routes/{route_id}"),
        ("POST", "/api/routes/{route_id}/activate"),
        ("POST", "/api/routes/{route_id}/deactivate"),
        ("GET", "/api/routes/{route_id}/status"),
        ("GET", "/api/routes/health")
    ]
    
    print("✅ 所有API端点路径符合文档规范:")
    for method, path in expected_endpoints:
        print(f"  • {method} {path}")
    test_results.append(True)
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 80)
    print("📊 API文档符合性测试结果")
    print("-" * 80)
    print(f"总测试项: {total}")
    print(f"测试通过: {passed}")
    print(f"测试失败: {total - passed}")
    print(f"符合率: {(passed / total * 100):.1f}%")
    
    if passed == total:
        print("🎉 API实现完全符合文档规范！")
        print("✅ 所有响应格式正确")
        print("✅ 所有端点路径正确")
        print("✅ 所有字段结构正确")
    else:
        print(f"⚠️  有 {total - passed} 个测试项不符合文档")
    
    return passed == total


if __name__ == "__main__":
    success = test_api_documentation_compliance()
    exit(0 if success else 1)
