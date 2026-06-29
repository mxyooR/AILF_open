"""
第八部分 - 完整API文档符合性测试
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


def test_complete_api_documentation_compliance():
    """完整的API文档符合性测试"""
    print("📋 第八部分 - 完整API文档符合性测试")
    print("=" * 80)
    print("验证每个API端点是否完全符合API文档规范")
    
    # 获取token
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_results = []
    created_role_id = None
    permission_id = None
    
    # API 1: 创建新的用户角色 (POST /api/roles)
    print("\n1️⃣ API 1: 创建新的用户角色 (POST /api/roles)")
    print("-" * 70)
    
    # 测试完整的请求格式
    role_data = {
        "name": "销售经理",
        "code": "sales_manager_test",
        "level": 6,
        "description": "负责销售团队管理和业务决策的角色",
        "status": "active",
        "permissions": [
            "products:read",
            "products:create",
            "products:update",
            "orders:*",
            "customers:*",
            "reports:sales"
        ],
        "metadata": {
            "department": "sales",
            "can_approve_discount": True,
            "max_discount_rate": 0.2
        }
    }
    
    try:
        response = requests.post("http://localhost:5000/api/roles", 
                               headers=headers, json=role_data)
        
        if response.status_code == 201:
            data = response.json()
            
            # 验证响应结构
            expected_fields = ["code", "message", "data"]
            role_fields = ["id", "name", "code", "level", "description", "status", 
                          "user_count", "permissions", "metadata", "created_at", "updated_at"]
            
            structure_ok = validate_response_structure(data, expected_fields, "创建角色响应")
            role_structure_ok = validate_response_structure(data["data"]["role"], role_fields, "角色数据结构")
            
            # 验证响应值
            if (data["code"] == 201 and 
                data["message"] == "角色创建成功" and
                data["data"]["role"]["name"] == role_data["name"] and
                data["data"]["role"]["code"] == role_data["code"] and
                data["data"]["role"]["level"] == role_data["level"]):
                
                created_role_id = data["data"]["role"]["id"]
                print(f"✅ 创建角色成功，ID: {created_role_id}")
                test_results.append(structure_ok and role_structure_ok)
            else:
                print("❌ 响应值不符合预期")
                test_results.append(False)
        else:
            print(f"❌ HTTP状态码错误: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        test_results.append(False)
    
    # 测试角色代码冲突 (409 Conflict)
    print("\n1️⃣-2 测试角色代码冲突 (409 Conflict)")
    print("-" * 50)
    
    try:
        # 使用相同的角色代码
        conflict_response = requests.post("http://localhost:5000/api/roles", 
                                        headers=headers, json=role_data)
        
        if conflict_response.status_code == 409:
            conflict_data = conflict_response.json()
            expected_fields = ["code", "message", "data"]
            error_fields = ["error", "details", "existing_role"]
            
            structure_ok = validate_response_structure(conflict_data, expected_fields, "冲突响应")
            error_structure_ok = validate_response_structure(conflict_data["data"], error_fields, "错误数据结构")
            
            if (conflict_data["code"] == 409 and 
                conflict_data["message"] == "角色代码已存在" and
                conflict_data["data"]["error"] == "role_code_exists"):
                print("✅ 角色代码冲突处理正确")
                test_results.append(structure_ok and error_structure_ok)
            else:
                print("❌ 冲突响应值不符合预期")
                test_results.append(False)
        else:
            print(f"❌ 冲突HTTP状态码错误: {conflict_response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 冲突测试异常: {e}")
        test_results.append(False)
    
    # API 2: 获取所有角色列表 (GET /api/roles)
    print("\n2️⃣ API 2: 获取所有角色列表 (GET /api/roles)")
    print("-" * 70)
    
    try:
        # 测试带查询参数的请求
        response = requests.get(
            "http://localhost:5000/api/roles?status=active&level_min=3&sort=level&page=1&limit=20", 
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # 验证响应结构
            expected_fields = ["code", "message", "data"]
            data_fields = ["roles", "pagination", "summary"]
            pagination_fields = ["page", "limit", "total", "pages", "has_next", "has_prev"]
            summary_fields = ["total_roles", "active_roles", "inactive_roles", "total_users", "avg_permissions_per_role"]
            
            structure_ok = validate_response_structure(data, expected_fields, "角色列表响应")
            data_structure_ok = validate_response_structure(data["data"], data_fields, "数据结构")
            pagination_ok = validate_response_structure(data["data"]["pagination"], pagination_fields, "分页结构")
            summary_ok = validate_response_structure(data["data"]["summary"], summary_fields, "汇总结构")
            
            # 验证角色列表项结构
            if data["data"]["roles"]:
                role_item_fields = ["id", "name", "code", "level", "description", "status", 
                                  "user_count", "permission_count", "created_at", "updated_at"]
                role_item_ok = validate_response_structure(data["data"]["roles"][0], role_item_fields, "角色列表项结构")
            else:
                role_item_ok = True
                print("✅ 角色列表为空，跳过列表项结构验证")
            
            if (data["code"] == 200 and 
                data["message"] == "获取角色列表成功"):
                print(f"✅ 获取角色列表成功，总数: {data['data']['pagination']['total']}")
                test_results.append(all([structure_ok, data_structure_ok, pagination_ok, summary_ok, role_item_ok]))
            else:
                print("❌ 响应值不符合预期")
                test_results.append(False)
        else:
            print(f"❌ HTTP状态码错误: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        test_results.append(False)
    
    # API 3: 获取特定角色详情 (GET /api/roles/{role_id})
    print("\n3️⃣ API 3: 获取特定角色详情 (GET /api/roles/{role_id})")
    print("-" * 70)
    
    if created_role_id:
        try:
            # 测试包含用户和权限信息的请求
            response = requests.get(
                f"http://localhost:5000/api/roles/{created_role_id}?include_users=true&include_permissions=true", 
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # 验证响应结构
                expected_fields = ["code", "message", "data"]
                role_fields = ["id", "name", "code", "level", "description", "status", 
                              "permissions", "users", "metadata", "statistics", "created_at", "updated_at"]
                statistics_fields = ["user_count", "permission_count", "active_users", "last_login"]
                
                structure_ok = validate_response_structure(data, expected_fields, "角色详情响应")
                role_structure_ok = validate_response_structure(data["data"]["role"], role_fields, "角色详情结构")
                statistics_ok = validate_response_structure(data["data"]["role"]["statistics"], statistics_fields, "统计信息结构")
                
                # 验证权限结构
                if data["data"]["role"]["permissions"]:
                    permission_fields = ["id", "name", "description", "resource", "action"]
                    permission_ok = validate_response_structure(data["data"]["role"]["permissions"][0], permission_fields, "权限结构")
                    permission_id = data["data"]["role"]["permissions"][0]["id"]  # 保存用于后续测试
                else:
                    permission_ok = True
                    print("✅ 权限列表为空，跳过权限结构验证")
                
                if (data["code"] == 200 and 
                    data["message"] == "获取角色详情成功"):
                    print(f"✅ 获取角色详情成功，权限数: {data['data']['role']['statistics']['permission_count']}")
                    test_results.append(all([structure_ok, role_structure_ok, statistics_ok, permission_ok]))
                else:
                    print("❌ 响应值不符合预期")
                    test_results.append(False)
            else:
                print(f"❌ HTTP状态码错误: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有创建的角色ID，跳过测试")
        test_results.append(False)
    
    # 测试角色不存在 (404 Not Found)
    print("\n3️⃣-2 测试角色不存在 (404 Not Found)")
    print("-" * 50)
    
    try:
        response = requests.get("http://localhost:5000/api/roles/nonexistent_role", headers=headers)
        
        if response.status_code == 404:
            data = response.json()
            if (data["code"] == 404 and 
                data["message"] == "角色不存在"):
                print("✅ 角色不存在处理正确")
                test_results.append(True)
            else:
                print("❌ 404响应值不符合预期")
                test_results.append(False)
        else:
            print(f"❌ 404状态码错误: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 404测试异常: {e}")
        test_results.append(False)

    # API 4: 更新角色信息 (PUT /api/roles/{role_id})
    print("\n4️⃣ API 4: 更新角色信息 (PUT /api/roles/{role_id})")
    print("-" * 70)

    if created_role_id:
        update_data = {
            "name": "高级销售经理",
            "description": "负责销售团队管理、业务决策和战略规划的高级角色",
            "level": 7,
            "status": "active",
            "metadata": {
                "department": "sales",
                "can_approve_discount": True,
                "max_discount_rate": 0.3,
                "can_access_analytics": True
            }
        }

        try:
            response = requests.put(f"http://localhost:5000/api/roles/{created_role_id}",
                                  headers=headers, json=update_data)

            if response.status_code == 200:
                data = response.json()

                # 验证响应结构
                expected_fields = ["code", "message", "data"]
                role_fields = ["id", "name", "code", "level", "description", "status",
                              "user_count", "metadata", "updated_at"]

                structure_ok = validate_response_structure(data, expected_fields, "更新角色响应")
                role_structure_ok = validate_response_structure(data["data"]["role"], role_fields, "更新角色数据结构")

                if (data["code"] == 200 and
                    data["message"] == "角色更新成功" and
                    data["data"]["role"]["name"] == update_data["name"] and
                    data["data"]["role"]["level"] == update_data["level"]):
                    print(f"✅ 更新角色成功，新名称: {data['data']['role']['name']}")
                    test_results.append(structure_ok and role_structure_ok)
                else:
                    print("❌ 更新响应值不符合预期")
                    test_results.append(False)
            else:
                print(f"❌ HTTP状态码错误: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有创建的角色ID，跳过测试")
        test_results.append(False)

    # API 5: 为角色分配权限 (POST /api/roles/{role_id}/permissions)
    print("\n5️⃣ API 5: 为角色分配权限 (POST /api/roles/{role_id}/permissions)")
    print("-" * 70)

    if created_role_id:
        permissions_data = {
            "permissions": [
                "analytics:read",
                "reports:create",
                "users:read",
                "settings:update"
            ],
            "replace": False
        }

        try:
            response = requests.post(f"http://localhost:5000/api/roles/{created_role_id}/permissions",
                                   headers=headers, json=permissions_data)

            if response.status_code == 200:
                data = response.json()

                # 验证响应结构
                expected_fields = ["code", "message", "data"]
                data_fields = ["role", "permissions"]
                role_fields = ["id", "name", "code"]
                permissions_fields = ["added", "existing", "total"]

                structure_ok = validate_response_structure(data, expected_fields, "权限分配响应")
                data_structure_ok = validate_response_structure(data["data"], data_fields, "权限分配数据结构")
                role_structure_ok = validate_response_structure(data["data"]["role"], role_fields, "角色信息结构")
                permissions_structure_ok = validate_response_structure(data["data"]["permissions"], permissions_fields, "权限信息结构")

                if (data["code"] == 200 and
                    data["message"] == "权限分配成功"):
                    added_count = len(data["data"]["permissions"]["added"])
                    total_count = data["data"]["permissions"]["total"]
                    print(f"✅ 权限分配成功，新增: {added_count}，总计: {total_count}")
                    test_results.append(all([structure_ok, data_structure_ok, role_structure_ok, permissions_structure_ok]))
                else:
                    print("❌ 权限分配响应值不符合预期")
                    test_results.append(False)
            else:
                print(f"❌ HTTP状态码错误: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有创建的角色ID，跳过测试")
        test_results.append(False)

    # API 6: 获取角色权限列表 (GET /api/roles/{role_id}/permissions)
    print("\n6️⃣ API 6: 获取角色权限列表 (GET /api/roles/{role_id}/permissions)")
    print("-" * 70)

    if created_role_id:
        try:
            # 测试带筛选参数的请求
            response = requests.get(f"http://localhost:5000/api/roles/{created_role_id}/permissions?resource=products",
                                  headers=headers)

            if response.status_code == 200:
                data = response.json()

                # 验证响应结构
                expected_fields = ["code", "message", "data"]
                data_fields = ["role", "permissions", "summary"]
                role_fields = ["id", "name", "code"]
                summary_fields = ["total_permissions", "by_resource", "by_action"]

                structure_ok = validate_response_structure(data, expected_fields, "权限列表响应")
                data_structure_ok = validate_response_structure(data["data"], data_fields, "权限列表数据结构")
                role_structure_ok = validate_response_structure(data["data"]["role"], role_fields, "角色信息结构")
                summary_structure_ok = validate_response_structure(data["data"]["summary"], summary_fields, "权限汇总结构")

                # 验证权限项结构
                if data["data"]["permissions"]:
                    permission_fields = ["id", "name", "description", "resource", "action", "granted_at"]
                    permission_structure_ok = validate_response_structure(data["data"]["permissions"][0], permission_fields, "权限项结构")
                    if not permission_id:  # 如果之前没有获取到权限ID，这里获取一个
                        permission_id = data["data"]["permissions"][0]["id"]
                else:
                    permission_structure_ok = True
                    print("✅ 权限列表为空，跳过权限项结构验证")

                if (data["code"] == 200 and
                    data["message"] == "获取角色权限成功"):
                    total_permissions = data["data"]["summary"]["total_permissions"]
                    print(f"✅ 获取角色权限成功，总权限数: {total_permissions}")
                    test_results.append(all([structure_ok, data_structure_ok, role_structure_ok, summary_structure_ok, permission_structure_ok]))
                else:
                    print("❌ 权限列表响应值不符合预期")
                    test_results.append(False)
            else:
                print(f"❌ HTTP状态码错误: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有创建的角色ID，跳过测试")
        test_results.append(False)

    # API 7: 移除角色权限 (DELETE /api/roles/{role_id}/permissions/{permission_id})
    print("\n7️⃣ API 7: 移除角色权限 (DELETE /api/roles/{role_id}/permissions/{permission_id})")
    print("-" * 70)

    if created_role_id and permission_id:
        try:
            response = requests.delete(f"http://localhost:5000/api/roles/{created_role_id}/permissions/{permission_id}",
                                     headers=headers)

            if response.status_code == 200:
                data = response.json()

                # 验证响应结构
                expected_fields = ["code", "message", "data"]
                data_fields = ["role", "permission", "removed_at"]
                role_fields = ["id", "name", "code"]
                permission_fields = ["id", "name", "description"]

                structure_ok = validate_response_structure(data, expected_fields, "权限移除响应")
                data_structure_ok = validate_response_structure(data["data"], data_fields, "权限移除数据结构")
                role_structure_ok = validate_response_structure(data["data"]["role"], role_fields, "角色信息结构")
                permission_structure_ok = validate_response_structure(data["data"]["permission"], permission_fields, "权限信息结构")

                if (data["code"] == 200 and
                    data["message"] == "角色权限移除成功"):
                    removed_permission = data["data"]["permission"]["name"]
                    print(f"✅ 权限移除成功，移除权限: {removed_permission}")
                    test_results.append(all([structure_ok, data_structure_ok, role_structure_ok, permission_structure_ok]))
                else:
                    print("❌ 权限移除响应值不符合预期")
                    test_results.append(False)
            else:
                print(f"❌ HTTP状态码错误: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有角色ID或权限ID，跳过测试")
        test_results.append(False)

    # 测试权限不存在 (404 Not Found)
    print("\n7️⃣-2 测试权限不存在 (404 Not Found)")
    print("-" * 50)

    if created_role_id:
        try:
            response = requests.delete(f"http://localhost:5000/api/roles/{created_role_id}/permissions/nonexistent_permission",
                                     headers=headers)

            if response.status_code == 404:
                data = response.json()
                if (data["code"] == 404 and
                    data["message"] == "权限不存在"):
                    print("✅ 权限不存在处理正确")
                    test_results.append(True)
                else:
                    print("❌ 权限不存在响应值不符合预期")
                    test_results.append(False)
            else:
                print(f"❌ 权限不存在状态码错误: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 权限不存在测试异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有角色ID，跳过测试")
        test_results.append(False)

    # API 8: 删除角色 (DELETE /api/roles/{role_id})
    print("\n8️⃣ API 8: 删除角色 (DELETE /api/roles/{role_id})")
    print("-" * 70)

    if created_role_id:
        try:
            # 测试带查询参数的删除
            response = requests.delete(f"http://localhost:5000/api/roles/{created_role_id}?force=true",
                                     headers=headers)

            if response.status_code == 200:
                data = response.json()

                # 验证响应结构
                expected_fields = ["code", "message", "data"]
                data_fields = ["role_id", "name", "deleted_at", "affected_users", "reassigned_to"]

                structure_ok = validate_response_structure(data, expected_fields, "删除角色响应")
                data_structure_ok = validate_response_structure(data["data"], data_fields, "删除角色数据结构")

                if (data["code"] == 200 and
                    data["message"] == "角色删除成功"):
                    deleted_name = data["data"]["name"]
                    print(f"✅ 角色删除成功，删除角色: {deleted_name}")
                    test_results.append(structure_ok and data_structure_ok)
                else:
                    print("❌ 删除角色响应值不符合预期")
                    test_results.append(False)
            else:
                print(f"❌ HTTP状态码错误: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            test_results.append(False)
    else:
        print("❌ 没有创建的角色ID，跳过测试")
        test_results.append(False)

    # 测试删除不存在的角色 (404 Not Found)
    print("\n8️⃣-2 测试删除不存在的角色 (404 Not Found)")
    print("-" * 50)

    try:
        response = requests.delete("http://localhost:5000/api/roles/nonexistent_role", headers=headers)

        if response.status_code == 404:
            data = response.json()
            if (data["code"] == 404 and
                data["message"] == "角色不存在"):
                print("✅ 删除不存在角色处理正确")
                test_results.append(True)
            else:
                print("❌ 删除不存在角色响应值不符合预期")
                test_results.append(False)
        else:
            print(f"❌ 删除不存在角色状态码错误: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ 删除不存在角色测试异常: {e}")
        test_results.append(False)

    # 统计结果
    passed = sum(test_results)
    total = len(test_results)

    print("\n" + "=" * 80)
    print("📊 完整API文档符合性测试结果")
    print("-" * 80)
    print(f"总测试项: {total}")
    print(f"测试通过: {passed}")
    print(f"测试失败: {total - passed}")
    print(f"符合率: {(passed / total * 100):.1f}%")

    # 详细测试项说明
    test_descriptions = [
        "1. 创建角色 - 正常流程",
        "2. 创建角色 - 代码冲突 (409)",
        "3. 获取角色列表 - 带筛选参数",
        "4. 获取角色详情 - 包含用户和权限",
        "5. 获取角色详情 - 角色不存在 (404)",
        "6. 更新角色信息",
        "7. 分配角色权限",
        "8. 获取角色权限列表 - 带筛选",
        "9. 移除角色权限",
        "10. 移除权限 - 权限不存在 (404)",
        "11. 删除角色 - 强制删除",
        "12. 删除角色 - 角色不存在 (404)"
    ]

    print("\n📋 详细测试结果:")
    for i, (result, desc) in enumerate(zip(test_results, test_descriptions)):
        status = "✅" if result else "❌"
        print(f"  {status} {desc}")

    if passed == total:
        print("\n🎉 所有API端点完全符合文档规范！")
        print("✅ 动态数据库生成功能正常")
        print("✅ 请求响应格式100%符合")
        print("✅ 错误处理机制完善")
        print("✅ HTTP状态码正确")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试项不符合文档规范")

    return passed == total


if __name__ == "__main__":
    success = test_complete_api_documentation_compliance()
    exit(0 if success else 1)
