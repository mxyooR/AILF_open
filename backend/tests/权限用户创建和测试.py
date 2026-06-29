#!/usr/bin/env python3
"""
创建测试用户和角色，用于测试权限配置
"""

import sys
import os
import requests
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db_session
from app.models.user import User as UserDBModel
from app.models.role import RoleDBModel, PermissionDBModel
from app.services.role_service import RoleService
from app.services.permission_service import PermissionService

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


def create_test_permissions():
    """创建测试需要的权限"""
    with get_db_session() as db:
        # 需要创建的权限
        test_permissions = [
            {
                "name": "test_data:read",
                "resource": "test_data",
                "action": "read",
                "description": "读取测试数据权限"
            }
        ]
        
        created_permissions = []
        for perm in test_permissions:
            # 检查权限是否已存在
            existing = db.query(PermissionDBModel).filter(
                PermissionDBModel.name == perm["name"]
            ).first()
            
            if not existing:
                try:
                    # 直接创建权限对象
                    import time
                    perm_id = f"perm_{int(time.time() * 1000)}"
                    
                    new_permission = PermissionDBModel(
                        id=perm_id,
                        name=perm["name"],
                        resource=perm["resource"],
                        action=perm["action"],
                        description=perm["description"],
                        is_system=False,
                        is_active=True
                    )
                    
                    db.add(new_permission)
                    db.commit()
                    
                    created_permissions.append(perm["name"])
                    print(f"✅ 创建权限: {perm['name']}")
                    
                except Exception as e:
                    print(f"❌ 创建权限异常: {perm['name']} - {e}")
                    db.rollback()
            else:
                print(f"ℹ️ 权限已存在: {perm['name']}")
        
        return created_permissions


def create_test_role():
    """创建测试角色"""
    with get_db_session() as db:
        # 检查测试管理员角色是否已存在
        existing_role = db.query(RoleDBModel).filter(
            RoleDBModel.code == "test_manager"
        ).first()
        
        if not existing_role:
            try:
                # 直接创建角色对象
                import time
                role_id = f"role_{int(time.time() * 1000)}"
                
                new_role = RoleDBModel(
                    id=role_id,
                    name="测试管理员",
                    code="test_manager",
                    description="用于测试权限系统的管理员角色",
                    status="active",
                    user_count=0,
                    permission_count=0
                )
                
                db.add(new_role)
                db.commit()
                
                print(f"✅ 创建角色: 测试管理员 (ID: {role_id})")
                
                # 为角色分配权限
                test_data_perm = db.query(PermissionDBModel).filter(
                    PermissionDBModel.name == "test_data:read"
                ).first()
                
                products_perm = db.query(PermissionDBModel).filter(
                    PermissionDBModel.name == "products:read"
                ).first()
                
                if test_data_perm:
                    new_role.permissions.append(test_data_perm)
                    print(f"✅ 分配权限: test_data:read")
                
                if products_perm:
                    new_role.permissions.append(products_perm)
                    print(f"✅ 分配权限: products:read")
                
                # 更新权限数量
                new_role.permission_count = len(list(new_role.permissions))
                db.commit()
                
                return role_id
                
            except Exception as e:
                print(f"❌ 创建角色异常: {e}")
                db.rollback()
                return None
        else:
            print(f"ℹ️ 角色已存在: 测试管理员 (ID: {existing_role.id})")
            return existing_role.id


def create_test_user(role_id):
    """创建测试用户"""
    token = get_developer_token()
    if not token:
        print("❌ 无法获取认证token")
        return None
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    user_data = {
        "username": "testuser",
        "password": "123456",
        "email": "testuser@example.com",
        "name": "测试用户",
        "role_id": role_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/users",
            headers=headers,
            json=user_data,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            user_id = data["data"]["user"]["id"]
            print(f"✅ 创建测试用户成功: testuser (ID: {user_id})")
            return user_id
        else:
            print(f"❌ 创建用户失败: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 创建用户异常: {e}")
        return None


def get_test_user_token():
    """获取测试用户的JWT token"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": "testuser", "password": "123456"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data["data"]["access_token"]
            print(f"✅ 获取测试用户token成功")
            return token
        else:
            print(f"❌ 用户登录失败: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 用户登录异常: {e}")
        return None


def test_user_access():
    """测试用户访问权限保护的路由"""
    user_token = get_test_user_token()
    if not user_token:
        print("❌ 无法获取用户token，跳过访问测试")
        return
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {user_token}"
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
            "data": {"action": "test"}
        }
    ]
    
    print("\n🧪 测试用户访问权限保护路由...")
    
    for route in test_routes:
        try:
            print(f"\n📞 用户访问: {route['name']}")
            
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
                print(f"✅ 用户访问成功: {route['name']}")
                try:
                    data = response.json()
                    print(f"📄 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"📄 响应内容: {response.text[:200]}...")
            elif response.status_code == 403:
                print(f"🔒 用户权限不足: {route['name']}")
                print(f"📄 响应: {response.text}")
            elif response.status_code == 401:
                print(f"🔑 用户认证失败: {route['name']}")
                print(f"📄 响应: {response.text}")
            else:
                print(f"❌ 用户访问失败: {route['name']} - {response.status_code}")
                print(f"📄 响应: {response.text}")
                
        except Exception as e:
            print(f"❌ 测试用户访问异常: {route['name']} - {e}")


def main():
    """主函数"""
    print("🚀 开始创建测试用户和角色...")
    
    try:
        # 1. 创建测试权限
        print("\n📋 创建测试权限...")
        create_test_permissions()
        
        # 2. 创建测试角色
        print("\n👥 创建测试角色...")
        role_id = create_test_role()
        
        if not role_id:
            print("❌ 无法创建测试角色，终止")
            return
        
        # 3. 创建测试用户
        print("\n👤 创建测试用户...")
        user_id = create_test_user(role_id)
        
        if not user_id:
            print("❌ 无法创建测试用户，但继续测试")
        
        # 4. 测试用户访问
        print("\n🧪 测试用户权限访问...")
        test_user_access()
        
        print("\n🎉 权限配置测试完成!")
        
    except Exception as e:
        print(f"💥 测试失败: {e}")


if __name__ == "__main__":
    main()
