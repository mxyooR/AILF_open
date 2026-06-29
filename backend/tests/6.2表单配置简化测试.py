"""
第六部分 - 表单配置模块简化测试
验证所有13个API端点的功能
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


def test_form_apis():
    """测试所有表单API"""
    print("🚀 开始运行表单配置模块简化测试...")
    print("=" * 60)
    
    # 获取token
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_results = []
    form_id = None
    entity_id = f"entity_{int(time.time())}"
    
    # 1. 创建表单配置
    print("1️⃣ 测试创建表单配置...")
    form_data = {
        "name": "简化测试表单",
        "entity": "test_entity",
        "description": "用于简化测试的表单",
        "layout": {"type": "grid", "columns": 2, "spacing": 16},
        "sections": [
            {
                "id": "section_basic",
                "title": "基本信息",
                "collapsible": False,
                "fields": [
                    {
                        "id": "field_name",
                        "entityField": "name",
                        "displayType": "input",
                        "label": "名称",
                        "required": True,
                        "gridSpan": 1
                    }
                ]
            }
        ],
        "permissions": []
    }
    
    response = requests.post("http://localhost:5000/api/forms", headers=headers, json=form_data)
    if response.status_code in [200, 201]:
        form_id = response.json()["data"]["form"]["id"]
        print(f"   ✅ 创建成功: {form_id}")
        test_results.append(True)
    else:
        print(f"   ❌ 创建失败: {response.status_code}")
        test_results.append(False)
    
    # 2. 获取表单配置列表
    print("2️⃣ 测试获取表单配置列表...")
    response = requests.get("http://localhost:5000/api/forms", headers=headers)
    if response.status_code == 200:
        forms = response.json()["data"]["forms"]
        print(f"   ✅ 获取成功: {len(forms)}个表单")
        test_results.append(True)
    else:
        print(f"   ❌ 获取失败: {response.status_code}")
        test_results.append(False)
    
    # 3. 获取表单配置详情
    print("3️⃣ 测试获取表单配置详情...")
    if form_id:
        response = requests.get(f"http://localhost:5000/api/forms/{form_id}", headers=headers)
        if response.status_code == 200:
            form = response.json()["data"]["form"]
            print(f"   ✅ 获取成功: {form['name']}")
            test_results.append(True)
        else:
            print(f"   ❌ 获取失败: {response.status_code}")
            test_results.append(False)
    else:
        print("   ❌ 没有表单ID")
        test_results.append(False)
    
    # 4. 更新表单配置
    print("4️⃣ 测试更新表单配置...")
    if form_id:
        update_data = {"description": "更新后的描述"}
        response = requests.put(f"http://localhost:5000/api/forms/{form_id}", headers=headers, json=update_data)
        if response.status_code == 200:
            print("   ✅ 更新成功")
            test_results.append(True)
        else:
            print(f"   ❌ 更新失败: {response.status_code}")
            test_results.append(False)
    else:
        print("   ❌ 没有表单ID")
        test_results.append(False)
    
    # 5. 获取表单渲染配置
    print("5️⃣ 测试获取表单渲染配置...")
    if form_id:
        response = requests.get(f"http://localhost:5000/api/forms/{form_id}/render", headers=headers)
        if response.status_code == 200:
            schema = response.json()["data"]["schema"]
            print(f"   ✅ 获取成功: {schema['type']}")
            test_results.append(True)
        else:
            print(f"   ❌ 获取失败: {response.status_code}")
            test_results.append(False)
    else:
        print("   ❌ 没有表单ID")
        test_results.append(False)
    
    # 6. 提交表单数据
    print("6️⃣ 测试提交表单数据...")
    if form_id:
        submit_data = {
            "form_data": {"name": "测试数据"},
            "entity_id": entity_id
        }
        response = requests.post(f"http://localhost:5000/api/forms/{form_id}/submit", headers=headers, json=submit_data)
        if response.status_code == 200:
            print("   ✅ 提交成功")
            test_results.append(True)
        else:
            print(f"   ❌ 提交失败: {response.status_code}")
            test_results.append(False)
    else:
        print("   ❌ 没有表单ID")
        test_results.append(False)
    
    # 7. 获取表单数据用于编辑
    print("7️⃣ 测试获取表单数据用于编辑...")
    if form_id:
        response = requests.get(f"http://localhost:5000/api/forms/{form_id}/data/{entity_id}", headers=headers)
        if response.status_code == 200:
            data = response.json()["data"]["form_data"]
            print(f"   ✅ 获取成功: {data.get('name', 'N/A')}")
            test_results.append(True)
        else:
            print(f"   ❌ 获取失败: {response.status_code}")
            test_results.append(False)
    else:
        print("   ❌ 没有表单ID")
        test_results.append(False)
    
    # 8. 验证表单配置
    print("8️⃣ 测试验证表单配置...")
    if form_id:
        response = requests.post(f"http://localhost:5000/api/forms/{form_id}/validate", headers=headers)
        if response.status_code == 200:
            validation = response.json()["data"]
            print(f"   ✅ 验证完成: {validation['valid']}")
            test_results.append(True)
        else:
            print(f"   ❌ 验证失败: {response.status_code}")
            test_results.append(False)
    else:
        print("   ❌ 没有表单ID")
        test_results.append(False)
    
    # 9. 获取表单字段列表
    print("9️⃣ 测试获取表单字段列表...")
    if form_id:
        response = requests.get(f"http://localhost:5000/api/forms/{form_id}/fields", headers=headers)
        if response.status_code == 200:
            fields = response.json()["data"]["fields"]
            print(f"   ✅ 获取成功: {len(fields)}个字段")
            test_results.append(True)
        else:
            print(f"   ❌ 获取失败: {response.status_code}")
            test_results.append(False)
    else:
        print("   ❌ 没有表单ID")
        test_results.append(False)
    
    # 10. 添加表单字段
    print("🔟 测试添加表单字段...")
    if form_id:
        field_data = {
            "field_id": "field_description",
            "section_id": "section_basic",
            "entityField": "description",
            "displayType": "textarea",
            "label": "描述",
            "required": False,
            "gridSpan": 2
        }
        response = requests.post(f"http://localhost:5000/api/forms/{form_id}/fields", headers=headers, json=field_data)
        if response.status_code in [200, 201]:
            print("   ✅ 添加成功")
            test_results.append(True)
        else:
            print(f"   ❌ 添加失败: {response.status_code}")
            test_results.append(False)
    else:
        print("   ❌ 没有表单ID")
        test_results.append(False)
    
    # 11. 更新表单字段
    print("1️⃣1️⃣ 测试更新表单字段...")
    if form_id:
        update_data = {"label": "详细描述"}
        response = requests.put(f"http://localhost:5000/api/forms/{form_id}/fields/field_description", headers=headers, json=update_data)
        if response.status_code == 200:
            print("   ✅ 更新成功")
            test_results.append(True)
        else:
            print(f"   ❌ 更新失败: {response.status_code}")
            test_results.append(False)
    else:
        print("   ❌ 没有表单ID")
        test_results.append(False)
    
    # 12. 删除表单字段
    print("1️⃣2️⃣ 测试删除表单字段...")
    if form_id:
        response = requests.delete(f"http://localhost:5000/api/forms/{form_id}/fields/field_description", headers=headers)
        if response.status_code == 200:
            print("   ✅ 删除成功")
            test_results.append(True)
        else:
            print(f"   ❌ 删除失败: {response.status_code}")
            test_results.append(False)
    else:
        print("   ❌ 没有表单ID")
        test_results.append(False)
    
    # 13. 删除表单配置
    print("1️⃣3️⃣ 测试删除表单配置...")
    if form_id:
        response = requests.delete(f"http://localhost:5000/api/forms/{form_id}?force=true", headers=headers)
        if response.status_code == 200:
            print("   ✅ 删除成功")
            test_results.append(True)
        else:
            print(f"   ❌ 删除失败: {response.status_code}")
            test_results.append(False)
    else:
        print("   ❌ 没有表单ID")
        test_results.append(False)
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 60)
    print("📊 第六部分表单配置模块测试结果")
    print("-" * 60)
    print(f"总API端点: {total}")
    print(f"测试通过: {passed}")
    print(f"测试失败: {total - passed}")
    print(f"成功率: {(passed / total * 100):.1f}%")
    
    if passed == total:
        print("🎉 所有13个API端点测试全部通过！")
        return True
    else:
        print(f"⚠️  有 {total - passed} 个API端点测试失败")
        return False


if __name__ == "__main__":
    success = test_form_apis()
    exit(0 if success else 1)
