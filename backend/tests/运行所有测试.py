"""
运行所有认证模块测试
按照API文档第一部分的规范执行完整测试
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from importlib import import_module


def run_all_auth_tests():
    """运行所有认证模块测试"""
    print("🚀 AILF 认证模块完整测试")
    print("=" * 60)
    print("📋 测试范围: API文档第一部分 - 认证模块")
    print("🔗 API端点:")
    print("   1. POST /api/auth/developer - 开发者认证")
    print("   2. POST /api/auth/developer/verify-token - 验证开发者令牌")
    print("=" * 60)
    
    # 测试结果统计
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    try:
        # 1.1 登录测试
        print("\n📝 1.1 登录测试")
        print("-" * 30)
        
        # 动态导入测试模块
        login_test_module = import_module("1.1登录测试")
        login_test = login_test_module.DeveloperLoginTest()
        
        # 运行登录测试
        token = login_test.run_all_tests()
        if token:
            passed_tests += 1
            print("✅ 1.1 登录测试 - 通过")
        else:
            failed_tests += 1
            print("❌ 1.1 登录测试 - 失败")
        total_tests += 1
        
        print("\n" + "=" * 60)
        
        # 1.2 认证测试
        print("\n📝 1.2 认证测试")
        print("-" * 30)
        
        # 动态导入测试模块
        verify_test_module = import_module("1.2认证测试")
        verify_test = verify_test_module.TokenVerificationTest()
        
        # 运行认证测试
        result = verify_test.run_all_tests()
        if result:
            passed_tests += 1
            print("✅ 1.2 认证测试 - 通过")
        else:
            failed_tests += 1
            print("❌ 1.2 认证测试 - 失败")
        total_tests += 1
        
    except ImportError as e:
        print(f"❌ 导入测试模块失败: {e}")
        failed_tests += 1
        total_tests += 1
    except Exception as e:
        print(f"❌ 运行测试时发生错误: {e}")
        failed_tests += 1
        total_tests += 1
    
    # 输出测试总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("-" * 30)
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {failed_tests}")
    print(f"成功率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
    
    if failed_tests == 0:
        print("\n🎉 所有测试通过！认证模块API完全符合文档规范！")
        print("✨ 可以继续实现下一个模块的API")
    else:
        print(f"\n⚠️  有 {failed_tests} 个测试失败，请检查并修复问题")
    
    print("=" * 60)
    
    return failed_tests == 0


def check_server_status():
    """检查服务器状态"""
    import requests
    
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务器状态: {data['data']['status']}")
            print(f"📅 服务器时间: {data['data']['timestamp']}")
            print(f"🔖 服务器版本: {data['data']['version']}")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        print("💡 请确保服务器在 http://localhost:5000 运行")
        print("🚀 启动命令: uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload")
        return False
    except Exception as e:
        print(f"❌ 检查服务器状态时发生错误: {e}")
        return False


def main():
    """主函数"""
    print("🔍 检查服务器状态...")
    if not check_server_status():
        print("\n❌ 服务器未运行，无法执行测试")
        return False
    
    print("\n" + "=" * 60)
    
    # 运行所有测试
    success = run_all_auth_tests()
    
    return success


if __name__ == "__main__":
    success = main()
    
    # 设置退出码
    sys.exit(0 if success else 1)
