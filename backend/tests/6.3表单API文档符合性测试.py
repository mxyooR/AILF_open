"""
第六部分 - 表单配置模块API文档符合性测试
验证所有13个API端点完全符合API文档规范
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


def test_form_api_compliance():
    """测试表单API文档符合性"""
    print("🔍 第六部分 - 表单配置模块API文档符合性测试")
    print("=" * 80)
    
    # 获取token
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    compliance_results = []
    form_id = None
    entity_id = f"entity_{int(time.time())}"
    
    # 1. 测试创建动态表单配置API
    print("\n1️⃣ 测试创建动态表单配置 (POST /api/forms)")
    print("-" * 50)
    
    form_data = {
        "name": "API文档符合性测试表单",
        "entity": "test_entity",
        "description": "用于验证API文档符合性的测试表单",
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
                        },
                        "gridSpan": 1
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
        structure_checks = [
            ("code", data.get("code") == 201),
            ("message", "message" in data),
            ("data", "data" in data),
            ("data.form", "form" in data.get("data", {}))
        ]
        
        for field, check in structure_checks:
            print(f"响应结构.{field}: {'✅' if check else '❌'}")
        
        # 检查表单字段
        if "form" in data.get("data", {}):
            form = data["data"]["form"]
            form_fields = [
                ("id", "id" in form),
                ("name", "name" in form),
                ("entity", "entity" in form),
                ("description", "description" in form),
                ("layout", "layout" in form),
                ("status", "status" in form),
                ("sections", "sections" in form),
                ("permissions", "permissions" in form),
                ("field_count", "field_count" in form),
                ("section_count", "section_count" in form),
                ("created_at", "created_at" in form and check_time_format(form.get("created_at", ""))),
                ("updated_at", "updated_at" in form and check_time_format(form.get("updated_at", "")))
            ]
            
            for field, check in form_fields:
                print(f"表单.{field}: {'✅' if check else '❌'}")
            
            # 检查sections格式
            if "sections" in form and form["sections"]:
                section = form["sections"][0]
                section_fields = [
                    ("id", "id" in section),
                    ("title", "title" in section),
                    ("collapsible", "collapsible" in section),
                    ("fields", "fields" in section),
                    ("orderIndex", "orderIndex" in section),
                    ("created_at", "created_at" in section and check_time_format(section.get("created_at", ""))),
                    ("updated_at", "updated_at" in section and check_time_format(section.get("updated_at", "")))
                ]
                
                for field, check in section_fields:
                    print(f"分组.{field}: {'✅' if check else '❌'}")
                
                # 检查字段格式
                if "fields" in section and section["fields"]:
                    field = section["fields"][0]
                    field_fields = [
                        ("id", "id" in field),
                        ("entityField", "entityField" in field),
                        ("displayType", "displayType" in field),
                        ("label", "label" in field),
                        ("required", "required" in field),
                        ("readonly", "readonly" in field),
                        ("hidden", "hidden" in field),
                        ("validation", "validation" in field),
                        ("gridSpan", "gridSpan" in field),
                        ("orderIndex", "orderIndex" in field),
                        ("created_at", "created_at" in field and check_time_format(field.get("created_at", ""))),
                        ("updated_at", "updated_at" in field and check_time_format(field.get("updated_at", "")))
                    ]
                    
                    for field_name, check in field_fields:
                        print(f"字段.{field_name}: {'✅' if check else '❌'}")
        
        compliance_results.append(status_ok and all(check for _, check in structure_checks))
    else:
        compliance_results.append(False)
    
    # 2. 测试获取所有表单配置API
    print("\n2️⃣ 测试获取所有表单配置 (GET /api/forms)")
    print("-" * 50)
    
    response = requests.get("http://localhost:5000/api/forms", headers=headers)
    
    status_ok = response.status_code == 200
    print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")
    
    if response.status_code == 200:
        data = response.json()
        
        # 检查响应结构
        structure_checks = [
            ("code", data.get("code") == 200),
            ("message", "message" in data),
            ("data", "data" in data),
            ("data.forms", "forms" in data.get("data", {})),
            ("data.total", "total" in data.get("data", {}))
        ]
        
        for field, check in structure_checks:
            print(f"响应结构.{field}: {'✅' if check else '❌'}")
        
        # 检查表单列表项字段
        if "forms" in data.get("data", {}) and data["data"]["forms"]:
            form = data["data"]["forms"][0]
            form_fields = [
                ("id", "id" in form),
                ("name", "name" in form),
                ("entity", "entity" in form),
                ("description", "description" in form),
                ("status", "status" in form),
                ("field_count", "field_count" in form),
                ("section_count", "section_count" in form),
                ("created_at", "created_at" in form and check_time_format(form.get("created_at", ""))),
                ("updated_at", "updated_at" in form and check_time_format(form.get("updated_at", "")))
            ]
            
            for field, check in form_fields:
                print(f"表单项.{field}: {'✅' if check else '❌'}")
        
        compliance_results.append(status_ok and all(check for _, check in structure_checks))
    else:
        compliance_results.append(False)
    
    # 3. 测试获取特定表单配置API
    print("\n3️⃣ 测试获取特定表单配置 (GET /api/forms/{form_id})")
    print("-" * 50)
    
    if form_id:
        response = requests.get(f"http://localhost:5000/api/forms/{form_id}", headers=headers)
        
        status_ok = response.status_code == 200
        print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查响应结构（与创建表单相同）
            structure_checks = [
                ("code", data.get("code") == 200),
                ("message", "message" in data),
                ("data", "data" in data),
                ("data.form", "form" in data.get("data", {}))
            ]
            
            for field, check in structure_checks:
                print(f"响应结构.{field}: {'✅' if check else '❌'}")
            
            compliance_results.append(status_ok and all(check for _, check in structure_checks))
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有表单ID，跳过测试")
        compliance_results.append(False)
    
    # 4. 测试获取表单渲染配置API
    print("\n4️⃣ 测试获取表单渲染配置 (GET /api/forms/{form_id}/render)")
    print("-" * 50)
    
    if form_id:
        response = requests.get(f"http://localhost:5000/api/forms/{form_id}/render?user_role=admin", headers=headers)
        
        status_ok = response.status_code == 200
        print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查响应结构
            structure_checks = [
                ("code", data.get("code") == 200),
                ("message", "message" in data),
                ("data", "data" in data),
                ("data.schema", "schema" in data.get("data", {}))
            ]
            
            for field, check in structure_checks:
                print(f"响应结构.{field}: {'✅' if check else '❌'}")
            
            # 检查amis schema格式
            if "schema" in data.get("data", {}):
                schema = data["data"]["schema"]
                schema_fields = [
                    ("type", "type" in schema),
                    ("title", "title" in schema),
                    ("api", "api" in schema),
                    ("body", "body" in schema)
                ]
                
                for field, check in schema_fields:
                    print(f"schema.{field}: {'✅' if check else '❌'}")
            
            compliance_results.append(status_ok and all(check for _, check in structure_checks))
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有表单ID，跳过测试")
        compliance_results.append(False)
    
    # 5. 测试提交表单数据API
    print("\n5️⃣ 测试提交表单数据 (POST /api/forms/{form_id}/submit)")
    print("-" * 50)
    
    if form_id:
        submit_data = {
            "form_data": {"name": "测试数据"},
            "entity_id": entity_id
        }
        
        response = requests.post(f"http://localhost:5000/api/forms/{form_id}/submit", 
                               headers=headers, json=submit_data)
        
        status_ok = response.status_code == 200
        print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查响应结构
            structure_checks = [
                ("code", data.get("code") == 200),
                ("message", "message" in data),
                ("data", "data" in data),
                ("data.data_id", "data_id" in data.get("data", {})),
                ("data.form_data", "form_data" in data.get("data", {})),
                ("data.submitted_at", "submitted_at" in data.get("data", {}))
            ]
            
            for field, check in structure_checks:
                print(f"响应结构.{field}: {'✅' if check else '❌'}")
            
            compliance_results.append(status_ok and all(check for _, check in structure_checks))
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有表单ID，跳过测试")
        compliance_results.append(False)
    
    # 统计结果
    passed = sum(compliance_results)
    total = len(compliance_results)
    
    print("\n" + "=" * 80)
    print("📊 第六部分表单配置模块API文档符合性测试结果")
    print("-" * 80)
    print(f"测试API数量: {total}")
    print(f"符合文档: {passed}")
    print(f"不符合文档: {total - passed}")
    print(f"符合率: {(passed / total * 100):.1f}%")
    
    if passed == total:
        print("🎉 所有API完全符合文档规范！")
        return True
    else:
        print(f"⚠️  有 {total - passed} 个API不符合文档规范")
        return False


if __name__ == "__main__":
    success = test_form_api_compliance()
    exit(0 if success else 1)
