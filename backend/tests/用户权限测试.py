#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户权限测试脚本
测试用户111是否能访问患者创建API和患者列表API
"""

import requests
import json
import time
from typing import Dict, Any

class UserPermissionTest:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.username = "111"
        self.password = "123456"
        self.token = None
        
    def login_user(self) -> bool:
        """用户登录"""
        print("🔑 正在登录用户...")
        
        login_data = {
            "username": self.username,
            "password": self.password
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/user/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"📤 登录请求状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["data"]["access_token"]
                user_info = data["data"]["user"]
                
                print("✅ 登录成功!")
                print(f"👤 用户ID: {user_info['id']}")
                print(f"👤 用户名: {user_info['username']}")
                print(f"👤 真实姓名: {user_info.get('real_name', 'N/A')}")
                print(f"🏷️  角色: {user_info['role']['name']} ({user_info['role']['code']})")
                print(f"🔑 Token: {self.token[:50]}...")
                
                return True
            else:
                print("❌ 登录失败")
                print(f"响应内容: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False
    
    def check_user_permissions(self) -> None:
        """检查用户权限"""
        if not self.token:
            print("❌ 未登录，无法检查权限")
            return
            
        print("\n🔍 检查用户权限...")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/api/v1/user/permissions",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                accessible_apis = data["data"].get("accessible_apis", [])
                
                print("✅ 用户权限信息:")
                print(f"📊 可访问API数量: {len(accessible_apis)}")
                
                # 查找患者相关API
                patient_apis = [api for api in accessible_apis if 'patient' in api.get('endpoint', '').lower() or 'patient' in api.get('name', '').lower()]
                
                print(f"🏥 患者相关API数量: {len(patient_apis)}")
                
                for api in patient_apis:
                    print(f"  - {api.get('name', 'N/A')}: {api.get('method', 'N/A')} {api.get('endpoint', 'N/A')}")
                    
            else:
                print(f"❌ 获取权限失败，状态码: {response.status_code}")
                print(f"响应: {response.text}")
                
        except Exception as e:
            print(f"❌ 检查权限异常: {e}")
    
    def test_patient_create_api(self) -> bool:
        """测试患者创建API"""
        if not self.token:
            print("❌ 未登录，无法测试API")
            return False
            
        print("\n🧪 测试患者创建API...")
        
        # 测试数据
        patient_data = {
            "name": "测试患者",
            "id_card": "110101199001011234",
            "phone": "13800138000",
            "gender": "男",
            "birth_date": "1990-01-01",
            "address": "北京市朝阳区测试地址"
        }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            # 尝试访问患者创建API
            response = requests.post(
                f"{self.base_url}/api/v1/patients",
                json=patient_data,
                headers=headers,
                timeout=10
            )
            
            print(f"📤 患者创建API状态码: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("✅ 患者创建API访问成功!")
                data = response.json()
                print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            elif response.status_code == 403:
                print("❌ 权限不足，无法访问患者创建API")
                print(f"响应: {response.text}")
                return False
            elif response.status_code == 404:
                print("⚠️  患者创建API不存在")
                print(f"响应: {response.text}")
                return False
            else:
                print(f"❌ 患者创建API访问失败，状态码: {response.status_code}")
                print(f"响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 测试患者创建API异常: {e}")
            return False
    
    def test_patient_list_api(self) -> bool:
        """测试患者列表API"""
        if not self.token:
            print("❌ 未登录，无法测试API")
            return False
            
        print("\n📋 测试患者列表API...")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            # 尝试访问患者列表API
            response = requests.get(
                f"{self.base_url}/api/v1/patients",
                headers=headers,
                params={"page": 1, "limit": 10},
                timeout=10
            )
            
            print(f"📤 患者列表API状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ 患者列表API访问成功!")
                data = response.json()
                print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            elif response.status_code == 403:
                print("❌ 权限不足，无法访问患者列表API")
                print(f"响应: {response.text}")
                return False
            elif response.status_code == 404:
                print("⚠️  患者列表API不存在")
                print(f"响应: {response.text}")
                return False
            else:
                print(f"❌ 患者列表API访问失败，状态码: {response.status_code}")
                print(f"响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 测试患者列表API异常: {e}")
            return False
    
    def test_dynamic_patient_apis(self) -> None:
        """测试动态注册的患者API"""
        if not self.token:
            print("❌ 未登录，无法测试API")
            return
            
        print("\n🔗 测试动态注册的患者API...")
        
        # 测试通过动态路由注册的患者API
        dynamic_endpoints = [
            ("/api/v1/dynamic/patient_create_api", "POST"),
            ("/api/v1/dynamic/patient_list_api", "GET"),
        ]
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        for endpoint, method in dynamic_endpoints:
            try:
                print(f"\n🔍 测试 {method} {endpoint}")
                
                if method == "GET":
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        timeout=10
                    )
                elif method == "POST":
                    test_data = {
                        "name": "动态测试患者",
                        "id_card": "110101199002021234",
                        "phone": "13800138001"
                    }
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        json=test_data,
                        headers=headers,
                        timeout=10
                    )
                else:
                    continue
                
                print(f"📤 状态码: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    print("✅ API访问成功!")
                elif response.status_code == 403:
                    print("❌ 权限不足")
                elif response.status_code == 404:
                    print("⚠️  API不存在或未注册")
                else:
                    print(f"❌ API访问失败: {response.status_code}")
                
                print(f"响应: {response.text[:200]}{'...' if len(response.text) > 200 else ''}")
                
            except Exception as e:
                print(f"❌ 测试 {endpoint} 异常: {e}")
    
    def run_all_tests(self) -> None:
        """运行所有测试"""
        print("=" * 80)
        print("🧪 用户权限测试开始")
        print("=" * 80)
        
        # 1. 登录
        if not self.login_user():
            print("\n❌ 登录失败，测试终止")
            return
        
        # 2. 检查权限
        self.check_user_permissions()
        
        # 3. 测试患者创建API
        create_success = self.test_patient_create_api()
        
        # 4. 测试患者列表API
        list_success = self.test_patient_list_api()
        
        # 5. 测试动态API
        self.test_dynamic_patient_apis()
        
        # 总结
        print("\n" + "=" * 80)
        print("📊 测试总结")
        print("=" * 80)
        print(f"🔑 登录状态: ✅ 成功")
        print(f"🏥 患者创建API: {'✅ 成功' if create_success else '❌ 失败'}")
        print(f"📋 患者列表API: {'✅ 成功' if list_success else '❌ 失败'}")
        
        if not (create_success and list_success):
            print("\n🔧 需要修复的问题:")
            if not create_success:
                print("  - 用户111无法访问患者创建API，需要授权")
            if not list_success:
                print("  - 用户111无法访问患者列表API，需要授权")


if __name__ == "__main__":
    # 运行测试
    test = UserPermissionTest()
    test.run_all_tests()
