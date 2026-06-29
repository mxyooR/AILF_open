#!/usr/bin/env python3
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
完整代码生成流程测试脚本
测试从场景配置到代码生成、审查、激活的完整流程
"""

import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def get_auth_headers() -> Dict[str, str]:
    """获取认证头"""
    try:
        with open("dev_token.txt", "r") as f:
            token = f.read().strip()
        return {"Authorization": f"Bearer {token}"}
    except FileNotFoundError:
        print("❌ 未找到dev_token.txt文件，请先运行 python generate_dev_token.py")
        return {}

def api_request(method: str, endpoint: str, data: Dict[Any, Any] = None) -> Dict[Any, Any]:
    """发送API请求"""
    headers = get_auth_headers()
    if not headers:
        return {"error": "无法获取认证token"}
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            return {"error": f"不支持的HTTP方法: {method}"}
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            return {"error": response.text, "status_code": response.status_code}
            
    except Exception as e:
        return {"error": str(e)}

def test_complete_generation_flow():
    """测试完整的代码生成流程"""
    print("🚀 开始测试完整代码生成流程...")
    print("=" * 60)
    
    # 1. 获取活跃场景
    print("\n1️⃣ 获取活跃场景配置")
    scenario_result = api_request("GET", "/api/scenario?include_details=true")
    
    if "error" in scenario_result:
        print(f"❌ 获取场景失败: {scenario_result['error']}")
        return
    
    scenario = scenario_result.get("data", {}).get("scenario", {})
    print(f"✅ 获取到活跃场景: {scenario.get('name', 'Unknown')}")
    print(f"   场景类型: {scenario.get('type', 'Unknown')}")
    print(f"   场景ID: {scenario.get('id', 'Unknown')}")
    
    # 2. 准备代码生成请求
    print("\n2️⃣ 准备代码生成请求")
    
    # 从场景配置中提取实体信息
    config = scenario.get("config", {})
    custom_settings = config.get("custom_settings", {})
    entities = custom_settings.get("entities", [])
    
    if not entities:
        print("❌ 场景中没有实体配置")
        return
    
    # 构建代码生成请求
    generation_request = {
        "project_name": f"generated_{scenario.get('type', 'project')}_{int(time.time())}",
        "description": f"基于{scenario.get('name', '场景')}自动生成的系统",
        "entities": entities,
        "options": {
            "include_tests": True,
            "include_docs": True,
            "framework": "fastapi",
            "database": "sqlite",
            "frontend": "amis"
        }
    }
    
    print(f"✅ 生成请求准备完成")
    print(f"   项目名称: {generation_request['project_name']}")
    print(f"   实体数量: {len(entities)}")
    print(f"   实体列表: {[entity['name'] for entity in entities]}")
    
    # 3. 执行完整系统生成
    print("\n3️⃣ 执行完整系统生成")
    generation_result = api_request("POST", "/api/generate-complete", generation_request)
    
    if "error" in generation_result:
        print(f"❌ 代码生成失败: {generation_result['error']}")
        print(f"   完整响应: {json.dumps(generation_result, ensure_ascii=False, indent=2)}")
        return
    
    generation_data = generation_result.get("data", {})
    generation_id = generation_data.get("generation_id")
    
    print(f"✅ 代码生成启动成功")
    print(f"   生成ID: {generation_id}")
    print(f"   目标目录: {generation_data.get('target_directory', 'Unknown')}")
    
    # 4. 监控生成状态
    print("\n4️⃣ 监控生成状态")
    max_wait_time = 300  # 最大等待5分钟
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        status_result = api_request("GET", "/api/generate/status")
        
        if "error" in status_result:
            print(f"❌ 获取状态失败: {status_result['error']}")
            break
        
        current_generation = status_result.get("data", {}).get("current_generation")
        
        if current_generation:
            status = current_generation.get("status", "unknown")
            print(f"   生成状态: {status}")
            
            if status == "completed":
                print("✅ 代码生成完成!")
                break
            elif status == "failed":
                print("❌ 代码生成失败!")
                print(f"   错误信息: {current_generation.get('error', 'Unknown error')}")
                return
        else:
            print("   没有正在进行的生成任务")
            break
        
        time.sleep(5)  # 等待5秒后再次检查
    
    # 5. 获取生成结果
    print("\n5️⃣ 获取生成结果")
    final_status = api_request("GET", "/api/generate/status")
    
    if "error" not in final_status:
        recent_generations = final_status.get("data", {}).get("recent_generations", [])
        if recent_generations:
            latest_generation = recent_generations[0]
            print(f"✅ 最新生成结果:")
            print(f"   生成ID: {latest_generation.get('generation_id', 'Unknown')}")
            print(f"   状态: {latest_generation.get('status', 'Unknown')}")
            print(f"   开始时间: {latest_generation.get('started_at', 'Unknown')}")
            print(f"   完成时间: {latest_generation.get('completed_at', 'Unknown')}")
            
            # 显示组件生成结果
            components = latest_generation.get("components", {})
            for component_name, component_info in components.items():
                success = component_info.get("success", False)
                status_icon = "✅" if success else "❌"
                print(f"   {status_icon} {component_name}: {'成功' if success else '失败'}")
                
                if success and component_info.get("files_generated"):
                    files = component_info.get("files_generated", [])
                    print(f"      生成文件: {len(files)} 个")
                    for file_path in files[:3]:  # 只显示前3个文件
                        print(f"        - {file_path}")
                    if len(files) > 3:
                        print(f"        ... 还有 {len(files) - 3} 个文件")
    
    # 6. 代码审查
    print("\n6️⃣ 执行代码审查")
    if generation_id:
        review_request = {
            "generation_id": generation_id,
            "check_types": ["security", "quality", "performance", "compliance"]
        }
        
        review_result = api_request("POST", "/api/code-review", review_request)
        
        if "error" in review_result:
            print(f"❌ 代码审查失败: {review_result['error']}")
        else:
            review_data = review_result.get("data", {})
            print(f"✅ 代码审查启动成功")
            print(f"   审查ID: {review_data.get('review_id', 'Unknown')}")
            
            # 等待审查完成
            print("   等待审查完成...")
            time.sleep(10)
            
            # 获取审查结果
            review_status = api_request("GET", "/api/code-review/status")
            if "error" not in review_status:
                recent_reviews = review_status.get("data", {}).get("recent_reviews", [])
                if recent_reviews:
                    latest_review = recent_reviews[0]
                    print(f"   审查状态: {latest_review.get('status', 'Unknown')}")
                    
                    results = latest_review.get("results", {})
                    for check_type, result in results.items():
                        passed = result.get("passed", False)
                        status_icon = "✅" if passed else "❌"
                        print(f"   {status_icon} {check_type}: {'通过' if passed else '未通过'}")
                        
                        if not passed and result.get("issues"):
                            issues = result.get("issues", [])
                            print(f"      发现 {len(issues)} 个问题")
    
    # 7. 代码激活（如果审查通过）
    print("\n7️⃣ 代码激活")
    if generation_id:
        activate_request = {
            "generation_id": generation_id,
            "force_activate": False  # 只有审查通过才激活
        }
        
        activate_result = api_request("POST", "/api/activate", activate_request)
        
        if "error" in activate_result:
            print(f"❌ 代码激活失败: {activate_result['error']}")
        else:
            activate_data = activate_result.get("data", {})
            print(f"✅ 代码激活成功")
            print(f"   激活状态: {activate_data.get('status', 'Unknown')}")
            
            if activate_data.get("endpoints"):
                print("   新增API端点:")
                for endpoint in activate_data.get("endpoints", [])[:5]:
                    print(f"     - {endpoint}")
    
    print("\n" + "=" * 60)
    print("🎉 完整代码生成流程测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_complete_generation_flow()
