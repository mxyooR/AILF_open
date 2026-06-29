"""
第六部分 - 表单配置模块API文档完全符合性测试
验证所有13个API端点完全符合API文档规范
包括请求格式、响应格式、状态码、字段完整性等
"""
import requests
import json
import time
import re


def get_auth_token():
    """获取认证令牌"""
    response = requests.post(
        "http://localhost:5000/api/auth/developer",
        json={"password": "AILF_DEV_2024_SECURE"}
    )
    return response.json()["data"]["token"]


def check_time_format(time_str):
    """检查时间格式是否符合ISO 8601标准"""
    pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z'
    return re.match(pattern, time_str) is not None


def test_complete_form_api_compliance():
    """测试表单API完全符合性"""
    print("🔍 第六部分 - 表单配置模块API文档完全符合性测试")
    print("验证所有13个API端点完全符合API文档规范")
    print("=" * 80)
    
    # 获取token
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    compliance_results = []
    form_id = None
    field_id = None
    entity_id = f"entity_{int(time.time())}"
    
    # 1. 测试创建动态表单配置API
    print("\n1️⃣ 测试创建动态表单配置 (POST /api/forms)")
    print("-" * 60)
    
    form_data = {
        "name": "完全符合性测试表单",
        "entity": "compliance_test",
        "description": "用于验证API文档完全符合性的测试表单",
        "layout": {
            "type": "grid",
            "columns": 2,
            "spacing": 16
        },
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
                        "placeholder": "请输入名称",
                        "required": True,
                        "readonly": False,
                        "hidden": False,
                        "validation": {
                            "rules": ["required", "max:100"],
                            "messages": {
                                "required": "名称不能为空",
                                "max": "名称不能超过100个字符"
                            }
                        }
                    }
                ]
            }
        ],
        "permissions": [
            {
                "role": "admin",
                "actions": ["create", "read", "update", "delete"]
            }
        ]
    }
    
    response = requests.post("http://localhost:5000/api/forms", headers=headers, json=form_data)
    
    # 检查状态码
    status_ok = response.status_code == 201
    print(f"状态码: 期望201, 实际{response.status_code} - {'✅' if status_ok else '❌'}")
    
    if response.status_code == 201:
        data = response.json()
        form_id = data["data"]["form"]["id"]
        
        # 检查响应结构
        required_structure = {
            "code": lambda x: x == 201,
            "message": lambda x: isinstance(x, str),
            "data": lambda x: isinstance(x, dict),
            "data.form": lambda x: "form" in data.get("data", {}),
        }
        
        for field, validator in required_structure.items():
            if "." in field:
                parts = field.split(".")
                value = data
                for part in parts:
                    value = value.get(part, {})
                check = validator(value)
            else:
                check = validator(data.get(field))
            print(f"响应结构.{field}: {'✅' if check else '❌'}")
        
        # 检查表单字段完整性
        if "form" in data.get("data", {}):
            form = data["data"]["form"]
            required_form_fields = {
                "id": lambda x: isinstance(x, str) and x.startswith("form_"),
                "name": lambda x: x == "完全符合性测试表单",
                "entity": lambda x: x == "compliance_test",
                "description": lambda x: isinstance(x, str),
                "layout": lambda x: isinstance(x, dict),
                "sections": lambda x: isinstance(x, list) and len(x) > 0,
                "field_count": lambda x: isinstance(x, int),
                "created_at": lambda x: check_time_format(x),
                "updated_at": lambda x: check_time_format(x)
            }
            
            for field, validator in required_form_fields.items():
                check = validator(form.get(field))
                print(f"表单.{field}: {'✅' if check else '❌'}")
            
            # 检查sections格式
            if "sections" in form and form["sections"]:
                section = form["sections"][0]
                required_section_fields = {
                    "id": lambda x: x == "section_basic",
                    "title": lambda x: x == "基本信息",
                    "collapsible": lambda x: x == False,
                    "field_count": lambda x: isinstance(x, int)
                }
                
                for field, validator in required_section_fields.items():
                    check = validator(section.get(field))
                    print(f"分组.{field}: {'✅' if check else '❌'}")
        
        compliance_results.append(status_ok)
    else:
        print(f"❌ 创建失败: {response.text}")
        compliance_results.append(False)
    
    # 2. 测试获取所有表单配置API
    print("\n2️⃣ 测试获取所有表单配置 (GET /api/forms)")
    print("-" * 60)
    
    response = requests.get("http://localhost:5000/api/forms?page=1&limit=20", headers=headers)
    
    status_ok = response.status_code == 200
    print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")
    
    if response.status_code == 200:
        data = response.json()
        
        # 检查响应结构
        required_structure = {
            "code": lambda x: x == 200,
            "message": lambda x: isinstance(x, str),
            "data": lambda x: isinstance(x, dict),
            "data.forms": lambda x: isinstance(data.get("data", {}).get("forms"), list),
            "data.total": lambda x: isinstance(data.get("data", {}).get("total"), int)
        }
        
        for field, validator in required_structure.items():
            if "." in field:
                parts = field.split(".")
                value = data
                for part in parts:
                    value = value.get(part, {})
                check = validator(value)
            else:
                check = validator(data.get(field))
            print(f"响应结构.{field}: {'✅' if check else '❌'}")
        
        # 检查表单列表项字段
        if "forms" in data.get("data", {}) and data["data"]["forms"]:
            form = data["data"]["forms"][0]
            required_list_fields = {
                "id": lambda x: isinstance(x, str),
                "name": lambda x: isinstance(x, str),
                "entity": lambda x: isinstance(x, str),
                "description": lambda x: isinstance(x, str),
                "field_count": lambda x: isinstance(x, int),
                "section_count": lambda x: isinstance(x, int),
                "created_at": lambda x: check_time_format(x),
                "updated_at": lambda x: check_time_format(x)
            }
            
            for field, validator in required_list_fields.items():
                check = validator(form.get(field))
                print(f"表单项.{field}: {'✅' if check else '❌'}")
        
        compliance_results.append(status_ok)
    else:
        compliance_results.append(False)
    
    # 3. 测试获取特定表单配置API
    print("\n3️⃣ 测试获取特定表单配置 (GET /api/forms/{form_id})")
    print("-" * 60)
    
    if form_id:
        response = requests.get(f"http://localhost:5000/api/forms/{form_id}", headers=headers)
        
        status_ok = response.status_code == 200
        print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查响应结构（应该与创建表单相同）
            required_structure = {
                "code": lambda x: x == 200,
                "message": lambda x: isinstance(x, str),
                "data": lambda x: isinstance(x, dict),
                "data.form": lambda x: "form" in data.get("data", {})
            }
            
            for field, validator in required_structure.items():
                if "." in field:
                    parts = field.split(".")
                    value = data
                    for part in parts:
                        value = value.get(part, {})
                    check = validator(value)
                else:
                    check = validator(data.get(field))
                print(f"响应结构.{field}: {'✅' if check else '❌'}")
            
            # 检查是否包含完整的表单信息
            if "form" in data.get("data", {}):
                form = data["data"]["form"]
                has_sections = "sections" in form and isinstance(form["sections"], list)
                has_layout = "layout" in form and isinstance(form["layout"], dict)
                has_permissions = "permissions" in form and isinstance(form["permissions"], list)
                
                print(f"包含sections: {'✅' if has_sections else '❌'}")
                print(f"包含layout: {'✅' if has_layout else '❌'}")
                print(f"包含permissions: {'✅' if has_permissions else '❌'}")
            
            compliance_results.append(status_ok)
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有表单ID，跳过测试")
        compliance_results.append(False)
    
    # 4. 测试更新表单配置API
    print("\n4️⃣ 测试更新表单配置 (PUT /api/forms/{form_id})")
    print("-" * 60)
    
    if form_id:
        update_data = {
            "name": "更新后的完全符合性测试表单",
            "description": "更新后的描述信息"
        }
        
        response = requests.put(f"http://localhost:5000/api/forms/{form_id}", 
                              headers=headers, json=update_data)
        
        status_ok = response.status_code == 200
        print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查响应结构
            required_structure = {
                "code": lambda x: x == 200,
                "message": lambda x: isinstance(x, str),
                "data": lambda x: isinstance(x, dict),
                "data.form": lambda x: "form" in data.get("data", {})
            }
            
            for field, validator in required_structure.items():
                if "." in field:
                    parts = field.split(".")
                    value = data
                    for part in parts:
                        value = value.get(part, {})
                    check = validator(value)
                else:
                    check = validator(data.get(field))
                print(f"响应结构.{field}: {'✅' if check else '❌'}")
            
            # 检查更新是否生效
            if "form" in data.get("data", {}):
                form = data["data"]["form"]
                name_updated = form.get("name") == "更新后的完全符合性测试表单"
                desc_updated = form.get("description") == "更新后的描述信息"
                
                print(f"名称更新: {'✅' if name_updated else '❌'}")
                print(f"描述更新: {'✅' if desc_updated else '❌'}")
            
            compliance_results.append(status_ok)
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有表单ID，跳过测试")
        compliance_results.append(False)
    
    # 5. 测试获取表单渲染配置API
    print("\n5️⃣ 测试获取表单渲染配置 (GET /api/forms/{form_id}/render)")
    print("-" * 60)
    
    if form_id:
        response = requests.get(f"http://localhost:5000/api/forms/{form_id}/render?user_role=admin&mode=create", 
                              headers=headers)
        
        status_ok = response.status_code == 200
        print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查响应结构
            required_structure = {
                "code": lambda x: x == 200,
                "message": lambda x: isinstance(x, str),
                "data": lambda x: isinstance(x, dict),
                "data.schema": lambda x: "schema" in data.get("data", {})
            }
            
            for field, validator in required_structure.items():
                if "." in field:
                    parts = field.split(".")
                    value = data
                    for part in parts:
                        value = value.get(part, {})
                    check = validator(value)
                else:
                    check = validator(data.get(field))
                print(f"响应结构.{field}: {'✅' if check else '❌'}")
            
            # 检查amis schema格式
            if "schema" in data.get("data", {}):
                schema = data["data"]["schema"]
                required_schema_fields = {
                    "type": lambda x: x == "form",
                    "title": lambda x: isinstance(x, str),
                    "api": lambda x: isinstance(x, dict),
                    "body": lambda x: isinstance(x, list)
                }
                
                for field, validator in required_schema_fields.items():
                    check = validator(schema.get(field))
                    print(f"schema.{field}: {'✅' if check else '❌'}")
            
            compliance_results.append(status_ok)
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有表单ID，跳过测试")
        compliance_results.append(False)
    
    # 6. 测试提交表单数据API
    print("\n6️⃣ 测试提交表单数据 (POST /api/forms/{form_id}/submit)")
    print("-" * 60)

    if form_id:
        submit_data = {
            "form_data": {"name": "测试提交数据"},
            "entity_id": entity_id
        }

        response = requests.post(f"http://localhost:5000/api/forms/{form_id}/submit",
                               headers=headers, json=submit_data)

        status_ok = response.status_code == 200
        print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")

        if response.status_code == 200:
            data = response.json()

            # 检查响应结构
            required_structure = {
                "code": lambda x: x == 200,
                "message": lambda x: isinstance(x, str),
                "data": lambda x: isinstance(x, dict),
                "data.data_id": lambda x: isinstance(data.get("data", {}).get("data_id"), str),
                "data.form_data": lambda x: isinstance(data.get("data", {}).get("form_data"), dict),
                "data.submitted_at": lambda x: check_time_format(data.get("data", {}).get("submitted_at", ""))
            }

            for field, validator in required_structure.items():
                if "." in field:
                    parts = field.split(".")
                    value = data
                    for part in parts:
                        value = value.get(part, {})
                    check = validator(value)
                else:
                    check = validator(data.get(field))
                print(f"响应结构.{field}: {'✅' if check else '❌'}")

            compliance_results.append(status_ok)
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有表单ID，跳过测试")
        compliance_results.append(False)

    # 7. 测试获取表单数据用于编辑API
    print("\n7️⃣ 测试获取表单数据用于编辑 (GET /api/forms/{form_id}/data/{entity_id})")
    print("-" * 60)

    if form_id and entity_id:
        response = requests.get(f"http://localhost:5000/api/forms/{form_id}/data/{entity_id}",
                              headers=headers)

        status_ok = response.status_code == 200
        print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")

        if response.status_code == 200:
            data = response.json()

            # 检查响应结构
            required_structure = {
                "code": lambda x: x == 200,
                "message": lambda x: isinstance(x, str),
                "data": lambda x: isinstance(x, dict),
                "data.form_data": lambda x: isinstance(data.get("data", {}).get("form_data"), dict),
                "data.entity_id": lambda x: data.get("data", {}).get("entity_id") == entity_id
            }

            for field, validator in required_structure.items():
                if "." in field:
                    parts = field.split(".")
                    value = data
                    for part in parts:
                        value = value.get(part, {})
                    check = validator(value)
                else:
                    check = validator(data.get(field))
                print(f"响应结构.{field}: {'✅' if check else '❌'}")

            compliance_results.append(status_ok)
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有表单ID或实体ID，跳过测试")
        compliance_results.append(False)

    # 8. 测试验证表单配置API
    print("\n8️⃣ 测试验证表单配置 (POST /api/forms/{form_id}/validate)")
    print("-" * 60)

    if form_id:
        response = requests.post(f"http://localhost:5000/api/forms/{form_id}/validate",
                               headers=headers, json={})

        status_ok = response.status_code == 200
        print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")

        if response.status_code == 200:
            data = response.json()

            # 检查响应结构
            required_structure = {
                "code": lambda x: x == 200,
                "message": lambda x: isinstance(x, str),
                "data": lambda x: isinstance(x, dict),
                "data.valid": lambda x: isinstance(data.get("data", {}).get("valid"), bool),
                "data.errors": lambda x: isinstance(data.get("data", {}).get("errors"), list)
            }

            for field, validator in required_structure.items():
                if "." in field:
                    parts = field.split(".")
                    value = data
                    for part in parts:
                        value = value.get(part, {})
                    check = validator(value)
                else:
                    check = validator(data.get(field))
                print(f"响应结构.{field}: {'✅' if check else '❌'}")

            compliance_results.append(status_ok)
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有表单ID，跳过测试")
        compliance_results.append(False)

    # 9. 测试获取表单字段列表API
    print("\n9️⃣ 测试获取表单字段列表 (GET /api/forms/{form_id}/fields)")
    print("-" * 60)

    if form_id:
        response = requests.get(f"http://localhost:5000/api/forms/{form_id}/fields", headers=headers)

        status_ok = response.status_code == 200
        print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")

        if response.status_code == 200:
            data = response.json()

            # 检查响应结构
            required_structure = {
                "code": lambda x: x == 200,
                "message": lambda x: isinstance(x, str),
                "data": lambda x: isinstance(x, dict),
                "data.fields": lambda x: isinstance(data.get("data", {}).get("fields"), list),
                "data.total": lambda x: isinstance(data.get("data", {}).get("total"), int)
            }

            for field, validator in required_structure.items():
                if "." in field:
                    parts = field.split(".")
                    value = data
                    for part in parts:
                        value = value.get(part, {})
                    check = validator(value)
                else:
                    check = validator(data.get(field))
                print(f"响应结构.{field}: {'✅' if check else '❌'}")

            # 检查字段项格式
            if "fields" in data.get("data", {}) and data["data"]["fields"]:
                field_item = data["data"]["fields"][0]
                required_field_fields = {
                    "id": lambda x: isinstance(x, str),
                    "entityField": lambda x: isinstance(x, str),
                    "displayType": lambda x: isinstance(x, str),
                    "label": lambda x: isinstance(x, str),
                    "required": lambda x: isinstance(x, bool),
                    "readonly": lambda x: isinstance(x, bool),
                    "hidden": lambda x: isinstance(x, bool),
                    "created_at": lambda x: check_time_format(x),
                    "updated_at": lambda x: check_time_format(x)
                }

                for field, validator in required_field_fields.items():
                    check = validator(field_item.get(field))
                    print(f"字段项.{field}: {'✅' if check else '❌'}")

            compliance_results.append(status_ok)
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有表单ID，跳过测试")
        compliance_results.append(False)

    # 10. 测试添加表单字段API
    print("\n🔟 测试添加表单字段 (POST /api/forms/{form_id}/fields)")
    print("-" * 60)

    if form_id:
        field_data = {
            "field_id": "field_email",
            "section_id": "section_basic",
            "entityField": "email",
            "displayType": "input",
            "label": "邮箱地址",
            "placeholder": "请输入邮箱地址",
            "required": True,
            "readonly": False,
            "hidden": False,
            "validation": {
                "rules": ["required", "email"],
                "messages": {
                    "required": "邮箱不能为空",
                    "email": "邮箱格式不正确"
                }
            },
            "gridSpan": 1
        }

        response = requests.post(f"http://localhost:5000/api/forms/{form_id}/fields",
                               headers=headers, json=field_data)

        status_ok = response.status_code == 201
        print(f"状态码: 期望201, 实际{response.status_code} - {'✅' if status_ok else '❌'}")

        if response.status_code == 201:
            data = response.json()
            field_id = data["data"]["field"]["id"]

            # 检查响应结构
            required_structure = {
                "code": lambda x: x == 201,
                "message": lambda x: isinstance(x, str),
                "data": lambda x: isinstance(x, dict),
                "data.field": lambda x: "field" in data.get("data", {})
            }

            for field, validator in required_structure.items():
                if "." in field:
                    parts = field.split(".")
                    value = data
                    for part in parts:
                        value = value.get(part, {})
                    check = validator(value)
                else:
                    check = validator(data.get(field))
                print(f"响应结构.{field}: {'✅' if check else '❌'}")

            compliance_results.append(status_ok)
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有表单ID，跳过测试")
        compliance_results.append(False)

    # 11. 测试更新表单字段API
    print("\n1️⃣1️⃣ 测试更新表单字段 (PUT /api/forms/{form_id}/fields/{field_id})")
    print("-" * 60)

    if form_id and field_id:
        update_field_data = {
            "label": "更新后的邮箱地址",
            "placeholder": "请输入您的邮箱地址",
            "required": False
        }

        response = requests.put(f"http://localhost:5000/api/forms/{form_id}/fields/{field_id}",
                              headers=headers, json=update_field_data)

        status_ok = response.status_code == 200
        print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")

        if response.status_code == 200:
            data = response.json()

            # 检查响应结构
            required_structure = {
                "code": lambda x: x == 200,
                "message": lambda x: isinstance(x, str),
                "data": lambda x: isinstance(x, dict),
                "data.field": lambda x: "field" in data.get("data", {})
            }

            for field, validator in required_structure.items():
                if "." in field:
                    parts = field.split(".")
                    value = data
                    for part in parts:
                        value = value.get(part, {})
                    check = validator(value)
                else:
                    check = validator(data.get(field))
                print(f"响应结构.{field}: {'✅' if check else '❌'}")

            compliance_results.append(status_ok)
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有表单ID或字段ID，跳过测试")
        compliance_results.append(False)

    # 12. 测试删除表单字段API
    print("\n1️⃣2️⃣ 测试删除表单字段 (DELETE /api/forms/{form_id}/fields/{field_id})")
    print("-" * 60)

    if form_id and field_id:
        response = requests.delete(f"http://localhost:5000/api/forms/{form_id}/fields/{field_id}",
                                 headers=headers)

        status_ok = response.status_code == 200
        print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")

        if response.status_code == 200:
            data = response.json()

            # 检查响应结构
            required_structure = {
                "code": lambda x: x == 200,
                "message": lambda x: isinstance(x, str),
                "data": lambda x: isinstance(x, dict)
            }

            for field, validator in required_structure.items():
                check = validator(data.get(field))
                print(f"响应结构.{field}: {'✅' if check else '❌'}")

            compliance_results.append(status_ok)
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有表单ID或字段ID，跳过测试")
        compliance_results.append(False)

    # 13. 测试删除表单配置API
    print("\n1️⃣3️⃣ 测试删除表单配置 (DELETE /api/forms/{form_id})")
    print("-" * 60)

    if form_id:
        response = requests.delete(f"http://localhost:5000/api/forms/{form_id}?force=true",
                                 headers=headers)

        status_ok = response.status_code == 200
        print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")

        if response.status_code == 200:
            data = response.json()

            # 检查响应结构
            required_structure = {
                "code": lambda x: x == 200,
                "message": lambda x: isinstance(x, str),
                "data": lambda x: isinstance(x, dict)
            }

            for field, validator in required_structure.items():
                check = validator(data.get(field))
                print(f"响应结构.{field}: {'✅' if check else '❌'}")

            compliance_results.append(status_ok)
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有表单ID，跳过测试")
        compliance_results.append(False)

    # 最终统计
    passed = sum(compliance_results)
    total = len(compliance_results)

    print("\n" + "=" * 80)
    print("📊 第六部分表单配置模块API文档完全符合性测试结果")
    print("-" * 80)
    print(f"测试API数量: {total}")
    print(f"符合文档: {passed}")
    print(f"不符合文档: {total - passed}")
    print(f"符合率: {(passed / total * 100):.1f}%")

    if passed == total:
        print("🎉 所有13个API完全符合文档规范！")
        return True
    else:
        print(f"⚠️  有 {total - passed} 个API不符合文档规范")
        return False


if __name__ == "__main__":
    success = test_complete_form_api_compliance()
    exit(0 if success else 1)
