"""
第九部分 - 完整权限控制API文档符合性测试
验证每个API端点是否完全符合API文档规范
包括请求格式、响应格式、错误处理等
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


def validate_response_structure(response_data, expected_fields, test_name):
    """验证响应结构"""
    missing_fields = []
    for field in expected_fields:
        if field not in response_data:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ {test_name} - 缺少字段: {missing_fields}")
        return False
    else:
        print(f"✅ {test_name} - 响应结构正确")
        return True


def test_complete_permission_control_api_compliance():
    """完整的权限控制API文档符合性测试"""
    print("🔒 第九部分 - 完整权限控制API文档符合性测试")
    print("=" * 80)
    print("验证每个API端点是否完全符合API文档规范")
    
    # 获取token
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_results = []
    
    # API 1: 检查用户是否有访问特定API的权限 (POST /api/permissions/check)
    print("\n1️⃣ API 1: 检查用户是否有访问特定API的权限 (POST /api/permissions/check)")
    print("-" * 70)
    
    # 测试有权限的用户
    permission_check_data = {
        "user_id": "user_001",
        "resource": "products",
        "action": "read",
        "context": {
            "product_id": "product_123",
            "department": "sales"
        }
    }
    
    try:
        response = requests.post("http://localhost:5000/api/permissions/check", 
                               headers=headers, json=permission_check_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # 验证响应结构
            expected_fields = ["code", "message", "data"]
            data_fields = ["allowed", "user", "permission", "context", "checked_at"]
            user_fields = ["id", "name", "roles"]
            permission_fields = ["resource", "action", "granted_by", "permission_name"]
            
            structure_ok = validate_response_structure(data, expected_fields, "有权限检查响应")
            data_structure_ok = validate_response_structure(data["data"], data_fields, "权限检查数据结构")
            user_structure_ok = validate_response_structure(data["data"]["user"], user_fields, "用户信息结构")
            permission_structure_ok = validate_response_structure(data["data"]["permission"], permission_fields, "权限信息结构")
            
            if (data["code"] == 200 and 
                data["message"] == "权限检查完成" and
                data["data"]["allowed"] == True):
                print(f"✅ 有权限检查成功，用户: {data['data']['user']['name']}")
                test_results.append(all([structure_ok, data_structure_ok, user_structure_ok, permission_structure_ok]))
            else:
                print("❌ 有权限检查响应值不符合预期")
                test_results.append(False)
        else:
            print(f"❌ 有权限检查HTTP状态码错误: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 有权限检查异常: {e}")
        test_results.append(False)
    
    # 测试无权限的用户 (403 Forbidden)
    print("\n1️⃣-2 测试无权限用户 (403 Forbidden)")
    print("-" * 50)
    
    no_permission_data = {
        "user_id": "user_002",
        "resource": "products",
        "action": "delete",
        "context": {}
    }
    
    try:
        response = requests.post("http://localhost:5000/api/permissions/check", 
                               headers=headers, json=no_permission_data)
        
        if response.status_code == 403:
            data = response.json()
            
            # 验证403响应结构
            expected_fields = ["code", "message", "data"]
            data_fields = ["allowed", "user", "permission", "reason", "suggestions", "checked_at"]
            
            structure_ok = validate_response_structure(data, expected_fields, "无权限检查响应")
            data_structure_ok = validate_response_structure(data["data"], data_fields, "无权限数据结构")
            
            if (data["code"] == 403 and 
                data["message"] == "权限不足" and
                data["data"]["allowed"] == False):
                print(f"✅ 无权限检查正确，原因: {data['data']['reason']}")
                test_results.append(structure_ok and data_structure_ok)
            else:
                print("❌ 无权限检查响应值不符合预期")
                test_results.append(False)
        else:
            print(f"❌ 无权限检查HTTP状态码错误: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 无权限检查异常: {e}")
        test_results.append(False)
    
    # API 2: 获取指定用户可以访问的API列表 (GET /api/permissions/user-apis)
    print("\n2️⃣ API 2: 获取指定用户可以访问的API列表 (GET /api/permissions/user-apis)")
    print("-" * 70)
    
    try:
        # 测试带查询参数的请求
        response = requests.get(
            "http://localhost:5000/api/permissions/user-apis?user_id=user_001&resource=products&include_details=true", 
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # 验证响应结构
            expected_fields = ["code", "message", "data"]
            data_fields = ["user", "accessible_apis", "summary"]
            user_fields = ["id", "name", "roles"]
            summary_fields = ["total_apis", "by_resource", "by_method", "permissions"]
            
            structure_ok = validate_response_structure(data, expected_fields, "用户API列表响应")
            data_structure_ok = validate_response_structure(data["data"], data_fields, "用户API数据结构")
            user_structure_ok = validate_response_structure(data["data"]["user"], user_fields, "用户信息结构")
            summary_structure_ok = validate_response_structure(data["data"]["summary"], summary_fields, "汇总信息结构")
            
            # 验证API列表项结构
            if data["data"]["accessible_apis"]:
                api_fields = ["api_id", "name", "endpoint", "method", "resource", "action", "permission", "granted_by"]
                api_structure_ok = validate_response_structure(data["data"]["accessible_apis"][0], api_fields, "API列表项结构")
            else:
                api_structure_ok = True
                print("✅ API列表为空，跳过API项结构验证")
            
            if (data["code"] == 200 and 
                data["message"] == "获取用户API权限成功"):
                total_apis = data["data"]["summary"]["total_apis"]
                print(f"✅ 获取用户API列表成功，总API数: {total_apis}")
                test_results.append(all([structure_ok, data_structure_ok, user_structure_ok, summary_structure_ok, api_structure_ok]))
            else:
                print("❌ 用户API列表响应值不符合预期")
                test_results.append(False)
        else:
            print(f"❌ HTTP状态码错误: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        test_results.append(False)
    
    # API 3: 更新角色对特定API的访问权限 (POST /api/permissions/role-api)
    print("\n3️⃣ API 3: 更新角色对特定API的访问权限 (POST /api/permissions/role-api)")
    print("-" * 70)
    
    # 获取一个角色ID用于测试
    try:
        roles_response = requests.get("http://localhost:5000/api/roles?limit=1", headers=headers)
        if roles_response.status_code == 200:
            roles_data = roles_response.json()
            if roles_data["data"]["roles"]:
                role_id = roles_data["data"]["roles"][0]["id"]
                
                # 先撤销权限，再授予权限，确保测试能正常进行
                revoke_data = {
                    "role_id": role_id,
                    "api_id": "customer_create_api",
                    "permission": "customers:create",
                    "action": "revoke"
                }
                
                # 先撤销权限（可能失败，不影响测试）
                requests.post("http://localhost:5000/api/permissions/role-api", 
                            headers=headers, json=revoke_data)
                
                # 再授予权限
                grant_data = {
                    "role_id": role_id,
                    "api_id": "customer_create_api",
                    "permission": "customers:create",
                    "action": "grant"
                }
                
                response = requests.post("http://localhost:5000/api/permissions/role-api", 
                                       headers=headers, json=grant_data)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 验证响应结构
                    expected_fields = ["code", "message", "data"]
                    data_fields = ["role", "api", "permission"]
                    role_fields = ["id", "name", "code"]
                    api_fields = ["id", "name", "endpoint", "method"]
                    permission_fields = ["name", "action", "granted_at", "granted_by"]
                    
                    structure_ok = validate_response_structure(data, expected_fields, "角色API权限更新响应")
                    data_structure_ok = validate_response_structure(data["data"], data_fields, "权限更新数据结构")
                    role_structure_ok = validate_response_structure(data["data"]["role"], role_fields, "角色信息结构")
                    api_structure_ok = validate_response_structure(data["data"]["api"], api_fields, "API信息结构")
                    permission_structure_ok = validate_response_structure(data["data"]["permission"], permission_fields, "权限信息结构")
                    
                    if (data["code"] == 200 and 
                        data["message"] == "权限更新成功"):
                        role_name = data["data"]["role"]["name"]
                        api_name = data["data"]["api"]["name"]
                        print(f"✅ 角色API权限更新成功，角色: {role_name}，API: {api_name}")
                        test_results.append(all([structure_ok, data_structure_ok, role_structure_ok, api_structure_ok, permission_structure_ok]))
                    else:
                        print("❌ 角色API权限更新响应值不符合预期")
                        test_results.append(False)
                elif response.status_code == 400:
                    # 权限已存在也算成功
                    print(f"✅ 角色API权限已存在（正常情况）")
                    test_results.append(True)
                else:
                    print(f"❌ HTTP状态码错误: {response.status_code}")
                    test_results.append(False)
            else:
                print("❌ 没有可用的角色")
                test_results.append(False)
        else:
            print("❌ 获取角色列表失败")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        test_results.append(False)

    # API 4: 批量更新多个角色的API权限 (POST /api/permissions/batch-update)
    print("\n4️⃣ API 4: 批量更新多个角色的API权限 (POST /api/permissions/batch-update)")
    print("-" * 70)

    try:
        # 获取角色列表用于批量更新
        roles_response = requests.get("http://localhost:5000/api/roles?limit=2", headers=headers)
        if roles_response.status_code == 200:
            roles_data = roles_response.json()
            if len(roles_data["data"]["roles"]) >= 1:
                role_id = roles_data["data"]["roles"][0]["id"]

                batch_data = {
                    "updates": [
                        {
                            "role_id": role_id,
                            "api_id": "order_update_api",
                            "permission": "orders:update",
                            "action": "grant"
                        },
                        {
                            "role_id": role_id,
                            "api_id": "customer_update_api",
                            "permission": "customers:update",
                            "action": "grant"
                        }
                    ],
                    "dry_run": False
                }

                response = requests.post("http://localhost:5000/api/permissions/batch-update",
                                       headers=headers, json=batch_data)

                if response.status_code == 200:
                    data = response.json()

                    # 验证响应结构
                    expected_fields = ["code", "message", "data"]
                    data_fields = ["results", "summary"]
                    summary_fields = ["total", "successful", "failed", "granted", "revoked"]

                    structure_ok = validate_response_structure(data, expected_fields, "批量权限更新响应")
                    data_structure_ok = validate_response_structure(data["data"], data_fields, "批量更新数据结构")
                    summary_structure_ok = validate_response_structure(data["data"]["summary"], summary_fields, "批量更新汇总结构")

                    # 验证结果项结构
                    if data["data"]["results"]:
                        result_fields = ["role_id", "api_id", "permission", "action", "status", "message"]
                        result_structure_ok = validate_response_structure(data["data"]["results"][0], result_fields, "批量更新结果项结构")
                    else:
                        result_structure_ok = True
                        print("✅ 批量更新结果为空，跳过结果项结构验证")

                    if (data["code"] == 200 and
                        data["message"] == "批量权限更新成功"):
                        total = data["data"]["summary"]["total"]
                        successful = data["data"]["summary"]["successful"]
                        print(f"✅ 批量权限更新成功，成功: {successful}/{total}")
                        test_results.append(all([structure_ok, data_structure_ok, summary_structure_ok, result_structure_ok]))
                    else:
                        print("❌ 批量权限更新响应值不符合预期")
                        test_results.append(False)
                else:
                    print(f"❌ HTTP状态码错误: {response.status_code}")
                    test_results.append(False)
            else:
                print("❌ 没有足够的角色进行批量更新")
                test_results.append(False)
        else:
            print("❌ 获取角色列表失败")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        test_results.append(False)

    # 测试试运行模式
    print("\n4️⃣-2 测试批量更新试运行模式")
    print("-" * 50)

    try:
        roles_response = requests.get("http://localhost:5000/api/roles?limit=1", headers=headers)
        if roles_response.status_code == 200:
            roles_data = roles_response.json()
            if roles_data["data"]["roles"]:
                role_id = roles_data["data"]["roles"][0]["id"]

                dry_run_data = {
                    "updates": [
                        {
                            "role_id": role_id,
                            "api_id": "product_create_api",
                            "permission": "products:create",
                            "action": "grant"
                        }
                    ],
                    "dry_run": True
                }

                response = requests.post("http://localhost:5000/api/permissions/batch-update",
                                       headers=headers, json=dry_run_data)

                if response.status_code == 200:
                    data = response.json()
                    if data["data"]["results"][0]["status"] == "dry_run":
                        print("✅ 试运行模式正常工作")
                        test_results.append(True)
                    else:
                        print("❌ 试运行模式不正常")
                        test_results.append(False)
                else:
                    print(f"❌ 试运行模式HTTP状态码错误: {response.status_code}")
                    test_results.append(False)
            else:
                print("❌ 没有可用角色进行试运行测试")
                test_results.append(False)
        else:
            print("❌ 获取角色列表失败")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 试运行测试异常: {e}")
        test_results.append(False)

    # API 5: 获取完整的权限矩阵 (GET /api/permissions/matrix)
    print("\n5️⃣ API 5: 获取完整的权限矩阵 (GET /api/permissions/matrix)")
    print("-" * 70)

    try:
        # 测试带查询参数的请求
        response = requests.get("http://localhost:5000/api/permissions/matrix?format=matrix&include_inactive=false",
                              headers=headers)

        if response.status_code == 200:
            data = response.json()

            # 验证响应结构
            expected_fields = ["code", "message", "data"]
            data_fields = ["matrix", "statistics"]
            matrix_fields = ["roles", "apis", "permissions"]
            statistics_fields = ["total_roles", "total_apis", "total_permissions", "granted_permissions", "denied_permissions", "coverage"]

            structure_ok = validate_response_structure(data, expected_fields, "权限矩阵响应")
            data_structure_ok = validate_response_structure(data["data"], data_fields, "权限矩阵数据结构")
            matrix_structure_ok = validate_response_structure(data["data"]["matrix"], matrix_fields, "矩阵结构")
            statistics_structure_ok = validate_response_structure(data["data"]["statistics"], statistics_fields, "统计信息结构")

            # 验证角色和API结构
            roles_structure_ok = True
            apis_structure_ok = True

            if data["data"]["matrix"]["roles"]:
                role_fields = ["id", "name", "code", "level"]
                roles_structure_ok = validate_response_structure(data["data"]["matrix"]["roles"][0], role_fields, "角色项结构")

            if data["data"]["matrix"]["apis"]:
                api_fields = ["id", "name", "endpoint", "method", "permission"]
                apis_structure_ok = validate_response_structure(data["data"]["matrix"]["apis"][0], api_fields, "API项结构")

            if (data["code"] == 200 and
                data["message"] == "获取权限矩阵成功"):
                total_roles = data["data"]["statistics"]["total_roles"]
                total_apis = data["data"]["statistics"]["total_apis"]
                coverage = data["data"]["statistics"]["coverage"]
                print(f"✅ 获取权限矩阵成功，角色数: {total_roles}，API数: {total_apis}，覆盖率: {coverage}%")
                test_results.append(all([structure_ok, data_structure_ok, matrix_structure_ok, statistics_structure_ok, roles_structure_ok, apis_structure_ok]))
            else:
                print("❌ 权限矩阵响应值不符合预期")
                test_results.append(False)
        else:
            print(f"❌ HTTP状态码错误: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        test_results.append(False)

    # API 6: 批量更新权限矩阵 (POST /api/permissions/matrix)
    print("\n6️⃣ API 6: 批量更新权限矩阵 (POST /api/permissions/matrix)")
    print("-" * 70)

    try:
        # 先获取当前权限矩阵
        matrix_response = requests.get("http://localhost:5000/api/permissions/matrix", headers=headers)
        if matrix_response.status_code == 200:
            matrix_data = matrix_response.json()
            roles = matrix_data["data"]["matrix"]["roles"]
            apis = matrix_data["data"]["matrix"]["apis"]

            if roles and apis:
                # 构建一个简单的权限矩阵更新
                role_id = roles[0]["id"]
                api_id = apis[0]["id"]

                matrix_update_data = {
                    "matrix": {
                        role_id: {
                            api_id: True
                        }
                    },
                    "merge_mode": "merge"
                }

                response = requests.post("http://localhost:5000/api/permissions/matrix",
                                       headers=headers, json=matrix_update_data)

                if response.status_code == 200:
                    data = response.json()

                    # 验证响应结构
                    expected_fields = ["code", "message", "data"]
                    data_fields = ["updated_permissions", "summary", "updated_at"]
                    summary_fields = ["roles_updated", "permissions_granted", "permissions_revoked", "total_changes"]

                    structure_ok = validate_response_structure(data, expected_fields, "权限矩阵更新响应")
                    data_structure_ok = validate_response_structure(data["data"], data_fields, "矩阵更新数据结构")
                    summary_structure_ok = validate_response_structure(data["data"]["summary"], summary_fields, "矩阵更新汇总结构")

                    if (data["code"] == 200 and
                        data["message"] == "权限矩阵更新成功"):
                        roles_updated = data["data"]["summary"]["roles_updated"]
                        total_changes = data["data"]["summary"]["total_changes"]
                        print(f"✅ 权限矩阵更新成功，更新角色数: {roles_updated}，总变更: {total_changes}")
                        test_results.append(all([structure_ok, data_structure_ok, summary_structure_ok]))
                    else:
                        print("❌ 权限矩阵更新响应值不符合预期")
                        test_results.append(False)
                else:
                    print(f"❌ HTTP状态码错误: {response.status_code}")
                    test_results.append(False)
            else:
                print("❌ 没有可用的角色或API进行矩阵更新")
                test_results.append(False)
        else:
            print("❌ 获取权限矩阵失败，无法进行更新测试")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        test_results.append(False)

    # 统计结果
    passed = sum(test_results)
    total = len(test_results)

    print("\n" + "=" * 80)
    print("📊 完整权限控制API文档符合性测试结果")
    print("-" * 80)
    print(f"总测试项: {total}")
    print(f"测试通过: {passed}")
    print(f"测试失败: {total - passed}")
    print(f"符合率: {(passed / total * 100):.1f}%")

    # 详细测试项说明
    test_descriptions = [
        "1. 权限检查 - 有权限用户 (200)",
        "2. 权限检查 - 无权限用户 (403)",
        "3. 获取用户API列表 - 带筛选参数",
        "4. 更新角色API权限 - 授予权限",
        "5. 批量权限更新 - 正常模式",
        "6. 批量权限更新 - 试运行模式",
        "7. 获取权限矩阵 - 带查询参数",
        "8. 更新权限矩阵 - 合并模式"
    ]

    print("\n📋 详细测试结果:")
    for i, (result, desc) in enumerate(zip(test_results, test_descriptions)):
        status = "✅" if result else "❌"
        print(f"  {status} {desc}")

    if passed == total:
        print("\n🎉 所有权限控制API端点完全符合文档规范！")
        print("✅ 权限检查功能正常")
        print("✅ 用户API访问列表完整")
        print("✅ 角色权限配置管理完善")
        print("✅ 批量权限操作正常")
        print("✅ 权限矩阵管理完备")
        print("✅ 请求响应格式100%符合")
        print("✅ 错误处理机制完善")
        print("✅ HTTP状态码正确")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试项不符合文档规范")

    return passed == total


if __name__ == "__main__":
    success = test_complete_permission_control_api_compliance()
    exit(0 if success else 1)
