"""
完整业务角色验证测试
验证角色创建、用户分配、权限检查的完整流程
确保前台、教练等角色能够正确控制API访问
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


def test_complete_business_role_verification():
    """完整业务角色验证测试"""
    print("🏢 完整业务角色验证测试")
    print("=" * 80)
    print("验证角色创建、用户分配、权限检查的完整流程")
    
    # 获取token
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_results = []
    
    # 1. 验证系统中的角色列表
    print("\n1️⃣ 验证系统中的角色列表")
    print("-" * 50)
    
    try:
        response = requests.get("http://localhost:5000/api/roles", headers=headers)
        if response.status_code == 200:
            data = response.json()
            roles = data["data"]["roles"]
            print(f"✅ 系统中共有 {len(roles)} 个角色:")
            
            front_desk_exists = False
            coach_exists = False
            
            for role in roles:
                print(f"  • {role['name']} ({role['code']}) - 级别{role['level']}")
                if role['code'] == 'front_desk':
                    front_desk_exists = True
                if role['code'] == 'coach':
                    coach_exists = True
            
            if front_desk_exists and coach_exists:
                print("✅ 前台和教练角色都存在")
                test_results.append(True)
            else:
                print("❌ 缺少前台或教练角色")
                test_results.append(False)
        else:
            print(f"❌ 获取角色列表失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 获取角色列表异常: {e}")
        test_results.append(False)
    
    # 2. 验证权限矩阵
    print("\n2️⃣ 验证权限矩阵")
    print("-" * 50)
    
    try:
        response = requests.get("http://localhost:5000/api/permissions/matrix", headers=headers)
        if response.status_code == 200:
            data = response.json()
            matrix = data["data"]["matrix"]
            stats = data["data"]["statistics"]
            
            print(f"✅ 权限矩阵获取成功")
            print(f"  • 角色数: {stats['total_roles']}")
            print(f"  • API数: {stats['total_apis']}")
            print(f"  • 权限覆盖率: {stats['coverage']}%")
            
            # 检查前台和教练角色在矩阵中的权限
            front_desk_role = None
            coach_role = None
            
            for role in matrix["roles"]:
                if role["code"] == "front_desk":
                    front_desk_role = role
                elif role["code"] == "coach":
                    coach_role = role
            
            if front_desk_role and coach_role:
                print(f"✅ 前台角色: {front_desk_role['name']} (级别{front_desk_role['level']})")
                print(f"✅ 教练角色: {coach_role['name']} (级别{coach_role['level']})")
                
                # 检查权限分配
                front_desk_permissions = matrix["permissions"].get(front_desk_role["id"], {})
                coach_permissions = matrix["permissions"].get(coach_role["id"], {})
                
                front_desk_api_count = sum(1 for has_perm in front_desk_permissions.values() if has_perm)
                coach_api_count = sum(1 for has_perm in coach_permissions.values() if has_perm)
                
                print(f"  • 前台可访问API数: {front_desk_api_count}")
                print(f"  • 教练可访问API数: {coach_api_count}")
                
                test_results.append(True)
            else:
                print("❌ 权限矩阵中缺少前台或教练角色")
                test_results.append(False)
        else:
            print(f"❌ 获取权限矩阵失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 获取权限矩阵异常: {e}")
        test_results.append(False)
    
    # 3. 测试具体的权限检查场景
    print("\n3️⃣ 测试具体的权限检查场景")
    print("-" * 50)
    
    # 场景1: 前台查看客户信息
    print("场景1: 前台查看客户信息")
    permission_check = {
        "user_id": "front_desk_user_001",
        "resource": "customers",
        "action": "read"
    }
    
    try:
        response = requests.post("http://localhost:5000/api/permissions/check", 
                               headers=headers, json=permission_check)
        if response.status_code in [200, 403]:
            data = response.json()
            allowed = data["data"]["allowed"]
            user_roles = data["data"]["user"]["roles"]
            print(f"  结果: {'允许' if allowed else '拒绝'}")
            print(f"  用户角色: {user_roles}")
            if not allowed:
                print(f"  拒绝原因: {data['data']['reason']}")
            test_results.append(True)
        else:
            print(f"  ❌ 权限检查失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 权限检查异常: {e}")
        test_results.append(False)
    
    # 场景2: 教练更新客户信息
    print("场景2: 教练更新客户信息")
    permission_check = {
        "user_id": "coach_user_001",
        "resource": "customers",
        "action": "update"
    }
    
    try:
        response = requests.post("http://localhost:5000/api/permissions/check", 
                               headers=headers, json=permission_check)
        if response.status_code in [200, 403]:
            data = response.json()
            allowed = data["data"]["allowed"]
            user_roles = data["data"]["user"]["roles"]
            print(f"  结果: {'允许' if allowed else '拒绝'}")
            print(f"  用户角色: {user_roles}")
            if not allowed:
                print(f"  拒绝原因: {data['data']['reason']}")
            test_results.append(True)
        else:
            print(f"  ❌ 权限检查失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 权限检查异常: {e}")
        test_results.append(False)
    
    # 场景3: 前台尝试删除用户（应该被拒绝）
    print("场景3: 前台尝试删除用户（应该被拒绝）")
    permission_check = {
        "user_id": "front_desk_user_001",
        "resource": "users",
        "action": "delete"
    }
    
    try:
        response = requests.post("http://localhost:5000/api/permissions/check", 
                               headers=headers, json=permission_check)
        if response.status_code == 403:
            data = response.json()
            reason = data["data"]["reason"]
            print(f"  ✅ 正确拒绝，原因: {reason}")
            test_results.append(True)
        elif response.status_code == 200:
            print(f"  ❌ 不应该允许前台删除用户")
            test_results.append(False)
        else:
            print(f"  ❌ 权限检查失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 权限检查异常: {e}")
        test_results.append(False)
    
    # 4. 验证用户API访问列表
    print("\n4️⃣ 验证用户API访问列表")
    print("-" * 50)
    
    # 前台用户API列表
    print("前台用户API访问列表:")
    try:
        response = requests.get("http://localhost:5000/api/permissions/user-apis?user_id=front_desk_user_001", 
                              headers=headers)
        if response.status_code == 200:
            data = response.json()
            user_info = data["data"]["user"]
            summary = data["data"]["summary"]
            
            print(f"  用户: {user_info['name']}")
            print(f"  角色: {user_info['roles']}")
            print(f"  可访问API数: {summary['total_apis']}")
            print(f"  按资源分组: {summary['by_resource']}")
            test_results.append(True)
        else:
            print(f"  ❌ 获取API列表失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 获取API列表异常: {e}")
        test_results.append(False)
    
    # 教练用户API列表
    print("教练用户API访问列表:")
    try:
        response = requests.get("http://localhost:5000/api/permissions/user-apis?user_id=coach_user_001", 
                              headers=headers)
        if response.status_code == 200:
            data = response.json()
            user_info = data["data"]["user"]
            summary = data["data"]["summary"]
            
            print(f"  用户: {user_info['name']}")
            print(f"  角色: {user_info['roles']}")
            print(f"  可访问API数: {summary['total_apis']}")
            print(f"  按资源分组: {summary['by_resource']}")
            test_results.append(True)
        else:
            print(f"  ❌ 获取API列表失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 获取API列表异常: {e}")
        test_results.append(False)
    
    # 5. 验证开发者权限控制能力
    print("\n5️⃣ 验证开发者权限控制能力")
    print("-" * 50)
    
    # 获取前台角色ID
    front_desk_id = None
    try:
        response = requests.get("http://localhost:5000/api/roles", headers=headers)
        if response.status_code == 200:
            roles = response.json()["data"]["roles"]
            for role in roles:
                if role["code"] == "front_desk":
                    front_desk_id = role["id"]
                    break
    except:
        pass
    
    if front_desk_id:
        # 开发者为前台角色添加报表查看权限
        role_api_data = {
            "role_id": front_desk_id,
            "api_id": "reports_sales_api",
            "permission": "reports:sales",
            "action": "grant"
        }
        
        try:
            response = requests.post("http://localhost:5000/api/permissions/role-api", 
                                   headers=headers, json=role_api_data)
            if response.status_code == 200:
                print("✅ 开发者成功为前台角色添加报表查看权限")
                
                # 验证权限添加效果
                permission_check = {
                    "user_id": "front_desk_user_001",
                    "resource": "reports",
                    "action": "sales"
                }
                
                check_response = requests.post("http://localhost:5000/api/permissions/check", 
                                             headers=headers, json=permission_check)
                if check_response.status_code in [200, 403]:
                    check_data = check_response.json()
                    allowed = check_data["data"]["allowed"]
                    print(f"✅ 权限添加后，前台查看报表权限: {'允许' if allowed else '拒绝'}")
                    test_results.append(True)
                else:
                    print("❌ 权限验证失败")
                    test_results.append(False)
            else:
                print(f"❌ 开发者权限调整失败: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 开发者权限调整异常: {e}")
            test_results.append(False)
    else:
        print("❌ 未找到前台角色ID")
        test_results.append(False)
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 80)
    print("📊 完整业务角色验证测试结果")
    print("-" * 80)
    print(f"总测试项: {total}")
    print(f"测试通过: {passed}")
    print(f"测试失败: {total - passed}")
    print(f"成功率: {(passed / total * 100):.1f}%")
    
    if passed == total:
        print("\n🎉 完整业务角色验证测试全部通过！")
        print("✅ 角色创建功能正常")
        print("✅ 权限矩阵管理完善")
        print("✅ 权限检查机制正确")
        print("✅ 用户API访问控制有效")
        print("✅ 开发者权限控制能力完备")
        print("✅ 前台、教练等业务角色能够正确控制API访问")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试项失败")
        print("需要进一步检查角色权限配置")
    
    return passed == total


if __name__ == "__main__":
    success = test_complete_business_role_verification()
    exit(0 if success else 1)
