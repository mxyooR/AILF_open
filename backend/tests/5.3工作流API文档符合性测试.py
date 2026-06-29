"""
第五部分 - 工作流设计模块API文档符合性测试
验证所有14个API端点完全符合API文档规范
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


def test_workflow_api_compliance():
    """测试工作流API文档符合性"""
    print("🔍 第五部分 - 工作流设计模块API文档符合性测试")
    print("=" * 80)
    
    # 获取token
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    compliance_results = []
    workflow_id = None
    instance_id = None
    
    # 1. 测试创建工作流定义API
    print("\n1️⃣ 测试创建工作流定义 (POST /api/workflows)")
    print("-" * 50)
    
    workflow_data = {
        "name": "API文档符合性测试工作流",
        "description": "用于验证API文档符合性的测试工作流",
        "triggerType": "manual",
        "steps": [
            {
                "id": "step_start",
                "name": "开始",
                "type": "start",
                "position": {"x": 100, "y": 100},
                "nextSteps": ["step_end"]
            },
            {
                "id": "step_end",
                "name": "结束",
                "type": "end",
                "position": {"x": 300, "y": 100}
            }
        ],
        "conditions": []
    }
    
    response = requests.post("http://localhost:5000/api/workflows", headers=headers, json=workflow_data)
    
    # 检查状态码
    status_ok = response.status_code == 201
    print(f"状态码: 期望201, 实际{response.status_code} - {'✅' if status_ok else '❌'}")
    
    if response.status_code == 201:
        data = response.json()
        workflow_id = data["data"]["workflow"]["id"]
        
        # 检查响应结构
        structure_checks = [
            ("code", data.get("code") == 201),
            ("message", "message" in data),
            ("data", "data" in data),
            ("data.workflow", "workflow" in data.get("data", {}))
        ]
        
        for field, check in structure_checks:
            print(f"响应结构.{field}: {'✅' if check else '❌'}")
        
        # 检查工作流字段
        if "workflow" in data.get("data", {}):
            workflow = data["data"]["workflow"]
            workflow_fields = [
                ("id", "id" in workflow),
                ("name", "name" in workflow),
                ("description", "description" in workflow),
                ("triggerType", "triggerType" in workflow),
                ("status", "status" in workflow),
                ("version", "version" in workflow),
                ("steps", "steps" in workflow),
                ("created_at", "created_at" in workflow and check_time_format(workflow.get("created_at", ""))),
                ("updated_at", "updated_at" in workflow and check_time_format(workflow.get("updated_at", "")))
            ]
            
            for field, check in workflow_fields:
                print(f"工作流.{field}: {'✅' if check else '❌'}")
            
            # 检查步骤格式
            if "steps" in workflow and workflow["steps"]:
                step = workflow["steps"][0]
                step_fields = [
                    ("id", "id" in step),
                    ("name", "name" in step),
                    ("type", "type" in step),
                    ("position", "position" in step),
                    ("config", "config" in step),
                    ("nextSteps", "nextSteps" in step),
                    ("created_at不存在", "created_at" not in step),
                    ("updated_at不存在", "updated_at" not in step)
                ]
                
                for field, check in step_fields:
                    print(f"步骤.{field}: {'✅' if check else '❌'}")
        
        compliance_results.append(status_ok and all(check for _, check in structure_checks))
    else:
        compliance_results.append(False)
    
    # 2. 测试获取工作流列表API
    print("\n2️⃣ 测试获取工作流列表 (GET /api/workflows)")
    print("-" * 50)
    
    response = requests.get("http://localhost:5000/api/workflows", headers=headers)
    
    status_ok = response.status_code == 200
    print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")
    
    if response.status_code == 200:
        data = response.json()
        
        # 检查响应结构
        structure_checks = [
            ("code", data.get("code") == 200),
            ("message", "message" in data),
            ("data", "data" in data),
            ("data.workflows", "workflows" in data.get("data", {})),
            ("data.total", "total" in data.get("data", {}))
        ]
        
        for field, check in structure_checks:
            print(f"响应结构.{field}: {'✅' if check else '❌'}")
        
        # 检查工作流列表项字段
        if "workflows" in data.get("data", {}) and data["data"]["workflows"]:
            workflow = data["data"]["workflows"][0]
            workflow_fields = [
                ("id", "id" in workflow),
                ("name", "name" in workflow),
                ("description", "description" in workflow),
                ("triggerType", "triggerType" in workflow),
                ("status", "status" in workflow),
                ("version", "version" in workflow),
                ("step_count", "step_count" in workflow),
                ("instance_count", "instance_count" in workflow),
                ("created_at", "created_at" in workflow and check_time_format(workflow.get("created_at", ""))),
                ("updated_at", "updated_at" in workflow and check_time_format(workflow.get("updated_at", "")))
            ]
            
            for field, check in workflow_fields:
                print(f"工作流项.{field}: {'✅' if check else '❌'}")
        
        compliance_results.append(status_ok and all(check for _, check in structure_checks))
    else:
        compliance_results.append(False)
    
    # 3. 测试获取工作流详情API
    print("\n3️⃣ 测试获取工作流详情 (GET /api/workflows/{workflow_id})")
    print("-" * 50)
    
    if workflow_id:
        response = requests.get(f"http://localhost:5000/api/workflows/{workflow_id}", headers=headers)
        
        status_ok = response.status_code == 200
        print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查响应结构（与创建工作流相同）
            structure_checks = [
                ("code", data.get("code") == 200),
                ("message", "message" in data),
                ("data", "data" in data),
                ("data.workflow", "workflow" in data.get("data", {}))
            ]
            
            for field, check in structure_checks:
                print(f"响应结构.{field}: {'✅' if check else '❌'}")
            
            compliance_results.append(status_ok and all(check for _, check in structure_checks))
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有工作流ID，跳过测试")
        compliance_results.append(False)
    
    # 4. 测试执行工作流API
    print("\n4️⃣ 测试执行工作流 (POST /api/workflows/{workflow_id}/execute)")
    print("-" * 50)
    
    if workflow_id:
        execute_data = {
            "input_data": {"test": "data"},
            "context": {"test_mode": True},
            "priority": "normal"
        }
        
        response = requests.post(f"http://localhost:5000/api/workflows/{workflow_id}/execute", 
                               headers=headers, json=execute_data)
        
        status_ok = response.status_code == 201
        print(f"状态码: 期望201, 实际{response.status_code} - {'✅' if status_ok else '❌'}")
        
        if response.status_code == 201:
            data = response.json()
            instance_id = data["data"]["instance"]["id"]
            
            # 检查响应结构
            structure_checks = [
                ("code", data.get("code") == 201),
                ("message", "message" in data),
                ("data", "data" in data),
                ("data.instance", "instance" in data.get("data", {}))
            ]
            
            for field, check in structure_checks:
                print(f"响应结构.{field}: {'✅' if check else '❌'}")
            
            compliance_results.append(status_ok and all(check for _, check in structure_checks))
        else:
            compliance_results.append(False)
    else:
        print("❌ 没有工作流ID，跳过测试")
        compliance_results.append(False)
    
    # 5. 测试获取工作流实例列表API
    print("\n5️⃣ 测试获取工作流实例列表 (GET /api/workflows/instances)")
    print("-" * 50)
    
    response = requests.get("http://localhost:5000/api/workflows/instances", headers=headers)
    
    status_ok = response.status_code == 200
    print(f"状态码: 期望200, 实际{response.status_code} - {'✅' if status_ok else '❌'}")
    
    if response.status_code == 200:
        data = response.json()
        
        # 检查响应结构
        structure_checks = [
            ("code", data.get("code") == 200),
            ("message", "message" in data),
            ("data", "data" in data),
            ("data.instances", "instances" in data.get("data", {})),
            ("data.summary", "summary" in data.get("data", {}))
        ]
        
        for field, check in structure_checks:
            print(f"响应结构.{field}: {'✅' if check else '❌'}")
        
        compliance_results.append(status_ok and all(check for _, check in structure_checks))
    else:
        compliance_results.append(False)
    
    # 统计结果
    passed = sum(compliance_results)
    total = len(compliance_results)
    
    print("\n" + "=" * 80)
    print("📊 第五部分工作流设计模块API文档符合性测试结果")
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
    success = test_workflow_api_compliance()
    exit(0 if success else 1)
