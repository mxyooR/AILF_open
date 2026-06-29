#!/usr/bin/env python3
"""
测试带权限配置的API路由注册
"""

import sys
import os
import requests
import json
from pathlib import Path

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
            token = data["data"]["token"]
            print(f"✅ 获取开发者token成功")
            return token
        else:
            print(f"❌ 认证失败: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 认证异常: {e}")
        return None


def get_headers_with_token():
    """获取带token的请求头"""
    token = get_developer_token()
    if not token:
        return None
    
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }


def test_register_protected_route():
    """测试注册带权限配置的路由"""
    
    # 获取认证头
    headers = get_headers_with_token()
    if not headers:
        print("❌ 无法获取认证token，测试终止")
        return False
    
    route_data = {
        "api_id": "test_permission_protected_route",
        "name": "权限保护测试路由",
        "endpoint": "/api/v1/test/permission-check",
        "method": "GET",
        "description": "测试新权限系统的受保护路由",
        "auth_required": True,
        "permission_config": {
            "required_permissions": [
                {
                    "resource": "test_data",
                    "action": "read",
                    "description": "读取测试数据权限"
                },
                {
                    "resource": "products",
                    "action": "read",
                    "description": "读取产品信息权限"
                }
            ],
            "required_roles": ["manager", "admin"],
            "min_role_level": 3,
            "allow_developer": True
        },
        "handler": {
            "type": "static_data",
            "config": {
                "data": {
                    "message": "权限验证成功！您有权访问此API",
                    "permissions_required": ["test_data:read", "products:read"],
                    "roles_required": ["manager", "admin"],
                    "min_level": 3,
                    "timestamp": "2024-01-20T10:00:00.000Z"
                }
            }
        },
        "parameters": [],
        "responses": {
            "200": {
                "description": "成功返回权限验证结果",
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
        print("🔧 注册带权限配置的测试路由...")
        response = requests.post(
            f"{BASE_URL}/api/v1/routes/register",
            headers=headers,
            json=route_data,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            route_id = data["data"]["route"]["id"]
            print(f"✅ 权限保护路由注册成功，路由ID: {route_id}")
            print(f"📡 访问地址: {BASE_URL}{route_data['endpoint']}")
            return True
        else:
            print(f"❌ 路由注册失败: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 注册路由异常: {e}")
        return False


def test_register_role_level_route():
    """测试注册基于角色级别的路由"""
    
    # 获取认证头
    headers = get_headers_with_token()
    if not headers:
        print("❌ 无法获取认证token，测试终止")
        return False
    
    route_data = {
        "api_id": "test_role_level_route", 
        "name": "角色级别测试路由",
        "endpoint": "/api/v1/test/role-level",
        "method": "POST",
        "description": "只有高级别角色才能访问的路由",
        "auth_required": True,
        "permission_config": {
            "required_permissions": [],
            "required_roles": [],
            "min_role_level": 5,  # 需要至少5级权限
            "allow_developer": True
        },
        "handler": {
            "type": "static_data",
            "config": {
                "data": {
                    "message": "高级角色验证成功！",
                    "min_level_required": 5,
                    "access_granted": True
                }
            }
        },
        "parameters": [
            {
                "name": "action",
                "type": "string",
                "location": "body",
                "required": False,
                "description": "操作类型"
            }
        ],
        "responses": {
            "200": {
                "description": "高级别角色访问成功",
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
        print("🔧 注册角色级别测试路由...")
        response = requests.post(
            f"{BASE_URL}/api/v1/routes/register",
            headers=headers,
            json=route_data,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            route_id = data["data"]["route"]["id"]
            print(f"✅ 角色级别路由注册成功，路由ID: {route_id}")
            print(f"📡 访问地址: {BASE_URL}{route_data['endpoint']}")
            return True
        else:
            print(f"❌ 路由注册失败: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 注册路由异常: {e}")
        return False


def test_access_protected_routes():
    """测试访问受保护的路由"""
    
    # 获取认证头
    headers = get_headers_with_token()
    if not headers:
        print("❌ 无法获取认证token，测试终止")
        return
    
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
            "data": {"action": "test"}
        }
    ]
    
    print("\n🧪 测试访问受保护路由...")
    
    for route in test_routes:
        try:
            print(f"\n📞 测试访问: {route['name']}")
            
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
                print(f"✅ 访问成功: {route['name']}")
                try:
                    data = response.json()
                    print(f"📄 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"📄 响应内容: {response.text[:200]}...")
            elif response.status_code == 403:
                print(f"🔒 权限不足: {route['name']}")
                print(f"📄 响应: {response.text}")
            elif response.status_code == 401:
                print(f"🔑 认证失败: {route['name']}")
                print(f"📄 响应: {response.text}")
            else:
                print(f"❌ 访问失败: {route['name']} - {response.status_code}")
                print(f"📄 响应: {response.text}")
                
        except Exception as e:
            print(f"❌ 测试访问异常: {route['name']} - {e}")


def main():
    """执行测试"""
    print("🚀 开始测试权限配置的API路由功能...")
    
    results = []
    
    # 1. 测试注册权限保护路由
    results.append(test_register_protected_route())
    
    # 2. 测试注册角色级别路由
    results.append(test_register_role_level_route())
    
    # 3. 测试访问受保护路由
    test_access_protected_routes()
    
    # 总结
    print(f"\n📊 测试结果统计:")
    print(f"✅ 成功: {sum(results)}")
    print(f"❌ 失败: {len(results) - sum(results)}")
    print(f"📈 成功率: {sum(results)/len(results)*100:.1f}%")
    
    if all(results):
        print("🎉 所有权限配置测试通过!")
    else:
        print("⚠️ 部分测试失败，请检查权限配置")


if __name__ == "__main__":
    main()
