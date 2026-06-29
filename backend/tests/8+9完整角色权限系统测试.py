"""
第八+九部分 - 完整角色权限系统测试
全面验证角色管理和权限控制的完整功能
包括所有14个API端点的完整测试
"""
import requests
import json
import time
import subprocess
import sys


def get_auth_token():
    """获取认证令牌"""
    response = requests.post(
        "http://localhost:5000/api/auth/developer",
        json={"password": "AILF_DEV_2024_SECURE"}
    )
    return response.json()["data"]["token"]


def run_test_script(script_name):
    """运行测试脚本并返回结果"""
    try:
        print(f"\n🧪 运行测试脚本: {script_name}")
        print("-" * 60)
        
        result = subprocess.run([
            sys.executable, script_name
        ], capture_output=True, text=True, cwd=".")
        
        # 输出测试结果
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 运行测试脚本失败: {e}")
        return False


def test_complete_role_permission_system():
    """完整角色权限系统测试"""
    print("🔐 完整角色权限系统测试")
    print("=" * 100)
    print("全面验证角色管理和权限控制的完整功能")
    
    # 获取token验证服务器状态
    try:
        token = get_auth_token()
        print("✅ 服务器连接正常，认证成功")
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")
        return False
    
    test_results = []
    
    # 1. 运行角色管理基础测试
    print("\n" + "=" * 100)
    print("1️⃣ 第八部分 - 角色管理模块测试")
    print("=" * 100)
    
    role_basic_test = run_test_script("tests/8.1角色管理测试.py")
    test_results.append(("角色管理基础功能", role_basic_test))
    
    # 2. 运行角色管理API文档符合性测试
    print("\n" + "=" * 100)
    print("2️⃣ 第八部分 - 角色管理API文档符合性测试")
    print("=" * 100)
    
    role_compliance_test = run_test_script("tests/8.2完整API文档符合性测试.py")
    test_results.append(("角色管理API文档符合性", role_compliance_test))
    
    # 3. 运行动态数据库生成测试
    print("\n" + "=" * 100)
    print("3️⃣ 第八部分 - 动态数据库生成测试")
    print("=" * 100)
    
    db_generation_test = run_test_script("tests/8.3动态数据库生成测试.py")
    test_results.append(("动态数据库生成功能", db_generation_test))
    
    # 4. 运行权限控制基础测试
    print("\n" + "=" * 100)
    print("4️⃣ 第九部分 - 权限控制模块测试")
    print("=" * 100)
    
    permission_basic_test = run_test_script("tests/9.1权限控制测试.py")
    test_results.append(("权限控制基础功能", permission_basic_test))
    
    # 5. 运行权限控制API文档符合性测试
    print("\n" + "=" * 100)
    print("5️⃣ 第九部分 - 权限控制API文档符合性测试")
    print("=" * 100)
    
    permission_compliance_test = run_test_script("tests/9.2完整权限控制API文档符合性测试.py")
    test_results.append(("权限控制API文档符合性", permission_compliance_test))
    
    # 6. 运行联合集成测试
    print("\n" + "=" * 100)
    print("6️⃣ 第八+九部分 - 角色权限联合集成测试")
    print("=" * 100)
    
    integration_test = run_test_script("tests/8+9联合角色权限集成测试.py")
    test_results.append(("角色权限联合集成", integration_test))
    
    # 7. 手动验证核心功能
    print("\n" + "=" * 100)
    print("7️⃣ 手动验证核心功能")
    print("=" * 100)
    
    manual_test_result = manual_core_functionality_test()
    test_results.append(("手动核心功能验证", manual_test_result))
    
    # 统计总体结果
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    print("\n" + "=" * 100)
    print("📊 完整角色权限系统测试总结")
    print("=" * 100)
    
    print(f"总测试模块: {total_tests}")
    print(f"通过模块: {passed_tests}")
    print(f"失败模块: {total_tests - passed_tests}")
    print(f"总体成功率: {(passed_tests / total_tests * 100):.1f}%")
    
    print("\n📋 详细测试结果:")
    for test_name, result in test_results:
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎉 完整角色权限系统测试全部通过！")
        print("✅ 第八部分角色管理模块: 完全正常")
        print("✅ 第九部分权限控制模块: 完全正常")
        print("✅ 角色权限联合集成: 完全正常")
        print("✅ 动态数据库生成: 完全正常")
        print("✅ API文档符合性: 100%符合")
        print("✅ 核心功能验证: 完全通过")
        print("\n🚀 AILF系统角色权限管理能力已完全就绪！")
    else:
        print(f"\n⚠️  有 {total_tests - passed_tests} 个测试模块失败")
        print("请检查失败的模块并修复问题")
    
    return passed_tests == total_tests


