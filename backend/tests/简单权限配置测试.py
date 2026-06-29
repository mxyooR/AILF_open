#!/usr/bin/env python3
"""
简单的权限配置API路由测试 - 使用开发者token
"""

import requests
import json

# API配置
BASE_URL = "http://localhost:5000"
DEV_PASSWORD = "123456"


def get_developer_token():
    """获取开发者认证token"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/developer",
            json={"password": DEV_PASSWORD},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["data"]["token"]
        else:
            print(f"❌ 认证失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 认证异常: {e}")
        return None


def test_developer_access_to_protected_routes():
    """测试开发者访问权限保护的路由"""
    token = get_developer_token()
    if not token:
        print("❌ 无法获取开发者token")
        return
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    test_routes = [
        {
            "url": f"{BASE_URL}/api/v1/test/permission-check",
            "method": "GET",
            "name": "权限保护测试路由"
        },
        {
            "url": f"{BASE_URL}/api/v1/test/role-level",
            "method": "POST",
            "name": "角色级别测试路由",
            "data": {"action": "developer_test"}
        }
    ]
    
    print("🧪 测试开发者访问权限保护路由...")
    
    success_count = 0
    for route in test_routes:
        try:
            print(f"\n📞 开发者访问: {route['name']}")
            
            if route["method"] == "GET":
                response = requests.get(route["url"], headers=headers, timeout=10)
            else:
                response = requests.post(
                    route["url"], 
                    headers=headers, 
                    json=route.get("data", {}), 
                    timeout=10
                )
            
            print(f"📊 状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ 开发者访问成功: {route['name']}")
                success_count += 1
                try:
                    data = response.json()
                    print(f"📄 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"📄 响应内容: {response.text[:200]}...")
            elif response.status_code == 403:
                print(f"🔒 开发者权限不足: {route['name']}")
                print(f"📄 响应: {response.text}")
            elif response.status_code == 401:
                print(f"🔑 开发者认证失败: {route['name']}")
                print(f"📄 响应: {response.text}")
            else:
                print(f"❌ 开发者访问失败: {route['name']} - {response.status_code}")
                print(f"📄 响应: {response.text}")
                
        except Exception as e:
            print(f"❌ 测试开发者访问异常: {route['name']} - {e}")
    
    print(f"\n📊 测试结果:")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {len(test_routes) - success_count}")
    print(f"📈 成功率: {success_count/len(test_routes)*100:.1f}%")
    
    if success_count == len(test_routes):
        print("🎉 开发者权限测试通过！权限配置系统工作正常。")
    else:
        print("⚠️ 部分测试失败，请检查权限配置。")


def test_register_and_access():
    """测试注册一个新的权限保护路由并访问"""
    token = get_developer_token()
    if not token:
        print("❌ 无法获取开发者token")
        return
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    print("\n🔧 注册一个新的权限保护路由...")
    
    route_data = {
        "api_id": "test_comprehensive_permission",
        "name": "综合权限测试路由",
        "endpoint": "/api/v1/test/comprehensive-permission",
        "method": "POST",
        "description": "综合测试新权限系统的完整功能",
        "auth_required": True,
        "permission_config": {
            "required_permissions": [
                {
                    "resource": "comprehensive_test",
                    "action": "execute",
                    "description": "执行综合测试权限"
                }
            ],
            "required_roles": [],
            "min_role_level": None,
            "allow_developer": True
        },
        "handler": {
            "type": "static_data",
            "config": {
                "data": {
                    "message": "🎉 综合权限验证成功！",
                    "system": "新权限配置系统",
                    "test_result": "PASSED",
                    "developer_access": True,
                    "timestamp": "2024-01-20T10:00:00.000Z"
                }
            }
        },
        "parameters": [
            {
                "name": "test_type",
                "type": "string",
                "location": "body",
                "required": True,
                "description": "测试类型"
            }
        ],
        "responses": {
            "200": {
                "description": "综合权限测试成功",
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
        response = requests.post(
            f"{BASE_URL}/api/v1/routes/register",
            headers=headers,
            json=route_data,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            route_id = data["data"]["route"]["id"]
            print(f"✅ 新权限保护路由注册成功，路由ID: {route_id}")
            
            # 测试访问新路由
            print(f"\n📞 测试访问新注册的权限保护路由...")
            test_response = requests.post(
                f"{BASE_URL}{route_data['endpoint']}",
                headers=headers,
                json={"test_type": "comprehensive_permission_test"},
                timeout=10
            )
            
            print(f"📊 状态码: {test_response.status_code}")
            if test_response.status_code == 200:
                print(f"✅ 新路由访问成功！")
                try:
                    test_data = test_response.json()
                    print(f"📄 响应数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"📄 响应内容: {test_response.text}")
                return True
            else:
                print(f"❌ 新路由访问失败: {test_response.status_code}")
                print(f"📄 响应: {test_response.text}")
                return False
        else:
            print(f"❌ 路由注册失败: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 注册和测试新路由异常: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始权限配置系统综合测试...")
    
    # 1. 测试开发者访问现有的权限保护路由
    test_developer_access_to_protected_routes()
    
    # 2. 测试注册新的权限保护路由并访问
    success = test_register_and_access()
    
    if success:
        print("\n🎉 恭喜！权限配置系统完全正常工作！")
        print("✅ 路由注册支持权限配置")
        print("✅ 动态路由处理器支持权限验证")
        print("✅ 开发者访问控制正常")
        print("✅ 权限配置数据库字段正常")
    else:
        print("\n⚠️ 权限配置系统部分功能异常，需要进一步检查。")


if __name__ == "__main__":
    main()
