"""
第七部分 - API路由管理模块测试
验证所有8个API端点功能
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


def test_api_route_management():
    """测试API路由管理功能"""
    print("🚀 开始运行API路由管理模块测试...")
    print("=" * 60)
    
    # 获取token
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_results = []
    route_id = None
    
    # 1. 测试动态注册新的API路由
    print("\n1️⃣ 测试动态注册新的API路由 (POST /api/routes/register)")
    print("-" * 50)
    
    route_data = {
        "api_id": "test_product_api",
        "name": "测试商品API",
        "endpoint": "/api/test/products",
        "method": "GET",
        "description": "获取商品列表的测试API",
        "auth_required": True,
        "handler": {
            "type": "entity_crud",
            "config": {
                "entity": "product",
                "operation": "list",
                "default_limit": 20,
                "max_limit": 100
            }
        },
        "parameters": [
            {
                "name": "page",
                "type": "integer",
                "location": "query",
                "required": False,
                "description": "页码，默认为1"
            },
            {
                "name": "limit",
                "type": "integer",
                "location": "query",
                "required": False,
                "description": "每页数量，默认为20"
            }
        ],
        "responses": {
            "200": {
                "description": "成功返回商品列表",
                "schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer"},
                        "message": {"type": "string"},
                        "data": {"type": "object"}
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
            route_id = data["data"]["route"]["id"]
            print(f"✅ 注册成功，路由ID: {route_id}")
            test_results.append(True)
        else:
            print(f"❌ 注册失败: {response.status_code} - {response.text}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 注册异常: {e}")
        test_results.append(False)
    
    # 2. 测试获取当前已注册的所有API路由
    print("\n2️⃣ 测试获取当前已注册的所有API路由 (GET /api/routes)")
    print("-" * 50)
    
    try:
        response = requests.get("http://localhost:5000/api/routes?page=1&limit=10", 
                              headers=headers)
        if response.status_code == 200:
            data = response.json()
            routes_count = len(data["data"]["routes"])
            total = data["data"]["pagination"]["total"]
            print(f"✅ 获取成功，当前页路由数: {routes_count}，总数: {total}")
            test_results.append(True)
        else:
            print(f"❌ 获取失败: {response.status_code} - {response.text}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 获取异常: {e}")
        test_results.append(False)
    
    # 3. 测试获取API路由详情
    print("\n3️⃣ 测试获取API路由详情 (GET /api/routes/{route_id})")
    print("-" * 50)
    
    if route_id:
        try:
            response = requests.get(f"http://localhost:5000/api/routes/{route_id}", 
                                  headers=headers)
            if response.status_code == 200:
                data = response.json()
                route_name = data["data"]["route"]["name"]
                print(f"✅ 获取成功，路由名称: {route_name}")
                test_results.append(True)
            else:
                print(f"❌ 获取失败: {response.status_code} - {response.text}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 获取异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有路由ID，跳过测试")
        test_results.append(False)
    
    # 4. 测试更新已注册的API路由
    print("\n4️⃣ 测试更新已注册的API路由 (PUT /api/routes/{route_id})")
    print("-" * 50)
    
    if route_id:
        update_data = {
            "name": "更新后的测试商品API",
            "description": "更新后的商品列表API描述"
        }
        
        try:
            response = requests.put(f"http://localhost:5000/api/routes/{route_id}", 
                                  headers=headers, json=update_data)
            if response.status_code == 200:
                data = response.json()
                updated_name = data["data"]["route"]["name"]
                print(f"✅ 更新成功，新名称: {updated_name}")
                test_results.append(True)
            else:
                print(f"❌ 更新失败: {response.status_code} - {response.text}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 更新异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有路由ID，跳过测试")
        test_results.append(False)
    
    # 5. 测试激活API路由
    print("\n5️⃣ 测试激活API路由 (POST /api/routes/{route_id}/activate)")
    print("-" * 50)
    
    if route_id:
        try:
            response = requests.post(f"http://localhost:5000/api/routes/{route_id}/activate", 
                                   headers=headers)
            if response.status_code == 200:
                data = response.json()
                status = data["data"]["route"]["status"]
                print(f"✅ 激活成功，状态: {status}")
                test_results.append(True)
            else:
                print(f"❌ 激活失败: {response.status_code} - {response.text}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 激活异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有路由ID，跳过测试")
        test_results.append(False)
    
    # 6. 测试停用API路由
    print("\n6️⃣ 测试停用API路由 (POST /api/routes/{route_id}/deactivate)")
    print("-" * 50)
    
    if route_id:
        try:
            response = requests.post(f"http://localhost:5000/api/routes/{route_id}/deactivate", 
                                   headers=headers)
            if response.status_code == 200:
                data = response.json()
                status = data["data"]["route"]["status"]
                print(f"✅ 停用成功，状态: {status}")
                test_results.append(True)
            else:
                print(f"❌ 停用失败: {response.status_code} - {response.text}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 停用异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有路由ID，跳过测试")
        test_results.append(False)
    
    # 7. 测试获取API路由状态
    print("\n7️⃣ 测试获取API路由状态 (GET /api/routes/{route_id}/status)")
    print("-" * 50)
    
    if route_id:
        try:
            response = requests.get(f"http://localhost:5000/api/routes/{route_id}/status", 
                                  headers=headers)
            if response.status_code == 200:
                data = response.json()
                status = data["data"]["route"]["status"]
                call_count = data["data"]["statistics"]["total_calls"]
                print(f"✅ 获取成功，状态: {status}，调用次数: {call_count}")
                test_results.append(True)
            else:
                print(f"❌ 获取失败: {response.status_code} - {response.text}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 获取异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有路由ID，跳过测试")
        test_results.append(False)
    
    # 8. 测试检查所有API路由健康状态
    print("\n8️⃣ 测试检查所有API路由健康状态 (GET /api/routes/health)")
    print("-" * 50)

    try:
        response = requests.get("http://localhost:5000/api/routes/health",
                              headers=headers)
        if response.status_code == 200:
            data = response.json()
            total_routes = data["data"]["total_routes"]
            healthy_routes = data["data"]["healthy_routes"]
            print(f"✅ 检查成功，总路由: {total_routes}，健康路由: {healthy_routes}")
            test_results.append(True)
        else:
            print(f"❌ 检查失败: {response.status_code} - {response.text}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 检查异常: {e}")
        test_results.append(False)
    
    # 清理：删除测试路由
    if route_id:
        print("\n🧹 清理测试数据...")
        try:
            response = requests.delete(f"http://localhost:5000/api/routes/{route_id}", 
                                     headers=headers)
            if response.status_code == 200:
                print("✅ 测试路由删除成功")
            else:
                print(f"⚠️ 测试路由删除失败: {response.status_code}")
        except Exception as e:
            print(f"⚠️ 删除测试路由异常: {e}")
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 60)
    print("📊 第七部分API路由管理模块测试结果")
    print("-" * 60)
    print(f"总API端点: {total}")
    print(f"测试通过: {passed}")
    print(f"测试失败: {total - passed}")
    print(f"成功率: {(passed / total * 100):.1f}%")
    
    if passed == total:
        print("🎉 所有8个API端点测试全部通过！")
    else:
        print(f"⚠️  有 {total - passed} 个API端点测试失败")
    
    return passed == total


if __name__ == "__main__":
    success = test_api_route_management()
    exit(0 if success else 1)
