"""
运行所有测试脚本
按顺序执行前四部分的所有测试
"""
import subprocess
import sys
import time
import requests


def check_server_status():
    """检查服务器状态"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器状态正常")
            return True
        else:
            print(f"❌ 服务器状态异常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到服务器: {e}")
        return False


def run_test_script(script_name, module_name):
    """运行单个测试脚本"""
    print(f"\n🧪 运行 {module_name}")
    print("-" * 50)
    
    try:
        # 运行测试脚本
        result = subprocess.run(
            [sys.executable, f"tests/{script_name}"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"✅ {module_name} - 测试通过")
            # 显示测试输出的关键信息
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if '✅' in line or '❌' in line or '🎉' in line:
                    print(f"   {line}")
            return True
        else:
            print(f"❌ {module_name} - 测试失败")
            print(f"   错误输出: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {module_name} - 测试超时")
        return False
    except Exception as e:
        print(f"❌ {module_name} - 运行异常: {e}")
        return False


def main():
    """主函数"""
    print("🚀 AILF前四部分完整测试套件")
    print("=" * 60)
    print("📋 测试覆盖范围:")
    print("   • 第一部分: 认证模块 (2个API端点)")
    print("   • 第二部分: 场景管理模块 (5个API端点)")
    print("   • 第三部分: 模板管理模块 (2个API端点)")
    print("   • 第四部分: 实体建模模块 (13个API端点)")
    print("   • 总计: 22个API端点")
    print("=" * 60)
    
    # 检查服务器状态
    if not check_server_status():
        print("❌ 服务器未启动，请先启动服务器")
        return False
    
    # 定义测试脚本列表
    test_scripts = [
        ("1.1登录测试.py", "第一部分 - 登录测试"),
        ("1.2认证测试.py", "第一部分 - 认证测试"),
        ("2.1场景管理测试.py", "第二部分 - 场景管理测试"),
        ("3.1模板管理测试.py", "第三部分 - 模板管理测试"),
        ("4.1实体建模测试.py", "第四部分 - 实体建模测试")
    ]
    
    # 测试结果统计
    total_tests = len(test_scripts)
    passed_tests = 0
    failed_tests = 0
    
    # 运行所有测试
    for script_name, module_name in test_scripts:
        if run_test_script(script_name, module_name):
            passed_tests += 1
        else:
            failed_tests += 1
        
        # 测试间隔
        time.sleep(1)
    
    # 显示测试总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("-" * 60)
    print(f"总测试模块: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {failed_tests}")
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"成功率: {success_rate:.1f}%")
    
    if failed_tests == 0:
        print("🎉 所有测试模块通过！前四部分API完全符合文档规范！")
        return True
    else:
        print(f"⚠️  有 {failed_tests} 个测试模块失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
