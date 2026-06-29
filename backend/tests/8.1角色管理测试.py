"""
第八部分 - 角色管理模块测试
验证所有8个API端点功能和动态数据库生成
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


def test_role_management():
    """测试角色管理功能"""
    print("🚀 开始运行角色管理模块测试...")
    print("=" * 60)
    
    # 获取token
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_results = []
    role_id = None
    permission_id = None
    
    # 1. 测试创建新的用户角色
    print("\n1️⃣ 测试创建新的用户角色 (POST /api/roles)")
    print("-" * 50)
    
    role_data = {
        "name": "测试角色",
        "code": "test_role",
        "level": 5,
        "description": "用于测试的角色",
        "status": "active",
        "permissions": [
            "products:read",
            "products:create",
            "orders:read"
        ],
        "metadata": {
            "department": "test",
            "test_role": True
        }
    }
    
    try:
        response = requests.post("http://localhost:5000/api/roles", 
                               headers=headers, json=role_data)
        if response.status_code == 201:
            data = response.json()
            role_id = data["data"]["role"]["id"]
            print(f"✅ 创建成功，角色ID: {role_id}")
            test_results.append(True)
        else:
            print(f"❌ 创建失败: {response.status_code} - {response.text}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 创建异常: {e}")
        test_results.append(False)
    
    # 2. 测试获取所有角色列表
    print("\n2️⃣ 测试获取所有角色列表 (GET /api/roles)")
    print("-" * 50)
    
    try:
        response = requests.get("http://localhost:5000/api/roles?page=1&limit=10", 
                              headers=headers)
        if response.status_code == 200:
            data = response.json()
            roles_count = len(data["data"]["roles"])
            total = data["data"]["pagination"]["total"]
            print(f"✅ 获取成功，当前页角色数: {roles_count}，总数: {total}")
            test_results.append(True)
        else:
            print(f"❌ 获取失败: {response.status_code} - {response.text}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 获取异常: {e}")
        test_results.append(False)
    
    # 3. 测试获取特定角色详情
    print("\n3️⃣ 测试获取特定角色详情 (GET /api/roles/{role_id})")
    print("-" * 50)
    
    if role_id:
        try:
            response = requests.get(f"http://localhost:5000/api/roles/{role_id}?include_permissions=true", 
                                  headers=headers)
            if response.status_code == 200:
                data = response.json()
                role_name = data["data"]["role"]["name"]
                permission_count = data["data"]["role"]["permission_count"]
                print(f"✅ 获取成功，角色名称: {role_name}，权限数: {permission_count}")
                test_results.append(True)
            else:
                print(f"❌ 获取失败: {response.status_code} - {response.text}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 获取异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有角色ID，跳过测试")
        test_results.append(False)
    
    # 4. 测试更新角色信息
    print("\n4️⃣ 测试更新角色信息 (PUT /api/roles/{role_id})")
    print("-" * 50)
    
    if role_id:
        update_data = {
            "name": "更新后的测试角色",
            "description": "更新后的角色描述",
            "level": 6
        }
        
        try:
            response = requests.put(f"http://localhost:5000/api/roles/{role_id}", 
                                  headers=headers, json=update_data)
            if response.status_code == 200:
                data = response.json()
                updated_name = data["data"]["role"]["name"]
                updated_level = data["data"]["role"]["level"]
                print(f"✅ 更新成功，新名称: {updated_name}，新级别: {updated_level}")
                test_results.append(True)
            else:
                print(f"❌ 更新失败: {response.status_code} - {response.text}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 更新异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有角色ID，跳过测试")
        test_results.append(False)
    
    # 5. 测试为角色分配权限
    print("\n5️⃣ 测试为角色分配权限 (POST /api/roles/{role_id}/permissions)")
    print("-" * 50)
    
    if role_id:
        permissions_data = {
            "permissions": [
                "customers:read",
                "customers:update",
                "reports:read"
            ],
            "replace": False
        }
        
        try:
            response = requests.post(f"http://localhost:5000/api/roles/{role_id}/permissions", 
                                   headers=headers, json=permissions_data)
            if response.status_code == 200:
                data = response.json()
                added_count = len(data["data"]["permissions"]["added"])
                total_count = data["data"]["permissions"]["total"]
                print(f"✅ 分配成功，新增权限: {added_count}，总权限: {total_count}")
                test_results.append(True)
            else:
                print(f"❌ 分配失败: {response.status_code} - {response.text}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 分配异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有角色ID，跳过测试")
        test_results.append(False)
    
    # 6. 测试获取角色权限列表
    print("\n6️⃣ 测试获取角色权限列表 (GET /api/roles/{role_id}/permissions)")
    print("-" * 50)
    
    if role_id:
        try:
            response = requests.get(f"http://localhost:5000/api/roles/{role_id}/permissions", 
                                  headers=headers)
            if response.status_code == 200:
                data = response.json()
                permissions = data["data"]["permissions"]
                total_permissions = data["data"]["summary"]["total_permissions"]
                if permissions:
                    permission_id = permissions[0]["id"]  # 保存第一个权限ID用于删除测试
                print(f"✅ 获取成功，权限数: {total_permissions}")
                test_results.append(True)
            else:
                print(f"❌ 获取失败: {response.status_code} - {response.text}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 获取异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有角色ID，跳过测试")
        test_results.append(False)
    
    # 7. 测试移除角色权限
    print("\n7️⃣ 测试移除角色权限 (DELETE /api/roles/{role_id}/permissions/{permission_id})")
    print("-" * 50)
    
    if role_id and permission_id:
        try:
            response = requests.delete(f"http://localhost:5000/api/roles/{role_id}/permissions/{permission_id}", 
                                     headers=headers)
            if response.status_code == 200:
                data = response.json()
                removed_permission = data["data"]["permission"]["name"]
                print(f"✅ 移除成功，移除权限: {removed_permission}")
                test_results.append(True)
            else:
                print(f"❌ 移除失败: {response.status_code} - {response.text}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 移除异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有角色ID或权限ID，跳过测试")
        test_results.append(False)
    
    # 8. 测试删除角色
    print("\n8️⃣ 测试删除角色 (DELETE /api/roles/{role_id})")
    print("-" * 50)
    
    if role_id:
        try:
            response = requests.delete(f"http://localhost:5000/api/roles/{role_id}?force=true", 
                                     headers=headers)
            if response.status_code == 200:
                data = response.json()
                deleted_name = data["data"]["name"]
                print(f"✅ 删除成功，删除角色: {deleted_name}")
                test_results.append(True)
            else:
                print(f"❌ 删除失败: {response.status_code} - {response.text}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 删除异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有角色ID，跳过测试")
        test_results.append(False)
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 60)
    print("📊 第八部分角色管理模块测试结果")
    print("-" * 60)
    print(f"总API端点: {total}")
    print(f"测试通过: {passed}")
    print(f"测试失败: {total - passed}")
    print(f"成功率: {(passed / total * 100):.1f}%")
    
    if passed == total:
        print("🎉 所有8个API端点测试全部通过！")
        print("✅ 动态数据库生成功能正常")
        print("✅ 角色权限管理功能完整")
    else:
        print(f"⚠️  有 {total - passed} 个API端点测试失败")
    
    return passed == total


if __name__ == "__main__":
    success = test_role_management()
    exit(0 if success else 1)
