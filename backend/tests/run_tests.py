#!/usr/bin/env python3
"""
AILF 测试运行器
"""

import sys
import os
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_test(test_file):
    """运行单个测试文件"""
    print(f"🧪 运行测试: {test_file}")
    print("-" * 40)
    
    try:
        # 设置环境变量
        env = os.environ.copy()
        env['PYTHONPATH'] = str(project_root)
        
        # 运行测试
        result = subprocess.run([
            sys.executable, test_file
        ], cwd=project_root / "tests", capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            print("✅ 测试通过")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ 测试失败")
            if result.stderr:
                print("错误输出:")
                print(result.stderr)
            if result.stdout:
                print("标准输出:")
                print(result.stdout)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 运行测试时出错: {e}")
        return False

def main():
    print("🚀 AILF 测试运行器")
    print("=" * 50)
    
    # 可用的测试文件
    test_files = [
        "test_ai_integration.py",
        "test_ai_apis.py",
        "test_generation_api.py", 
        "test_complete_generation.py",
        "test_code_review.py",
        "test_approve_activate.py"
    ]
    
    if len(sys.argv) > 1:
        # 运行指定的测试
        test_name = sys.argv[1]
        if not test_name.endswith('.py'):
            test_name += '.py'
        
        if test_name in test_files:
            run_test(test_name)
        else:
            print(f"❌ 测试文件不存在: {test_name}")
            print(f"可用的测试文件: {', '.join(test_files)}")
    else:
        # 显示可用测试
        print("可用的测试文件:")
        for i, test_file in enumerate(test_files, 1):
            print(f"  {i}. {test_file}")
        
        print("\n使用方法:")
        print("  python run_tests.py test_ai_integration")
        print("  python run_tests.py test_ai_apis")

if __name__ == "__main__":
    main()
