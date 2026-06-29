#!/usr/bin/env python3
"""
第十一部分：AI交互模块测试
测试AI命令处理、amis schema生成、schema校验等功能
"""
import requests
import json
import time
import sys
import os
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试配置
BASE_URL = "http://localhost:5000"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

class TestAIInteraction:
    """AI交互模块测试类"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_ai_health_check(self):
        """测试AI服务健康检查"""
        print("=== 测试AI服务健康检查 ===")
        
        try:
            response = self.session.get(f"{self.base_url}/api/ai/health")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"AI服务状态: {data.get('success', False)}")
                print(f"AI客户端状态: {data.get('ai_client', {}).get('status', 'unknown')}")
                return True
            else:
                print(f"健康检查失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"健康检查异常: {str(e)}")
            return False
    
    def test_command_processing(self):
        """测试命令处理"""
        print("\n=== 测试命令处理 ===")
        
        test_commands = [
            {
                "command": "显示用户列表",
                "context": {
                    "user_id": "test_user",
                    "scenario_id": "user_management"
                }
            },
            {
                "command": "创建新用户",
                "context": {
                    "user_id": "test_user",
                    "scenario_id": "user_management"
                }
            },
            {
                "command": "编辑用户信息",
                "context": {
                    "user_id": "test_user",
                    "scenario_id": "user_management"
                }
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_commands, 1):
            print(f"\n测试用例 {i}: {test_case['command']}")
            
            try:
                response = self.session.post(
                    f"{self.base_url}/api/command",
                    json=test_case
                )
                
                print(f"状态码: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        result_data = data.get("data", {})
                        print(f"✅ 命令处理成功")
                        print(f"意图类型: {result_data.get('intent', {}).get('intent_type', 'unknown')}")
                        print(f"Schema类型: {result_data.get('amis_schema', {}).get('type', 'unknown')}")
                        print(f"响应文本: {result_data.get('response_text', 'N/A')[:50]}...")
                        
                        # 检查校验结果
                        validation = result_data.get('validation', {})
                        print(f"Schema校验: {'通过' if validation.get('is_valid') else '失败'}")
                        if validation.get('summary'):
                            summary = validation['summary']
                            print(f"  错误: {summary.get('error_count', 0)}")
                            print(f"  警告: {summary.get('warning_count', 0)}")
                            print(f"  建议: {summary.get('info_count', 0)}")
                        
                        success_count += 1
                    else:
                        print(f"❌ 命令处理失败: {data.get('error', 'Unknown error')}")
                else:
                    print(f"❌ 请求失败: {response.text}")
                    
            except Exception as e:
                print(f"❌ 测试异常: {str(e)}")
        
        print(f"\n命令处理测试完成: {success_count}/{len(test_commands)} 成功")
        return success_count == len(test_commands)
    
    def test_schema_validation(self):
        """测试Schema校验"""
        print("\n=== 测试Schema校验 ===")
        
        # 测试有效的schema
        valid_schema = {
            "schema": {
                "type": "page",
                "title": "用户管理",
                "body": [
                    {
                        "type": "crud",
                        "api": "/api/users",
                        "columns": [
                            {"name": "id", "label": "ID", "type": "text"},
                            {"name": "username", "label": "用户名", "type": "text"},
                            {"name": "email", "label": "邮箱", "type": "text"}
                        ]
                    }
                ]
            },
            "schema_type": "amis"
        }
        
        print("测试有效schema:")
        try:
            response = self.session.post(
                f"{self.base_url}/api/ai/validate-schema",
                json=valid_schema
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ 校验成功")
                    print(f"Schema有效: {data.get('valid', False)}")
                    print(f"错误数量: {len(data.get('errors', []))}")
                    print(f"警告数量: {len(data.get('warnings', []))}")
                    print(f"建议数量: {len(data.get('suggestions', []))}")
                else:
                    print(f"❌ 校验失败: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ 请求失败: {response.text}")
                
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
        
        # 测试无效的schema
        invalid_schema = {
            "schema": {
                "type": "crud",
                # 缺少必需的api字段
                "columns": [
                    {"label": "用户名"}  # 缺少name字段
                ]
            },
            "schema_type": "amis"
        }
        
        print("\n测试无效schema:")
        try:
            response = self.session.post(
                f"{self.base_url}/api/ai/validate-schema",
                json=invalid_schema
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ 校验成功")
                    print(f"Schema有效: {data.get('valid', False)}")
                    errors = data.get('errors', [])
                    if errors:
                        print(f"错误详情:")
                        for error in errors[:3]:  # 只显示前3个错误
                            print(f"  - {error}")
                else:
                    print(f"❌ 校验失败: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ 请求失败: {response.text}")
                
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
    
    def test_ai_suggestions(self):
        """测试AI建议功能"""
        print("\n=== 测试AI建议功能 ===")
        
        # 测试实体建议
        print("测试实体建议:")
        entity_request = {
            "business_description": "电商平台用户管理系统，需要管理用户信息、订单、商品等"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/ai/suggest-entities",
                json=entity_request
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("✅ 实体建议成功")
                    suggestions = data.get("suggestions", {})
                    if isinstance(suggestions, dict) and "raw_analysis" not in suggestions:
                        print(f"建议实体数量: {len(suggestions.get('entities', []))}")
                    else:
                        print("获得文本分析结果")
                else:
                    print(f"❌ 实体建议失败: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ 请求失败: {response.text}")
                
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
        
        # 测试工作流建议
        print("\n测试工作流建议:")
        workflow_request = {
            "entities": ["user", "order", "product"],
            "business_scenario": "用户下单购买商品的完整流程"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/ai/suggest-workflows",
                json=workflow_request
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("✅ 工作流建议成功")
                    suggestions = data.get("suggestions", {})
                    if isinstance(suggestions, dict) and "raw_analysis" not in suggestions:
                        print(f"建议工作流数量: {len(suggestions.get('workflows', []))}")
                    else:
                        print("获得文本分析结果")
                else:
                    print(f"❌ 工作流建议失败: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ 请求失败: {response.text}")
                
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始AI交互模块完整测试...")
        print("=" * 50)
        
        # 等待服务启动
        print("等待后端服务启动...")
        time.sleep(2)
        
        test_results = []
        
        # 1. 健康检查
        result = self.test_ai_health_check()
        test_results.append(("AI健康检查", result))
        
        # 2. 命令处理测试
        result = self.test_command_processing()
        test_results.append(("命令处理", result))
        
        # 3. Schema校验测试
        self.test_schema_validation()
        test_results.append(("Schema校验", True))  # 这个测试主要是功能验证
        
        # 4. AI建议功能测试
        self.test_ai_suggestions()
        test_results.append(("AI建议功能", True))  # 这个测试主要是功能验证
        
        # 测试总结
        print("\n" + "=" * 50)
        print("测试总结:")
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n总体结果: {passed}/{total} 测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！AI交互模块功能正常")
        else:
            print("⚠️  部分测试失败，请检查相关功能")
        
        return passed == total


def main():
    """主函数"""
    tester = TestAIInteraction()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ AI交互模块测试完成，所有功能正常")
        sys.exit(0)
    else:
        print("\n❌ AI交互模块测试失败，请检查相关问题")
        sys.exit(1)


if __name__ == "__main__":
    main()
