#!/usr/bin/env python3
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AI API测试脚本
测试所有AI相关的API端点
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_api_endpoint(method: str, endpoint: str, data: Dict[Any, Any] = None, headers: Dict[str, str] = None) -> Dict[Any, Any]:
    """测试API端点"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            print(f"❌ 不支持的HTTP方法: {method}")
            return {"error": f"不支持的HTTP方法: {method}"}
        
        print(f"📡 {method.upper()} {endpoint}")
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result
        else:
            print(f"❌ 失败: {response.text}")
            return {"error": response.text, "status_code": response.status_code}
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return {"error": str(e)}

def get_auth_token() -> str:
    """获取认证token"""
    print("🔐 获取认证token...")

    # 从文件读取开发者token
    try:
        with open("dev_token.txt", "r") as f:
            token = f.read().strip()
        print(f"✅ 从文件获取到token: {token[:20]}...")
        return token
    except FileNotFoundError:
        print("❌ 未找到dev_token.txt文件，请先运行 python generate_dev_token.py")
        return ""

def test_ai_apis():
    """测试AI相关的API"""
    print("🤖 开始测试AI API...")
    print("=" * 50)
    
    # 获取认证token
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    print("\n" + "=" * 50)
    print("🧪 测试AI交互模块")
    print("=" * 50)
    
    # 1. 测试AI健康检查
    print("\n1️⃣ 测试AI健康检查")
    test_api_endpoint("GET", "/api/ai/health", headers=headers)
    
    # 2. 测试命令处理
    print("\n2️⃣ 测试命令处理")
    command_data = {
        "command": "创建一个用户管理系统",
        "context": {
            "user_id": "test_user",
            "scenario_id": "user_management"
        }
    }
    test_api_endpoint("POST", "/api/command", command_data, headers)
    
    # 3. 测试AI代码生成
    print("\n3️⃣ 测试AI代码生成")
    code_gen_data = {
        "prompt": "生成一个用户注册的Python函数",
        "language": "python",
        "context": "用户管理系统"
    }
    test_api_endpoint("POST", "/api/ai/generate-code", code_gen_data, headers)
    
    # 4. 测试实体推荐
    print("\n4️⃣ 测试实体推荐")
    entity_data = {
        "domain": "电商系统",
        "description": "需要管理商品、订单、用户"
    }
    test_api_endpoint("POST", "/api/ai/suggest-entities", entity_data, headers)
    
    # 5. 测试工作流推荐
    print("\n5️⃣ 测试工作流推荐")
    workflow_data = {
        "domain": "订单处理",
        "requirements": ["创建订单", "支付处理", "发货", "确认收货"]
    }
    test_api_endpoint("POST", "/api/ai/suggest-workflows", workflow_data, headers)
    
    # 6. 测试API推荐
    print("\n6️⃣ 测试API推荐")
    api_data = {
        "entities": ["User", "Product", "Order"],
        "operations": ["CRUD", "search", "filter"]
    }
    test_api_endpoint("POST", "/api/ai/suggest-apis", api_data, headers)
    
    print("\n" + "=" * 50)
    print("🏗️ 测试代码生成模块")
    print("=" * 50)
    
    # 7. 测试完整系统生成
    print("\n7️⃣ 测试完整系统生成")
    complete_gen_data = {
        "project_name": "test_ecommerce",
        "description": "简单的电商系统",
        "entities": [
            {
                "name": "Product",
                "fields": [
                    {"name": "name", "type": "string"},
                    {"name": "price", "type": "decimal"},
                    {"name": "description", "type": "text"}
                ]
            }
        ],
        "options": {
            "include_tests": True,
            "include_docs": True,
            "framework": "fastapi"
        }
    }
    test_api_endpoint("POST", "/api/generate-complete", complete_gen_data, headers)
    
    # 8. 测试生成状态查询
    print("\n8️⃣ 测试生成状态查询")
    test_api_endpoint("GET", "/api/generate/status", headers=headers)
    
    print("\n" + "=" * 50)
    print("🔍 测试代码审查模块")
    print("=" * 50)
    
    # 9. 测试代码审查
    print("\n9️⃣ 测试代码审查")
    review_data = {
        "project_path": "./generated/test_ecommerce",
        "check_types": ["security", "quality", "performance"]
    }
    test_api_endpoint("POST", "/api/code-review", review_data, headers)
    
    # 10. 测试审查状态查询
    print("\n🔟 测试审查状态查询")
    test_api_endpoint("GET", "/api/code-review/status", headers=headers)
    
    print("\n" + "=" * 50)
    print("🎉 AI API测试完成!")
    print("=" * 50)

if __name__ == "__main__":
    test_ai_apis()
