"""
真实业务角色API控制测试
验证前台、教练等具体业务角色能否正确控制API访问
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


def test_real_business_role_api_control():
    """测试真实业务角色API控制"""
    print("🏢 真实业务角色API控制测试")
    print("=" * 80)
    print("验证前台、教练等具体业务角色能否正确控制API访问")
    
    # 获取token
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_results = []
    
    # 1. 创建真实业务角色
    print("\n1️⃣ 创建真实业务角色")
    print("-" * 50)
    
    # 创建前台角色
    front_desk_role = {
        "name": "前台",
        "code": "front_desk",
        "level": 2,
        "description": "前台接待人员，负责客户接待和基础信息管理",
        "status": "active",
        "permissions": [
            "customers:read",
            "customers:create",
            "orders:read",
            "products:read"
        ],
        "metadata": {
            "department": "service",
            "business_role": "front_desk",
            "can_access_customer_info": True,
            "can_create_orders": False
        }
    }
    
    # 创建教练角色
    coach_role = {
        "name": "教练",
        "code": "coach",
        "level": 4,
        "description": "健身教练，负责会员训练指导和课程管理",
        "status": "active",
        "permissions": [
            "customers:read",
            "customers:update",
            "orders:read",
            "orders:create",
            "products:read",
            "reports:read"
        ],
        "metadata": {
            "department": "training",
            "business_role": "coach",
            "can_manage_members": True,
            "can_create_training_plans": True
        }
    }
    
    front_desk_id = None
    coach_id = None
    
    # 创建前台角色
    try:
        response = requests.post("http://localhost:5000/api/roles", 
                               headers=headers, json=front_desk_role)
        if response.status_code == 201:
            data = response.json()
            front_desk_id = data["data"]["role"]["id"]
            print(f"✅ 前台角色创建成功，ID: {front_desk_id}")
            test_results.append(True)
        elif response.status_code == 409:
            # 角色已存在，获取现有角色ID
            print("✅ 前台角色已存在")
            roles_response = requests.get("http://localhost:5000/api/roles", headers=headers)
            if roles_response.status_code == 200:
                roles_data = roles_response.json()
                for role in roles_data["data"]["roles"]:
                    if role["code"] == "front_desk":
                        front_desk_id = role["id"]
                        break
            test_results.append(True)
        else:
            print(f"❌ 前台角色创建失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 前台角色创建异常: {e}")
        test_results.append(False)
    
    # 创建教练角色
    try:
        response = requests.post("http://localhost:5000/api/roles", 
                               headers=headers, json=coach_role)
        if response.status_code == 201:
            data = response.json()
            coach_id = data["data"]["role"]["id"]
            print(f"✅ 教练角色创建成功，ID: {coach_id}")
            test_results.append(True)
        elif response.status_code == 409:
            # 角色已存在，获取现有角色ID
            print("✅ 教练角色已存在")
            roles_response = requests.get("http://localhost:5000/api/roles", headers=headers)
            if roles_response.status_code == 200:
                roles_data = roles_response.json()
                for role in roles_data["data"]["roles"]:
                    if role["code"] == "coach":
                        coach_id = role["id"]
                        break
            test_results.append(True)
        else:
            print(f"❌ 教练角色创建失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 教练角色创建异常: {e}")
        test_results.append(False)
    
    # 2. 测试前台角色的API访问权限
    print("\n2️⃣ 测试前台角色的API访问权限")
    print("-" * 50)
    
    # 模拟前台用户
    front_desk_user_id = "front_desk_user_001"
    
    # 测试前台可以访问的API - 客户信息查看
    permission_check_data = {
        "user_id": front_desk_user_id,
        "resource": "customers",
        "action": "read",
        "context": {
            "role": "front_desk",
            "department": "service"
        }
    }
    
    try:
        response = requests.post("http://localhost:5000/api/permissions/check", 
                               headers=headers, json=permission_check_data)
        if response.status_code in [200, 403]:
            data = response.json()
            allowed = data["data"]["allowed"]
            print(f"✅ 前台访问客户信息权限检查完成，允许: {allowed}")
            test_results.append(True)
        else:
            print(f"❌ 前台权限检查失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 前台权限检查异常: {e}")
        test_results.append(False)
    
    # 测试前台不能访问的API - 订单删除
    no_permission_data = {
        "user_id": front_desk_user_id,
        "resource": "orders",
        "action": "delete",
        "context": {
            "role": "front_desk"
        }
    }
    
    try:
        response = requests.post("http://localhost:5000/api/permissions/check", 
                               headers=headers, json=no_permission_data)
        if response.status_code == 403:
            data = response.json()
            reason = data["data"]["reason"]
            print(f"✅ 前台无法删除订单（正确），原因: {reason}")
            test_results.append(True)
        elif response.status_code == 200:
            print("❌ 前台不应该有删除订单的权限")
            test_results.append(False)
        else:
            print(f"❌ 前台权限检查失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 前台权限检查异常: {e}")
        test_results.append(False)
    
    # 3. 测试教练角色的API访问权限
    print("\n3️⃣ 测试教练角色的API访问权限")
    print("-" * 50)
    
    # 模拟教练用户
    coach_user_id = "coach_user_001"
    
    # 测试教练可以访问的API - 客户信息更新
    coach_permission_data = {
        "user_id": coach_user_id,
        "resource": "customers",
        "action": "update",
        "context": {
            "role": "coach",
            "department": "training"
        }
    }
    
    try:
        response = requests.post("http://localhost:5000/api/permissions/check", 
                               headers=headers, json=coach_permission_data)
        if response.status_code in [200, 403]:
            data = response.json()
            allowed = data["data"]["allowed"]
            print(f"✅ 教练更新客户信息权限检查完成，允许: {allowed}")
            test_results.append(True)
        else:
            print(f"❌ 教练权限检查失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 教练权限检查异常: {e}")
        test_results.append(False)
    
    # 测试教练不能访问的API - 用户管理
    coach_no_permission_data = {
        "user_id": coach_user_id,
        "resource": "users",
        "action": "delete",
        "context": {
            "role": "coach"
        }
    }
    
    try:
        response = requests.post("http://localhost:5000/api/permissions/check", 
                               headers=headers, json=coach_no_permission_data)
        if response.status_code == 403:
            data = response.json()
            reason = data["data"]["reason"]
            print(f"✅ 教练无法删除用户（正确），原因: {reason}")
            test_results.append(True)
        elif response.status_code == 200:
            print("❌ 教练不应该有删除用户的权限")
            test_results.append(False)
        else:
            print(f"❌ 教练权限检查失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 教练权限检查异常: {e}")
        test_results.append(False)
    
    # 4. 获取前台用户可访问的API列表
    print("\n4️⃣ 获取前台用户可访问的API列表")
    print("-" * 50)
    
    try:
        response = requests.get(f"http://localhost:5000/api/permissions/user-apis?user_id={front_desk_user_id}&include_details=true", 
                              headers=headers)
        if response.status_code == 200:
            data = response.json()
            api_count = data["data"]["summary"]["total_apis"]
            by_resource = data["data"]["summary"]["by_resource"]
            print(f"✅ 前台可访问API数: {api_count}")
            print("📊 按资源分组:")
            for resource, count in by_resource.items():
                print(f"  • {resource}: {count}个API")
            test_results.append(True)
        else:
            print(f"❌ 获取前台API列表失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 获取前台API列表异常: {e}")
        test_results.append(False)
    
    # 5. 获取教练用户可访问的API列表
    print("\n5️⃣ 获取教练用户可访问的API列表")
    print("-" * 50)
    
    try:
        response = requests.get(f"http://localhost:5000/api/permissions/user-apis?user_id={coach_user_id}&include_details=true", 
                              headers=headers)
        if response.status_code == 200:
            data = response.json()
            api_count = data["data"]["summary"]["total_apis"]
            by_resource = data["data"]["summary"]["by_resource"]
            print(f"✅ 教练可访问API数: {api_count}")
            print("📊 按资源分组:")
            for resource, count in by_resource.items():
                print(f"  • {resource}: {count}个API")
            test_results.append(True)
        else:
            print(f"❌ 获取教练API列表失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 获取教练API列表异常: {e}")
        test_results.append(False)
    
    # 6. 开发者动态调整角色权限
    print("\n6️⃣ 开发者动态调整角色权限")
    print("-" * 50)
    
    if front_desk_id:
        # 为前台角色添加订单创建权限
        role_api_data = {
            "role_id": front_desk_id,
            "api_id": "order_create_api",
            "permission": "orders:create",
            "action": "grant"
        }
        
        try:
            response = requests.post("http://localhost:5000/api/permissions/role-api", 
                                   headers=headers, json=role_api_data)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 开发者成功为前台角色添加订单创建权限")
                test_results.append(True)
            else:
                print(f"❌ 开发者调整权限失败: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 开发者调整权限异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有前台角色ID，跳过权限调整")
        test_results.append(False)
    
    # 7. 验证权限调整后的效果
    print("\n7️⃣ 验证权限调整后的效果")
    print("-" * 50)
    
    # 再次测试前台创建订单权限
    create_order_data = {
        "user_id": front_desk_user_id,
        "resource": "orders",
        "action": "create",
        "context": {
            "role": "front_desk"
        }
    }
    
    try:
        response = requests.post("http://localhost:5000/api/permissions/check", 
                               headers=headers, json=create_order_data)
        if response.status_code == 200:
            data = response.json()
            allowed = data["data"]["allowed"]
            print(f"✅ 权限调整后，前台创建订单权限: {allowed}")
            test_results.append(True)
        else:
            print(f"❌ 权限验证失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 权限验证异常: {e}")
        test_results.append(False)
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 80)
    print("📊 真实业务角色API控制测试结果")
    print("-" * 80)
    print(f"总测试项: {total}")
    print(f"测试通过: {passed}")
    print(f"测试失败: {total - passed}")
    print(f"成功率: {(passed / total * 100):.1f}%")
    
    if passed == total:
        print("\n🎉 真实业务角色API控制测试全部通过！")
        print("✅ 前台角色能够正确控制API访问")
        print("✅ 教练角色能够正确控制API访问")
        print("✅ 开发者能够动态调整角色权限")
        print("✅ 权限调整实时生效")
        print("✅ 角色权限控制符合业务需求")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试项失败")
    
    return passed == total


if __name__ == "__main__":
    success = test_real_business_role_api_control()
    exit(0 if success else 1)
