#!/usr/bin/env python3
"""
第十二部分：用户认证API测试
测试用户登录、注册、登出功能，以及基于权限的amis schema生成
符合第八、第九部分API文档规范的用户认证系统
"""
import requests
import json
import time
import sys
import os
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试配置
BASE_URL = "http://localhost:5000"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

class TestUserAuth:
    """用户认证测试类"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.test_user_token = None
        self.test_user_info = None
    
    def test_user_registration(self):
        """测试用户注册"""
        print("=== 测试用户注册 ===")
        
        # 生成唯一的测试用户
        timestamp = int(time.time())
        test_user = {
            "username": f"testuser_{timestamp}",
            "email": f"test_{timestamp}@example.com",
            "password": "password123",
            "real_name": "测试用户"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/user/register",
                json=test_user
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    user_data = data.get("data", {})
                    print(f"✅ 用户注册成功")
                    print(f"用户ID: {user_data.get('user_id')}")
                    print(f"用户名: {user_data.get('username')}")
                    print(f"角色: {user_data.get('role', {}).get('name')}")
                    
                    # 保存测试用户信息用于后续测试
                    self.test_user_info = {
                        "username": test_user["username"],
                        "password": test_user["password"],
                        "user_id": user_data.get("user_id")
                    }
                    
                    return True
                else:
                    print(f"❌ 注册失败: {data.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"❌ 请求失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
            return False
    
    def test_user_login(self):
        """测试用户登录"""
        print("\n=== 测试用户登录 ===")
        
        if not self.test_user_info:
            print("❌ 没有测试用户信息，请先运行注册测试")
            return False
        
        login_data = {
            "username": self.test_user_info["username"],
            "password": self.test_user_info["password"]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/user/login",
                json=login_data
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    login_result = data.get("data", {})
                    print(f"✅ 用户登录成功")
                    print(f"Token类型: {login_result.get('token_type')}")
                    print(f"过期时间: {login_result.get('expires_in')}秒")
                    
                    user_info = login_result.get("user", {})
                    print(f"用户: {user_info.get('username')} ({user_info.get('real_name')})")
                    print(f"角色: {user_info.get('role', {}).get('name')}")
                    
                    permissions = login_result.get("permissions", {})
                    apis = permissions.get("apis", [])
                    features = permissions.get("features", [])
                    print(f"可访问API数量: {len(apis)}")
                    print(f"可用功能: {', '.join(features)}")
                    
                    # 保存token用于后续测试
                    self.test_user_token = login_result.get("access_token")
                    
                    return True
                else:
                    print(f"❌ 登录失败: {data.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"❌ 请求失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
            return False
    
    def test_get_user_profile(self):
        """测试获取用户信息"""
        print("\n=== 测试获取用户信息 ===")
        
        if not self.test_user_token:
            print("❌ 没有用户token，请先登录")
            return False
        
        try:
            headers = self.headers.copy()
            headers["Authorization"] = f"Bearer {self.test_user_token}"
            
            response = self.session.get(
                f"{self.base_url}/api/user/me",
                headers=headers
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    user_data = data.get("data", {})
                    print(f"✅ 获取用户信息成功")
                    print(f"用户ID: {user_data.get('id')}")
                    print(f"用户名: {user_data.get('username')}")
                    print(f"邮箱: {user_data.get('email')}")
                    print(f"角色: {user_data.get('role', {}).get('name')}")
                    print(f"创建时间: {user_data.get('created_at')}")
                    
                    return True
                else:
                    print(f"❌ 获取失败: {data.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"❌ 请求失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
            return False
    
    def test_ai_command_with_auth(self):
        """测试带认证的AI命令处理"""
        print("\n=== 测试带认证的AI命令处理 ===")
        
        if not self.test_user_token:
            print("❌ 没有用户token，请先登录")
            return False
        
        # 模拟用户权限信息
        command_data = {
            "command": "显示用户列表",
            "context": {
                "user_id": self.test_user_info.get("user_id") if self.test_user_info else "test_user",
                "user_permissions": ["user:read", "data:query"],
                "accessible_apis": [
                    {
                        "endpoint": "/api/users",
                        "method": "GET",
                        "description": "获取用户列表",
                        "resource": "users",
                        "action": "list"
                    }
                ],
                "user_role": {
                    "id": "role_普通用户",
                    "name": "普通用户",
                    "level": 1
                }
            }
        }
        
        try:
            headers = self.headers.copy()
            headers["Authorization"] = f"Bearer {self.test_user_token}"
            
            response = self.session.post(
                f"{self.base_url}/api/command",
                json=command_data,
                headers=headers
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result_data = data.get("data", {})
                    print(f"✅ AI命令处理成功")
                    print(f"意图类型: {result_data.get('intent', {}).get('intent_type', 'unknown')}")
                    
                    schema = result_data.get('amis_schema', {})
                    print(f"Schema类型: {schema.get('type', 'unknown')}")
                    
                    # 检查schema是否包含权限约束
                    if schema.get('type') == 'page':
                        body = schema.get('body', [])
                        if body and isinstance(body, list):
                            first_component = body[0]
                            if first_component.get('type') == 'crud':
                                print("✅ 生成了CRUD组件")
                                
                                # 检查API配置
                                api_config = first_component.get('api', {})
                                if isinstance(api_config, dict):
                                    headers = api_config.get('headers', {})
                                    if 'Authorization' in headers:
                                        print("✅ API配置包含认证头部")
                                    else:
                                        print("⚠️  API配置缺少认证头部")
                    
                    validation = result_data.get('validation', {})
                    print(f"Schema校验: {'通过' if validation.get('is_valid') else '失败'}")
                    
                    return True
                else:
                    print(f"❌ 命令处理失败: {data.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ 请求失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
            return False
    
    def test_user_logout(self):
        """测试用户登出"""
        print("\n=== 测试用户登出 ===")
        
        if not self.test_user_token:
            print("❌ 没有用户token，请先登录")
            return False
        
        try:
            headers = self.headers.copy()
            headers["Authorization"] = f"Bearer {self.test_user_token}"
            
            response = self.session.post(
                f"{self.base_url}/api/user/logout",
                headers=headers
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    logout_data = data.get("data", {})
                    print(f"✅ 用户登出成功")
                    print(f"登出时间: {logout_data.get('logged_out_at')}")
                    
                    # 清除token
                    self.test_user_token = None
                    
                    return True
                else:
                    print(f"❌ 登出失败: {data.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"❌ 请求失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始用户认证模块完整测试...")
        print("=" * 60)
        
        # 等待服务启动
        print("等待后端服务启动...")
        time.sleep(2)
        
        test_results = []
        
        # 1. 用户注册测试
        result = self.test_user_registration()
        test_results.append(("用户注册", result))
        
        # 2. 用户登录测试
        result = self.test_user_login()
        test_results.append(("用户登录", result))
        
        # 3. 获取用户信息测试
        result = self.test_get_user_profile()
        test_results.append(("获取用户信息", result))
        
        # 4. 带认证的AI命令处理测试
        result = self.test_ai_command_with_auth()
        test_results.append(("带认证AI命令处理", result))
        
        # 5. 用户登出测试
        result = self.test_user_logout()
        test_results.append(("用户登出", result))
        
        # 测试总结
        print("\n" + "=" * 60)
        print("测试总结:")
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n总体结果: {passed}/{total} 测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！用户认证模块功能正常")
        else:
            print("⚠️  部分测试失败，请检查相关功能")
        
        return passed == total


def main():
    """主函数"""
    tester = TestUserAuth()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ 用户认证模块测试完成，所有功能正常")
        sys.exit(0)
    else:
        print("\n❌ 用户认证模块测试失败，请检查相关问题")
        sys.exit(1)


if __name__ == "__main__":
    main()
