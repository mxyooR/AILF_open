"""
第五部分 - 工作流设计模块测试
测试工作流定义、执行和步骤管理的14个API端点
"""
import requests
import json
import time
from typing import Dict, Any, Optional


class WorkflowDesignTest:
    """工作流设计模块测试类"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.token = None
        self.test_workflow_id = None
        self.test_instance_id = None
        
    def get_auth_token(self) -> bool:
        """获取认证令牌"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/developer",
                json={"password": "AILF_DEV_2024_SECURE"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["data"]["token"]
                return True
            else:
                print(f"❌ 获取令牌失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 获取令牌异常: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    # 工作流定义管理测试 (5个API端点)
    
    def test_create_workflow(self) -> bool:
        """测试创建工作流定义"""
        try:
            workflow_data = {
                "name": "订单处理流程",
                "description": "从下单到完成的完整订单处理流程",
                "triggerType": "manual",
                "steps": [
                    {
                        "id": "step_start",
                        "name": "开始",
                        "type": "start",
                        "position": {"x": 100, "y": 100},
                        "nextSteps": ["step_create_order"]
                    },
                    {
                        "id": "step_create_order",
                        "name": "创建订单",
                        "type": "form",
                        "position": {"x": 300, "y": 100},
                        "config": {
                            "formConfig": {
                                "entity": "order",
                                "fields": ["customer_name", "products", "total_amount"]
                            }
                        },
                        "nextSteps": ["step_payment"]
                    },
                    {
                        "id": "step_payment",
                        "name": "支付处理",
                        "type": "api_call",
                        "position": {"x": 500, "y": 100},
                        "config": {
                            "apiConfig": {
                                "endpoint": "/api/payment/process",
                                "method": "POST",
                                "params": {
                                    "order_id": "{{step_create_order.order_id}}",
                                    "amount": "{{step_create_order.total_amount}}"
                                }
                            }
                        },
                        "nextSteps": ["step_end"]
                    },
                    {
                        "id": "step_end",
                        "name": "结束",
                        "type": "end",
                        "position": {"x": 700, "y": 100}
                    }
                ],
                "conditions": [
                    {
                        "id": "payment_success",
                        "expression": "payment.status === \"success\"",
                        "action": "continue"
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/api/workflows",
                headers=self.get_headers(),
                json=workflow_data
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.test_workflow_id = data["data"]["workflow"]["id"]
                print(f"✅ 创建工作流成功: {self.test_workflow_id}")
                return True
            else:
                print(f"❌ 创建工作流失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 创建工作流异常: {e}")
            return False
    
    def test_get_workflows_list(self) -> bool:
        """测试获取工作流列表"""
        try:
            response = requests.get(
                f"{self.base_url}/api/workflows?status=active&page=1&limit=10",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                workflows = data["data"]["workflows"]
                total = data["data"]["total"]
                print(f"✅ 获取工作流列表成功: {len(workflows)}个工作流，总计{total}个")
                return True
            else:
                print(f"❌ 获取工作流列表失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 获取工作流列表异常: {e}")
            return False
    
    def test_get_workflow_detail(self) -> bool:
        """测试获取工作流详情"""
        if not self.test_workflow_id:
            print("❌ 没有可用的工作流ID")
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/api/workflows/{self.test_workflow_id}",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                workflow = data["data"]["workflow"]
                print(f"✅ 获取工作流详情成功: {workflow['name']} ({len(workflow['steps'])}个步骤)")
                return True
            else:
                print(f"❌ 获取工作流详情失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 获取工作流详情异常: {e}")
            return False
    
    def test_update_workflow(self) -> bool:
        """测试更新工作流定义"""
        if not self.test_workflow_id:
            print("❌ 没有可用的工作流ID")
            return False
            
        try:
            update_data = {
                "description": "更新后的订单处理流程描述",
                "status": "active"
            }
            
            response = requests.put(
                f"{self.base_url}/api/workflows/{self.test_workflow_id}",
                headers=self.get_headers(),
                json=update_data
            )
            
            if response.status_code == 200:
                data = response.json()
                workflow = data["data"]["workflow"]
                print(f"✅ 更新工作流成功: {workflow['description']}")
                return True
            else:
                print(f"❌ 更新工作流失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 更新工作流异常: {e}")
            return False
    
    def test_execute_workflow(self) -> bool:
        """测试执行工作流"""
        if not self.test_workflow_id:
            print("❌ 没有可用的工作流ID")
            return False
            
        try:
            execute_data = {
                "input_data": {
                    "customer_id": "customer_123",
                    "products": [
                        {"id": "product_1", "quantity": 2, "price": 99.99}
                    ]
                },
                "context": {
                    "user_id": "user_456",
                    "session_id": "session_789",
                    "priority": "normal"
                },
                "priority": "normal"
            }
            
            response = requests.post(
                f"{self.base_url}/api/workflows/{self.test_workflow_id}/execute",
                headers=self.get_headers(),
                json=execute_data
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                instance = data["data"]["instance"]
                self.test_instance_id = instance["id"]
                print(f"✅ 执行工作流成功: {self.test_instance_id} (状态: {instance['status']})")
                return True
            else:
                print(f"❌ 执行工作流失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 执行工作流异常: {e}")
            return False
    
    def test_get_workflow_instances(self) -> bool:
        """测试获取工作流实例列表"""
        try:
            response = requests.get(
                f"{self.base_url}/api/workflows/instances?page=1&limit=10&sort=created_at",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                instances = data["data"]["instances"]
                pagination = data["data"]["pagination"]
                summary = data["data"]["summary"]
                print(f"✅ 获取工作流实例列表成功: {len(instances)}个实例，总计{summary['total_instances']}个")
                return True
            else:
                print(f"❌ 获取工作流实例列表失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 获取工作流实例列表异常: {e}")
            return False
    
    def test_get_workflow_instance_detail(self) -> bool:
        """测试获取工作流实例详情"""
        if not self.test_instance_id:
            print("❌ 没有可用的实例ID")
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/api/workflows/instances/{self.test_instance_id}",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                instance = data["data"]["instance"]
                print(f"✅ 获取工作流实例详情成功: {instance['workflow_name']} (进度: {instance['progress']['percentage']}%)")
                return True
            else:
                print(f"❌ 获取工作流实例详情失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 获取工作流实例详情异常: {e}")
            return False
    
    def test_get_workflow_steps(self) -> bool:
        """测试获取工作流步骤列表"""
        if not self.test_workflow_id:
            print("❌ 没有可用的工作流ID")
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/api/workflows/{self.test_workflow_id}/steps",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                steps = data["data"]["steps"]
                print(f"✅ 获取工作流步骤列表成功: {len(steps)}个步骤")
                return True
            else:
                print(f"❌ 获取工作流步骤列表失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 获取工作流步骤列表异常: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 开始运行工作流设计模块测试...")
        print("=" * 50)
        
        # 获取认证令牌
        if not self.get_auth_token():
            return False
        
        test_results = []
        
        # 工作流定义管理测试
        print("\n📋 工作流定义管理测试")
        print("-" * 30)
        
        print("🧪 测试创建工作流定义...")
        test_results.append(self.test_create_workflow())
        
        print("🧪 测试获取工作流列表...")
        test_results.append(self.test_get_workflows_list())
        
        print("🧪 测试获取工作流详情...")
        test_results.append(self.test_get_workflow_detail())
        
        print("🧪 测试更新工作流定义...")
        test_results.append(self.test_update_workflow())
        
        # 工作流执行管理测试
        print("\n⚡ 工作流执行管理测试")
        print("-" * 30)
        
        print("🧪 测试执行工作流...")
        test_results.append(self.test_execute_workflow())
        
        print("🧪 测试获取工作流实例列表...")
        test_results.append(self.test_get_workflow_instances())
        
        print("🧪 测试获取工作流实例详情...")
        test_results.append(self.test_get_workflow_instance_detail())
        
        # 工作流步骤管理测试
        print("\n🔧 工作流步骤管理测试")
        print("-" * 30)
        
        print("🧪 测试获取工作流步骤列表...")
        test_results.append(self.test_get_workflow_steps())
        
        # 统计结果
        passed = sum(test_results)
        total = len(test_results)
        
        print("\n" + "=" * 50)
        if passed == total:
            print("🎉 工作流设计模块测试全部通过！")
            print(f"📊 测试统计: {passed}/{total} 通过")
            return True
        else:
            print(f"⚠️  部分测试失败: {passed}/{total} 通过")
            return False


if __name__ == "__main__":
    test = WorkflowDesignTest()
    success = test.run_all_tests()
    exit(0 if success else 1)
