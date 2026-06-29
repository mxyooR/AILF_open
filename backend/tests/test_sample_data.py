"""
测试模板示例数据功能
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def get_token():
    """获取开发者token"""
    try:
        with open("dev_token.txt", "r") as f:
            return f.read().strip()
    except:
        # 尝试生成新token
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "developer",
            "password": "dev123"
        })
        if response.status_code == 200:
            return response.json().get("data", {}).get("token")
        return None

def test_sample_data_info():
    """测试获取示例数据信息"""
    print("\n=== 测试获取示例数据信息 ===")
    token = get_token()
    if not token:
        print("❌ 无法获取token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试铁路售票模板
    response = requests.get(
        f"{BASE_URL}/templates/railway_ticketing/sample-data",
        headers=headers
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        sample_info = data.get("data", {})
        if sample_info.get("has_sample_data"):
            print(f"✅ 模板包含示例数据")
            print(f"   实体数: {sample_info.get('entity_count')}")
            print(f"   总记录数: {sample_info.get('total_records')}")
            return True
        else:
            print("❌ 模板不包含示例数据")
            return False
    else:
        print(f"❌ 请求失败: {response.text}")
        return False

def test_apply_template_without_sample_data():
    """测试应用模板（不导入示例数据）"""
    print("\n=== 测试应用模板（不导入示例数据）===")
    token = get_token()
    if not token:
        print("❌ 无法获取token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/templates/railway_ticketing/apply",
        headers=headers,
        json={
            "scenario_name": "测试铁路售票场景",
            "description": "测试示例数据功能",
            "import_sample_data": False
        }
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 模板应用成功")
        
        # 检查是否没有导入示例数据
        sample_import = data.get("data", {}).get("sample_data_import")
        if sample_import is None:
            print("✅ 未导入示例数据（符合预期）")
            return True
        else:
            print(f"⚠️ 意外导入了示例数据: {sample_import}")
            return False
    else:
        print(f"❌ 请求失败: {response.text}")
        return False

def test_apply_template_with_sample_data():
    """测试应用模板（导入示例数据）"""
    print("\n=== 测试应用模板（导入示例数据）===")
    token = get_token()
    if not token:
        print("❌ 无法获取token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/templates/railway_ticketing/apply",
        headers=headers,
        json={
            "scenario_name": "测试铁路售票场景2",
            "description": "测试示例数据导入功能",
            "import_sample_data": True
        }
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 模板应用成功")
        
        # 检查示例数据导入结果
        sample_import = data.get("data", {}).get("sample_data_import")
        if sample_import:
            print(f"✅ 示例数据导入结果:")
            print(f"   成功: {sample_import.get('success_count', 0)}")
            print(f"   跳过: {sample_import.get('skipped_count', 0)}")
            print(f"   失败: {sample_import.get('error_count', 0)}")
            return True
        else:
            print("❌ 未返回示例数据导入结果")
            return False
    else:
        print(f"❌ 请求失败: {response.text}")
        return False

def main():
    print("=" * 60)
    print("模板示例数据功能测试")
    print("=" * 60)
    
    results = []
    
    # 测试1: 获取示例数据信息
    results.append(("获取示例数据信息", test_sample_data_info()))
    
    # 测试2: 应用模板（不导入示例数据）
    results.append(("应用模板（不导入示例数据）", test_apply_template_without_sample_data()))
    
    # 测试3: 应用模板（导入示例数据）
    results.append(("应用模板（导入示例数据）", test_apply_template_with_sample_data()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
