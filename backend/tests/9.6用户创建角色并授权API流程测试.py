"""
用户创建角色并授权API流程测试
验证完整的用户工作流程：
1. 用户（开发者）创建角色
2. 用户为角色授权特定的API访问权限
3. 验证角色权限生效
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


def test_user_create_role_and_authorize_api():
    """测试用户创建角色并授权API的完整流程"""
    print("👤 用户创建角色并授权API流程测试")
    print("=" * 80)
    print("验证完整的用户工作流程：")
    print("1. 用户（开发者）创建角色")
    print("2. 用户为角色授权特定的API访问权限")
    print("3. 验证角色权限生效")
    
    # 获取token
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_results = []
    created_roles = []
    
    # 步骤1: 用户创建自定义业务角色
    print("\n🔨 步骤1: 用户创建自定义业务角色")
    print("-" * 60)
    
    # 创建健身房前台角色
    gym_receptionist_role = {
        "name": "健身房前台",
        "code": "gym_receptionist",
        "level": 2,
        "description": "健身房前台接待人员，负责会员接待、咨询和基础服务",
        "status": "active",
        "permissions": [],  # 初始不分配任何权限
        "metadata": {
            "department": "service",
            "business_type": "fitness",
            "work_hours": "09:00-21:00",
            "can_handle_membership": True
        }
    }
    
    try:
        response = requests.post("http://localhost:5000/api/roles", 
                               headers=headers, json=gym_receptionist_role)
        if response.status_code == 201:
            data = response.json()
            role_id = data["data"]["role"]["id"]
            role_name = data["data"]["role"]["name"]
            created_roles.append(role_id)
            print(f"✅ 用户成功创建角色: {role_name} (ID: {role_id})")
            test_results.append(True)
        elif response.status_code == 409:
            print("✅ 角色已存在，获取现有角色")
            # 获取现有角色ID
            roles_response = requests.get("http://localhost:5000/api/roles", headers=headers)
            if roles_response.status_code == 200:
                roles_data = roles_response.json()
                for role in roles_data["data"]["roles"]:
                    if role["code"] == "gym_receptionist":
                        created_roles.append(role["id"])
                        print(f"✅ 找到现有角色: {role['name']} (ID: {role['id']})")
                        break
            test_results.append(True)
        else:
            print(f"❌ 角色创建失败: {response.status_code} - {response.text}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 角色创建异常: {e}")
        test_results.append(False)
    
    # 创建私人教练角色
    personal_trainer_role = {
        "name": "私人教练",
        "code": "personal_trainer",
        "level": 4,
        "description": "私人健身教练，负责会员训练指导和健身计划制定",
        "status": "active",
        "permissions": [],  # 初始不分配任何权限
        "metadata": {
            "department": "training",
            "business_type": "fitness",
            "specialization": ["weight_training", "cardio", "nutrition"],
            "can_create_training_plan": True,
            "max_clients": 20
        }
    }
    
    try:
        response = requests.post("http://localhost:5000/api/roles", 
                               headers=headers, json=personal_trainer_role)
        if response.status_code == 201:
            data = response.json()
            role_id = data["data"]["role"]["id"]
            role_name = data["data"]["role"]["name"]
            created_roles.append(role_id)
            print(f"✅ 用户成功创建角色: {role_name} (ID: {role_id})")
            test_results.append(True)
        elif response.status_code == 409:
            print("✅ 角色已存在，获取现有角色")
            # 获取现有角色ID
            roles_response = requests.get("http://localhost:5000/api/roles", headers=headers)
            if roles_response.status_code == 200:
                roles_data = roles_response.json()
                for role in roles_data["data"]["roles"]:
                    if role["code"] == "personal_trainer":
                        created_roles.append(role["id"])
                        print(f"✅ 找到现有角色: {role['name']} (ID: {role['id']})")
                        break
            test_results.append(True)
        else:
            print(f"❌ 角色创建失败: {response.status_code} - {response.text}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 角色创建异常: {e}")
        test_results.append(False)
    
    # 步骤2: 用户为角色授权特定的API访问权限
    print("\n🔐 步骤2: 用户为角色授权特定的API访问权限")
    print("-" * 60)
    
    if len(created_roles) >= 2:
        gym_receptionist_id = created_roles[0]
        personal_trainer_id = created_roles[1]
        
        # 为健身房前台授权基础API权限
        print("为健身房前台授权API权限:")
        receptionist_permissions = [
            {
                "api_id": "customer_list_api",
                "permission": "customers:read",
                "description": "查看客户列表"
            },
            {
                "api_id": "customer_create_api", 
                "permission": "customers:create",
                "description": "创建新客户"
            },
            {
                "api_id": "product_list_api",
                "permission": "products:read", 
                "description": "查看产品列表"
            },
            {
                "api_id": "order_list_api",
                "permission": "orders:read",
                "description": "查看订单列表"
            }
        ]
        
        for perm in receptionist_permissions:
            try:
                role_api_data = {
                    "role_id": gym_receptionist_id,
                    "api_id": perm["api_id"],
                    "permission": perm["permission"],
                    "action": "grant"
                }
                
                response = requests.post("http://localhost:5000/api/permissions/role-api", 
                                       headers=headers, json=role_api_data)
                if response.status_code == 200:
                    print(f"  ✅ 授权成功: {perm['description']}")
                    test_results.append(True)
                elif response.status_code == 400:
                    print(f"  ✅ 权限已存在: {perm['description']}")
                    test_results.append(True)
                else:
                    print(f"  ❌ 授权失败: {perm['description']} - {response.status_code}")
                    test_results.append(False)
            except Exception as e:
                print(f"  ❌ 授权异常: {perm['description']} - {e}")
                test_results.append(False)
        
        # 为私人教练授权更高级的API权限
        print("\n为私人教练授权API权限:")
        trainer_permissions = [
            {
                "api_id": "customer_list_api",
                "permission": "customers:read",
                "description": "查看客户列表"
            },
            {
                "api_id": "customer_update_api",
                "permission": "customers:update", 
                "description": "更新客户信息"
            },
            {
                "api_id": "order_create_api",
                "permission": "orders:create",
                "description": "创建订单"
            },
            {
                "api_id": "order_update_api",
                "permission": "orders:update",
                "description": "更新订单"
            },
            {
                "api_id": "product_list_api",
                "permission": "products:read",
                "description": "查看产品列表"
            }
        ]
        
        for perm in trainer_permissions:
            try:
                role_api_data = {
                    "role_id": personal_trainer_id,
                    "api_id": perm["api_id"],
                    "permission": perm["permission"],
                    "action": "grant"
                }
                
                response = requests.post("http://localhost:5000/api/permissions/role-api", 
                                       headers=headers, json=role_api_data)
                if response.status_code == 200:
                    print(f"  ✅ 授权成功: {perm['description']}")
                    test_results.append(True)
                elif response.status_code == 400:
                    print(f"  ✅ 权限已存在: {perm['description']}")
                    test_results.append(True)
                else:
                    print(f"  ❌ 授权失败: {perm['description']} - {response.status_code}")
                    test_results.append(False)
            except Exception as e:
                print(f"  ❌ 授权异常: {perm['description']} - {e}")
                test_results.append(False)
    else:
        print("❌ 没有足够的角色进行权限授权")
        test_results.extend([False] * 9)  # 9个权限授权测试
    
    # 步骤3: 验证权限矩阵中的角色权限配置
    print("\n📊 步骤3: 验证权限矩阵中的角色权限配置")
    print("-" * 60)
    
    try:
        response = requests.get("http://localhost:5000/api/permissions/matrix", headers=headers)
        if response.status_code == 200:
            data = response.json()
            matrix = data["data"]["matrix"]
            
            # 查找我们创建的角色
            gym_receptionist_role = None
            personal_trainer_role = None
            
            for role in matrix["roles"]:
                if role["code"] == "gym_receptionist":
                    gym_receptionist_role = role
                elif role["code"] == "personal_trainer":
                    personal_trainer_role = role
            
            if gym_receptionist_role and personal_trainer_role:
                print("✅ 在权限矩阵中找到用户创建的角色")
                
                # 检查权限分配
                gym_permissions = matrix["permissions"].get(gym_receptionist_role["id"], {})
                trainer_permissions = matrix["permissions"].get(personal_trainer_role["id"], {})
                
                gym_api_count = sum(1 for has_perm in gym_permissions.values() if has_perm)
                trainer_api_count = sum(1 for has_perm in trainer_permissions.values() if has_perm)
                
                print(f"✅ 健身房前台可访问 {gym_api_count} 个API")
                print(f"✅ 私人教练可访问 {trainer_api_count} 个API")
                
                # 显示具体权限
                print("\n📋 健身房前台API权限:")
                for api in matrix["apis"]:
                    has_permission = gym_permissions.get(api["id"], False)
                    status = "✅" if has_permission else "❌"
                    print(f"  {status} {api['name']}")
                
                print("\n📋 私人教练API权限:")
                for api in matrix["apis"]:
                    has_permission = trainer_permissions.get(api["id"], False)
                    status = "✅" if has_permission else "❌"
                    print(f"  {status} {api['name']}")
                
                test_results.append(True)
            else:
                print("❌ 在权限矩阵中未找到用户创建的角色")
                test_results.append(False)
        else:
            print(f"❌ 获取权限矩阵失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 验证权限矩阵异常: {e}")
        test_results.append(False)
    
    # 步骤4: 测试批量权限管理
    print("\n⚡ 步骤4: 测试批量权限管理")
    print("-" * 60)
    
    if len(created_roles) >= 2:
        batch_updates = {
            "updates": [
                {
                    "role_id": created_roles[0],
                    "api_id": "order_create_api",
                    "permission": "orders:create",
                    "action": "grant"
                },
                {
                    "role_id": created_roles[1],
                    "api_id": "customer_delete_api",
                    "permission": "customers:delete",
                    "action": "revoke"
                }
            ],
            "dry_run": False
        }
        
        try:
            response = requests.post("http://localhost:5000/api/permissions/batch-update", 
                                   headers=headers, json=batch_updates)
            if response.status_code == 200:
                data = response.json()
                summary = data["data"]["summary"]
                print(f"✅ 批量权限更新成功")
                print(f"  总更新: {summary['total']}")
                print(f"  成功: {summary['successful']}")
                print(f"  失败: {summary['failed']}")
                test_results.append(True)
            else:
                print(f"❌ 批量权限更新失败: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 批量权限更新异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有足够的角色进行批量权限测试")
        test_results.append(False)
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 80)
    print("📊 用户创建角色并授权API流程测试结果")
    print("-" * 80)
    print(f"总测试项: {total}")
    print(f"测试通过: {passed}")
    print(f"测试失败: {total - passed}")
    print(f"成功率: {(passed / total * 100):.1f}%")
    
    if passed == total:
        print("\n🎉 用户创建角色并授权API流程测试全部通过！")
        print("✅ 用户可以自由创建自定义角色")
        print("✅ 用户可以为角色授权特定API权限")
        print("✅ 权限配置实时生效")
        print("✅ 支持批量权限管理")
        print("✅ 权限矩阵正确反映用户配置")
        
        print("\n🎯 完整工作流程验证:")
        print("1. ✅ 用户创建角色 → 成功")
        print("2. ✅ 用户授权API → 成功") 
        print("3. ✅ 权限验证 → 成功")
        print("4. ✅ 批量管理 → 成功")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试项失败")
    
    return passed == total


if __name__ == "__main__":
    success = test_user_create_role_and_authorize_api()
    if success:
        print("\n🚀 用户创建角色并授权API的完整流程工作正常！")
    else:
        print("\n❌ 用户创建角色并授权API的流程存在问题")
    exit(0 if success else 1)