def manual_core_functionality_test():
    """手动验证核心功能"""
    try:
        token = get_auth_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print("🔍 验证核心功能...")
        
        # 验证1: 角色列表获取
        roles_response = requests.get("http://localhost:5000/api/roles", headers=headers)
        if roles_response.status_code != 200:
            print("❌ 角色列表获取失败")
            return False
        
        roles_data = roles_response.json()
        role_count = len(roles_data["data"]["roles"])
        print(f"✅ 角色列表获取成功，角色数: {role_count}")
        
        # 验证2: 权限矩阵获取
        matrix_response = requests.get("http://localhost:5000/api/permissions/matrix", headers=headers)
        if matrix_response.status_code != 200:
            print("❌ 权限矩阵获取失败")
            return False
        
        matrix_data = matrix_response.json()
        api_count = matrix_data["data"]["statistics"]["total_apis"]
        coverage = matrix_data["data"]["statistics"]["coverage"]
        print(f"✅ 权限矩阵获取成功，API数: {api_count}，覆盖率: {coverage}%")
        
        # 验证3: 权限检查功能
        permission_check = {
            "user_id": "test_user",
            "resource": "products",
            "action": "read"
        }
        
        check_response = requests.post("http://localhost:5000/api/permissions/check", 
                                     headers=headers, json=permission_check)
        if check_response.status_code not in [200, 403]:
            print("❌ 权限检查功能异常")
            return False
        
        print("✅ 权限检查功能正常")
        
        # 验证4: 用户API访问列表
        user_apis_response = requests.get("http://localhost:5000/api/permissions/user-apis?user_id=user_001", 
                                        headers=headers)
        if user_apis_response.status_code != 200:
            print("❌ 用户API访问列表获取失败")
            return False
        
        user_apis_data = user_apis_response.json()
        accessible_apis = user_apis_data["data"]["summary"]["total_apis"]
        print(f"✅ 用户API访问列表获取成功，可访问API数: {accessible_apis}")
        
        print("✅ 所有核心功能验证通过")
        return True
        
    except Exception as e:
        print(f"❌ 核心功能验证异常: {e}")
        return False


def check_system_status():
    """检查系统状态"""
    print("🔍 检查系统状态...")
    
    try:
        # 检查服务器是否运行
        response = requests.get("http://localhost:5000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器正常运行")
        else:
            print(f"⚠️ 服务器响应异常: {response.status_code}")
            
        # 检查认证是否正常
        token = get_auth_token()
        print("✅ 认证系统正常")
        
        # 检查数据库连接
        headers = {"Authorization": f"Bearer {token}"}
        db_response = requests.get("http://localhost:5000/api/roles?limit=1", headers=headers)
        if db_response.status_code == 200:
            print("✅ 数据库连接正常")
        else:
            print("❌ 数据库连接异常")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 系统状态检查失败: {e}")
        return False


if __name__ == "__main__":
    print("🚀 启动完整角色权限系统测试...")
    
    # 首先检查系统状态
    if not check_system_status():
        print("❌ 系统状态检查失败，请确保服务器正常运行")
        exit(1)
    
    # 运行完整测试
    success = test_complete_role_permission_system()
    
    if success:
        print("\n🎉 完整角色权限系统测试成功完成！")
        print("🚀 AILF系统已具备完整的企业级角色权限管理能力！")
    else:
        print("\n❌ 完整角色权限系统测试存在问题！")
        print("请检查失败的测试模块并修复问题")
    
    exit(0 if success else 1)
