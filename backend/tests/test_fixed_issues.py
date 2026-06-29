#!/usr/bin/env python3
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
修复后的审查批准和代码激活测试
"""

import requests
import json
import os
import shutil

BASE_URL = "http://localhost:8000"

def get_auth_headers():
    try:
        with open("dev_token.txt", "r") as f:
            token = f.read().strip()
        return {"Authorization": f"Bearer {token}"}
    except FileNotFoundError:
        return {}

def api_request(method: str, endpoint: str, data=None):
    headers = get_auth_headers()
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            return {"error": f"不支持的HTTP方法: {method}"}
        
        print(f"📡 {method.upper()} {endpoint}")
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ 成功")
            return result
        else:
            print(f"❌ 失败: {response.text}")
            return {"error": response.text, "status_code": response.status_code}
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return {"error": str(e)}

def test_fixed_issues():
    print("🔧 测试修复后的审查批准和代码激活...")
    print("=" * 60)
    
    # 使用已知的ID
    review_id = "review_gen_1753422199291_1753422438"
    generation_id = "gen_1753422199291"
    
    # 1. 修复路径问题 - 确保代码在正确位置
    print("\n1️⃣ 修复路径问题")
    source_dir = f"./generated/{generation_id}"
    target_dir = f"/tmp/generated/{generation_id}"
    
    if os.path.exists(source_dir):
        # 创建目标目录
        os.makedirs("/tmp/generated", exist_ok=True)
        
        # 如果目标不存在，复制代码
        if not os.path.exists(target_dir):
            shutil.copytree(source_dir, target_dir)
            print(f"✅ 已复制代码到激活路径: {target_dir}")
        else:
            print(f"✅ 激活路径已存在: {target_dir}")
    else:
        print(f"❌ 源代码路径不存在: {source_dir}")
        return
    
    # 2. 测试审查批准（修复逻辑）
    print("\n2️⃣ 测试审查批准")
    approve_request = {
        "review_id": review_id,
        "approved": True,
        "approver": "developer",
        "comments": "代码质量良好，批准通过"
    }
    
    approve_result = api_request("POST", "/api/code-review/approve", approve_request)
    
    # 修复的逻辑：正确检查响应
    if "error" in approve_result:
        print(f"❌ 审查批准失败: {approve_result['error']}")
    else:
        # 检查API响应的success字段
        if approve_result.get("success", False):
            approve_data = approve_result.get("data", {})
            print(f"✅ 审查批准成功")
            print(f"   审查ID: {approve_data.get('review_id', 'Unknown')}")
            print(f"   生成ID: {approve_data.get('generation_id', 'Unknown')}")
            print(f"   批准状态: {approve_data.get('approval', {}).get('approved', 'Unknown')}")
            print(f"   批准人: {approve_data.get('approval', {}).get('approver', 'Unknown')}")
            print(f"   批准时间: {approve_data.get('approval', {}).get('approved_at', 'Unknown')}")
        else:
            print(f"❌ 审查批准失败: {approve_result.get('error', 'Unknown error')}")
    
    # 3. 查看审查状态
    print("\n3️⃣ 查看审查状态")
    status_result = api_request("GET", "/api/code-review/status")
    
    if "error" not in status_result and status_result.get("success", False):
        recent_reviews = status_result.get("data", {}).get("recent_reviews", [])
        if recent_reviews:
            latest_review = recent_reviews[0]
            print(f"✅ 最新审查记录:")
            print(f"   审查ID: {latest_review.get('review_id', 'Unknown')}")
            print(f"   生成ID: {latest_review.get('generation_id', 'Unknown')}")
            print(f"   状态: {latest_review.get('status', 'Unknown')}")
            print(f"   是否批准: {latest_review.get('approval', {}).get('approved', 'Unknown')}")
            print(f"   总体评分: {latest_review.get('overall_score', 'Unknown')}")
            print(f"   推荐: {latest_review.get('recommendation', 'Unknown')}")
        else:
            print("⚠️  没有找到审查记录")
    
    # 4. 测试代码激活（修复路径后）
    print("\n4️⃣ 测试代码激活")
    activate_request = {
        "generation_id": generation_id,
        "force_activate": False
    }
    
    activate_result = api_request("POST", "/api/activate", activate_request)
    
    if "error" in activate_result:
        print(f"❌ 代码激活失败: {activate_result['error']}")
    else:
        # 检查API响应的success字段
        if activate_result.get("success", False):
            activate_data = activate_result.get("data", {})
            activation_info = activate_data.get("activation", {})
            
            print(f"✅ 代码激活成功")
            print(f"   生成ID: {activation_info.get('generation_id', 'Unknown')}")
            print(f"   激活状态: {activation_info.get('status', 'Unknown')}")
            print(f"   激活时间: {activation_info.get('activated_at', 'Unknown')}")
            
            # 显示服务状态
            services = activation_info.get("services", {})
            print(f"   服务状态:")
            for service_name, service_info in services.items():
                status = "✅" if service_info.get("success", False) else "❌"
                print(f"     {status} {service_name}: {'成功' if service_info.get('success', False) else '失败'}")
            
            # 显示端点信息
            endpoints = activation_info.get("endpoints", {})
            if endpoints and endpoints.get("success", False):
                print(f"   API端点:")
                print(f"     - API基础URL: {endpoints.get('api_base', 'Unknown')}")
                print(f"     - API文档: {endpoints.get('api_docs', 'Unknown')}")
                print(f"     - 验证的端点数: {endpoints.get('endpoints_validated', 0)}")
            
            # 显示错误（如果有）
            errors = activation_info.get("errors", [])
            if errors:
                print(f"   警告/错误:")
                for error in errors:
                    print(f"     ⚠️  {error}")
        else:
            error = activate_result.get("error", "Unknown error")
            print(f"❌ 代码激活失败: {error}")
            
            # 显示详细错误信息
            if "data" in activate_result:
                errors = activate_result["data"].get("errors", [])
                if errors:
                    print(f"   详细错误:")
                    for error in errors:
                        print(f"     - {error}")
    
    # 5. 测试强制激活
    print("\n5️⃣ 测试强制激活")
    force_activate_request = {
        "generation_id": generation_id,
        "force_activate": True
    }
    
    force_result = api_request("POST", "/api/activate", force_activate_request)
    
    if "error" in force_result:
        print(f"❌ 强制激活失败: {force_result['error']}")
    else:
        if force_result.get("success", False):
            print(f"✅ 强制激活成功")
        else:
            print(f"❌ 强制激活失败: {force_result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 60)
    print("🎉 修复测试完成!")
    print("=" * 60)
    
    # 6. 总结问题和解决方案
    print("\n📋 问题总结:")
    print("1. 审查批准'失败'问题:")
    print("   - 原因: 测试脚本逻辑错误，没有正确检查API响应")
    print("   - 解决: 修复响应检查逻辑，正确解析success字段")
    print("")
    print("2. 代码激活'generation_not_found'问题:")
    print("   - 原因: 路径配置不匹配")
    print("   - 代码生成路径: ./generated/{generation_id}")
    print("   - 激活服务期望: /tmp/generated/{generation_id}")
    print("   - 解决: 复制代码到期望路径或修改配置")

if __name__ == "__main__":
    test_fixed_issues()
