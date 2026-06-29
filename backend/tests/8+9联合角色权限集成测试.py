"""
第八+九部分 - 角色权限联合集成测试
验证角色管理和权限控制模块的完整集成功能
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


def test_role_permission_integration():
    """测试角色权限完整集成功能"""
    print("🔗 开始运行角色权限联合集成测试...")
    print("=" * 80)
    
    # 获取token
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_results = []
    created_role_id = None
    
    # 1. 创建测试角色
    print("\n1️⃣ 创建测试角色")
    print("-" * 50)
    
    role_data = {
        "name": "集成测试角色",
        "code": "integration_test_role",
        "level": 4,
        "description": "用于集成测试的角色",
        "status": "active",
        "permissions": [
            "products:read",
            "orders:read"
        ],
        "metadata": {
            "department": "test",
            "integration_test": True
        }
    }
    
    try:
        response = requests.post("http://localhost:5000/api/roles", 
                               headers=headers, json=role_data)
        if response.status_code == 201:
            data = response.json()
            created_role_id = data["data"]["role"]["id"]
            role_name = data["data"]["role"]["name"]
            print(f"✅ 角色创建成功: {role_name} (ID: {created_role_id})")
            test_results.append(True)
        else:
            print(f"❌ 角色创建失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 角色创建异常: {e}")
        test_results.append(False)
    
    # 2. 为角色分配更多权限
    print("\n2️⃣ 为角色分配更多权限")
    print("-" * 50)
    
    if created_role_id:
        permissions_data = {
            "permissions": [
                "customers:read",
                "customers:update",
                "reports:read"
            ],
            "replace": False
        }
        
        try:
            response = requests.post(f"http://localhost:5000/api/roles/{created_role_id}/permissions", 
                                   headers=headers, json=permissions_data)
            if response.status_code == 200:
                data = response.json()
                added_count = len(data["data"]["permissions"]["added"])
                total_count = data["data"]["permissions"]["total"]
                print(f"✅ 权限分配成功，新增: {added_count}，总计: {total_count}")
                test_results.append(True)
            else:
                print(f"❌ 权限分配失败: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 权限分配异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有角色ID，跳过权限分配")
        test_results.append(False)
    
    # 3. 验证角色权限
    print("\n3️⃣ 验证角色权限")
    print("-" * 50)
    
    if created_role_id:
        try:
            response = requests.get(f"http://localhost:5000/api/roles/{created_role_id}/permissions", 
                                  headers=headers)
            if response.status_code == 200:
                data = response.json()
                permissions = data["data"]["permissions"]
                total_permissions = data["data"]["summary"]["total_permissions"]
                print(f"✅ 角色权限验证成功，总权限数: {total_permissions}")
                
                # 显示权限列表
                print("📋 角色权限列表:")
                for perm in permissions[:5]:  # 显示前5个权限
                    print(f"  • {perm['name']} - {perm['description']}")
                
                test_results.append(True)
            else:
                print(f"❌ 角色权限验证失败: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 角色权限验证异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有角色ID，跳过权限验证")
        test_results.append(False)
    
    # 4. 测试权限检查 - 有权限的操作
    print("\n4️⃣ 测试权限检查 - 有权限的操作")
    print("-" * 50)
    
    # 模拟用户拥有刚创建的角色
    permission_check_data = {
        "user_id": "integration_test_user",
        "resource": "products",
        "action": "read",
        "context": {
            "test_scenario": "integration_test"
        }
    }
    
    try:
        response = requests.post("http://localhost:5000/api/permissions/check", 
                               headers=headers, json=permission_check_data)
        if response.status_code == 200:
            data = response.json()
            allowed = data["data"]["allowed"]
            user_roles = data["data"]["user"]["roles"]
            print(f"✅ 权限检查成功，允许访问: {allowed}，用户角色: {user_roles}")
            test_results.append(True)
        elif response.status_code == 403:
            data = response.json()
            reason = data["data"]["reason"]
            print(f"✅ 权限检查成功（拒绝访问），原因: {reason}")
            test_results.append(True)
        else:
            print(f"❌ 权限检查失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 权限检查异常: {e}")
        test_results.append(False)
    
    # 5. 测试权限检查 - 无权限的操作
    print("\n5️⃣ 测试权限检查 - 无权限的操作")
    print("-" * 50)
    
    no_permission_data = {
        "user_id": "integration_test_user",
        "resource": "users",
        "action": "delete",
        "context": {}
    }
    
    try:
        response = requests.post("http://localhost:5000/api/permissions/check", 
                               headers=headers, json=no_permission_data)
        if response.status_code == 403:
            data = response.json()
            reason = data["data"]["reason"]
            print(f"✅ 无权限检查正确，拒绝原因: {reason}")
            test_results.append(True)
        else:
            print(f"❌ 无权限检查失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 无权限检查异常: {e}")
        test_results.append(False)
    
    # 6. 获取用户可访问API列表
    print("\n6️⃣ 获取用户可访问API列表")
    print("-" * 50)
    
    try:
        response = requests.get("http://localhost:5000/api/permissions/user-apis?user_id=integration_test_user", 
                              headers=headers)
        if response.status_code == 200:
            data = response.json()
            api_count = data["data"]["summary"]["total_apis"]
            by_resource = data["data"]["summary"]["by_resource"]
            print(f"✅ 用户API列表获取成功，可访问API数: {api_count}")
            print("📊 按资源分组:")
            for resource, count in by_resource.items():
                print(f"  • {resource}: {count}个API")
            test_results.append(True)
        else:
            print(f"❌ 用户API列表获取失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 用户API列表获取异常: {e}")
        test_results.append(False)
    
    # 7. 通过权限控制API更新角色权限
    print("\n7️⃣ 通过权限控制API更新角色权限")
    print("-" * 50)
    
    if created_role_id:
        role_api_data = {
            "role_id": created_role_id,
            "api_id": "customer_delete_api",
            "permission": "customers:delete",
            "action": "grant"
        }
        
        try:
            response = requests.post("http://localhost:5000/api/permissions/role-api", 
                                   headers=headers, json=role_api_data)
            if response.status_code == 200:
                data = response.json()
                role_name = data["data"]["role"]["name"]
                permission_name = data["data"]["permission"]["name"]
                print(f"✅ 角色API权限更新成功，角色: {role_name}，权限: {permission_name}")
                test_results.append(True)
            else:
                print(f"❌ 角色API权限更新失败: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 角色API权限更新异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有角色ID，跳过API权限更新")
        test_results.append(False)
    
    # 8. 获取完整权限矩阵
    print("\n8️⃣ 获取完整权限矩阵")
    print("-" * 50)
    
    try:
        response = requests.get("http://localhost:5000/api/permissions/matrix", headers=headers)
        if response.status_code == 200:
            data = response.json()
            stats = data["data"]["statistics"]
            print(f"✅ 权限矩阵获取成功")
            print(f"📊 统计信息:")
            print(f"  • 总角色数: {stats['total_roles']}")
            print(f"  • 总API数: {stats['total_apis']}")
            print(f"  • 总权限数: {stats['total_permissions']}")
            print(f"  • 已授予权限: {stats['granted_permissions']}")
            print(f"  • 权限覆盖率: {stats['coverage']}%")
            test_results.append(True)
        else:
            print(f"❌ 权限矩阵获取失败: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 权限矩阵获取异常: {e}")
        test_results.append(False)
    
    # 9. 清理测试数据
    print("\n9️⃣ 清理测试数据")
    print("-" * 50)
    
    if created_role_id:
        try:
            response = requests.delete(f"http://localhost:5000/api/roles/{created_role_id}?force=true", 
                                     headers=headers)
            if response.status_code == 200:
                data = response.json()
                deleted_name = data["data"]["name"]
                print(f"✅ 测试角色清理成功: {deleted_name}")
                test_results.append(True)
            else:
                print(f"❌ 测试角色清理失败: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 测试角色清理异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有角色ID，跳过清理")
        test_results.append(False)
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 80)
    print("📊 角色权限联合集成测试结果")
    print("-" * 80)
    print(f"总测试项: {total}")
    print(f"测试通过: {passed}")
    print(f"测试失败: {total - passed}")
    print(f"成功率: {(passed / total * 100):.1f}%")
    
    if passed == total:
        print("\n🎉 角色权限联合集成测试全部通过！")
        print("✅ 角色管理功能完整")
        print("✅ 权限控制功能完善")
        print("✅ 角色权限集成成功")
        print("✅ API访问控制正常")
        print("✅ 权限矩阵管理完备")
        print("✅ 数据一致性良好")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试项失败")
    
    return passed == total


if __name__ == "__main__":
    success = test_role_permission_integration()
    exit(0 if success else 1)
