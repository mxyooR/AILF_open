#!/usr/bin/env python3
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
使用已有生成项目测试代码审查流程
"""

import requests
import json
import time

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

def test_review_with_existing():
    print("🔍 使用已有项目测试代码审查流程...")
    print("=" * 60)
    
    # 使用最新的generation_id
    generation_id = "gen_1753422199291"
    
    print(f"\n📋 使用生成项目: {generation_id}")
    
    # 1. 执行代码审查
    print("\n1️⃣ 执行代码审查")
    review_request = {
        "generation_id": generation_id,
        "check_types": ["security", "quality", "performance", "compliance"]
    }
    
    review_result = api_request("POST", "/api/code-review", review_request)

    if "error" in review_result:
        print(f"❌ 代码审查失败: {review_result['error']}")
        return

    if not review_result.get("success", False):
        print(f"❌ 代码审查失败: API返回失败状态")
        return
    
    review_data = review_result.get("data", {})
    review_id = review_data.get("review_id")
    
    print(f"\n✅ 代码审查启动成功")
    print(f"   审查ID: {review_id}")
    
    # 2. 监控审查状态
    print("\n2️⃣ 监控审查状态")
    max_wait_time = 60  # 最大等待1分钟
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        print(f"\n   检查审查状态... ({int(time.time() - start_time)}s)")
        status_result = api_request("GET", "/api/code-review/status")
        
        if "error" in status_result:
            print(f"❌ 获取审查状态失败: {status_result['error']}")
            break
        
        current_review = status_result.get("data", {}).get("current_review")
        recent_reviews = status_result.get("data", {}).get("recent_reviews", [])
        
        if current_review:
            status = current_review.get("status", "unknown")
            print(f"   当前审查状态: {status}")
            
            if status == "completed":
                print("✅ 代码审查完成!")
                
                # 显示审查结果
                results = current_review.get("results", {})
                print("\n   📊 审查结果:")
                for check_type, result in results.items():
                    passed = result.get("passed", False)
                    status_icon = "✅" if passed else "❌"
                    print(f"   {status_icon} {check_type}: {'通过' if passed else '未通过'}")
                    
                    if not passed and result.get("issues"):
                        issues = result.get("issues", [])
                        print(f"      发现 {len(issues)} 个问题:")
                        for issue in issues[:3]:  # 只显示前3个问题
                            print(f"        - {issue.get('message', 'Unknown issue')}")
                        if len(issues) > 3:
                            print(f"        ... 还有 {len(issues) - 3} 个问题")
                
                break
            elif status == "failed":
                print("❌ 代码审查失败!")
                print(f"   错误信息: {current_review.get('error', 'Unknown error')}")
                return
        elif recent_reviews:
            # 检查最近的审查记录
            latest_review = recent_reviews[0]
            if latest_review.get("generation_id") == generation_id:
                print(f"   找到相关审查记录: {latest_review.get('status', 'unknown')}")
                if latest_review.get("status") == "completed":
                    print("✅ 审查已完成!")
                    review_id = latest_review.get("review_id")
                    break
        else:
            print("   没有正在进行的审查任务")
        
        time.sleep(5)  # 等待5秒后再次检查
    
    # 3. 测试审查批准
    print("\n3️⃣ 测试审查批准")
    if review_id:
        approve_request = {
            "review_id": review_id,
            "approved": True,
            "comments": "代码质量良好，批准通过"
        }
        
        approve_result = api_request("POST", "/api/code-review/approve", approve_request)
        
        if "error" in approve_result:
            print(f"❌ 审查批准失败: {approve_result['error']}")
        else:
            approve_data = approve_result.get("data", {})
            print(f"✅ 审查批准成功")
            print(f"   批准状态: {approve_data.get('status', 'Unknown')}")
            print(f"   批准时间: {approve_data.get('approved_at', 'Unknown')}")
    
    # 4. 测试代码激活
    print("\n4️⃣ 测试代码激活")
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
    
    # 5. 获取最终状态
    print("\n5️⃣ 获取最终状态")
    final_review_status = api_request("GET", "/api/code-review/status")
    
    if "error" not in final_review_status:
        recent_reviews = final_review_status.get("data", {}).get("recent_reviews", [])
        if recent_reviews:
            latest_review = recent_reviews[0]
            print(f"✅ 最新审查记录:")
            print(f"   审查ID: {latest_review.get('review_id', 'Unknown')}")
            print(f"   生成ID: {latest_review.get('generation_id', 'Unknown')}")
            print(f"   状态: {latest_review.get('status', 'Unknown')}")
            print(f"   是否批准: {latest_review.get('approved', 'Unknown')}")
            print(f"   审查时间: {latest_review.get('reviewed_at', 'Unknown')}")
    
    print("\n" + "=" * 60)
    print("🎉 代码审查流程测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_review_with_existing()
