#!/usr/bin/env python3
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
测试审查批准和代码激活功能
"""

import requests
import json

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

def test_approve_activate():
    print("🔍 测试审查批准和代码激活...")
    print("=" * 50)
    
    # 使用已知的review_id和generation_id
    review_id = "review_gen_1753422199291_1753422438"
    generation_id = "gen_1753422199291"
    
    # 1. 测试审查批准
    print("\n1️⃣ 测试审查批准")
    approve_request = {
        "review_id": review_id,
        "approved": True,
        "approver": "developer",
        "comments": "代码质量良好，虽然有一些小问题但可以接受，批准通过"
    }
    
    approve_result = api_request("POST", "/api/code-review/approve", approve_request)
    
    if "error" in approve_result:
        print(f"❌ 审查批准失败: {approve_result['error']}")
    else:
        approve_data = approve_result.get("data", {})
        print(f"✅ 审查批准成功")
        print(f"   批准状态: {approve_data.get('status', 'Unknown')}")
        print(f"   批准时间: {approve_data.get('approved_at', 'Unknown')}")
        print(f"   批准意见: {approve_data.get('comments', 'Unknown')}")
    
    # 2. 查看审查状态
    print("\n2️⃣ 查看审查状态")
    status_result = api_request("GET", "/api/code-review/status")
    
    if "error" not in status_result:
        recent_reviews = status_result.get("data", {}).get("recent_reviews", [])
        if recent_reviews:
            latest_review = recent_reviews[0]
            print(f"✅ 最新审查记录:")
            print(f"   审查ID: {latest_review.get('review_id', 'Unknown')}")
            print(f"   生成ID: {latest_review.get('generation_id', 'Unknown')}")
            print(f"   状态: {latest_review.get('status', 'Unknown')}")
            print(f"   是否批准: {latest_review.get('approved', 'Unknown')}")
            print(f"   总体评分: {latest_review.get('overall_score', 'Unknown')}")
            print(f"   推荐: {latest_review.get('recommendation', 'Unknown')}")
    
    # 3. 测试代码激活
    print("\n3️⃣ 测试代码激活")
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
        print(f"   激活时间: {activate_data.get('activated_at', 'Unknown')}")
        
        if activate_data.get("endpoints"):
            print("   新增API端点:")
            for endpoint in activate_data.get("endpoints", [])[:10]:
                print(f"     - {endpoint}")
        
        if activate_data.get("database_applied"):
            print(f"   数据库迁移: {'已应用' if activate_data.get('database_applied') else '未应用'}")
        
        if activate_data.get("services_started"):
            print(f"   服务启动: {'已启动' if activate_data.get('services_started') else '未启动'}")
    
    # 4. 强制激活测试（如果需要）
    print("\n4️⃣ 测试强制激活（如果需要）")
    force_activate_request = {
        "generation_id": generation_id,
        "force_activate": True  # 强制激活，忽略审查状态
    }
    
    force_activate_result = api_request("POST", "/api/activate", force_activate_request)
    
    if "error" in force_activate_result:
        print(f"❌ 强制激活失败: {force_activate_result['error']}")
    else:
        force_activate_data = force_activate_result.get("data", {})
        print(f"✅ 强制激活成功")
        print(f"   激活状态: {force_activate_data.get('status', 'Unknown')}")
    
    print("\n" + "=" * 50)
    print("🎉 审查批准和代码激活测试完成!")
    print("=" * 50)

if __name__ == "__main__":
    test_approve_activate()
