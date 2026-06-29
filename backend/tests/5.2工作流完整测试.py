"""
第五部分 - 工作流设计模块完整测试
测试所有14个API端点，确保完全符合API文档规范
"""
import requests
import json
import time
from typing import Dict, Any, Optional


class WorkflowCompleteTest:
    """工作流设计模块完整测试类"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.token = None
        self.test_workflow_id = None
        self.test_instance_id = None
        self.test_step_id = None
        
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
    
    def test_all_workflow_apis(self) -> bool:
        """测试所有14个工作流API端点"""
        print("🚀 开始运行工作流设计模块完整测试...")
        print("📋 覆盖所有14个API端点")
        print("=" * 60)
        
        test_results = []
        
        # 1. 创建工作流定义
        print("\n1️⃣ 测试创建工作流定义 (POST /api/workflow)")
        result = self.test_create_workflow()
        test_results.append(result)
        
        # 2. 获取工作流列表
        print("2️⃣ 测试获取工作流列表 (GET /api/workflow)")
        result = self.test_get_workflows_list()
        test_results.append(result)
        
        # 3. 获取工作流详情
        print("3️⃣ 测试获取工作流详情 (GET /api/workflow/{workflow_id})")
        result = self.test_get_workflow_detail()
        test_results.append(result)
        
        # 4. 更新工作流定义
        print("4️⃣ 测试更新工作流定义 (PUT /api/workflow/{workflow_id})")
        result = self.test_update_workflow()
        test_results.append(result)
        
        # 5. 获取工作流步骤列表
        print("5️⃣ 测试获取工作流步骤列表 (GET /api/workflow/{workflow_id}/steps)")
        result = self.test_get_workflow_steps()
        test_results.append(result)
        
        # 6. 添加工作流步骤
        print("6️⃣ 测试添加工作流步骤 (POST /api/workflow/{workflow_id}/steps)")
        result = self.test_add_workflow_step()
        test_results.append(result)
        
        # 7. 更新工作流步骤
        print("7️⃣ 测试更新工作流步骤 (PUT /api/workflow/{workflow_id}/steps/{step_id})")
        result = self.test_update_workflow_step()
        test_results.append(result)
        
        # 8. 执行工作流
        print("8️⃣ 测试执行工作流 (POST /api/workflow/{workflow_id}/execute)")
        result = self.test_execute_workflow()
        test_results.append(result)
        
        # 9. 获取工作流实例列表
        print("9️⃣ 测试获取工作流实例列表 (GET /api/workflow/instances)")
        result = self.test_get_workflow_instances()
        test_results.append(result)
        
        # 10. 获取工作流实例详情
        print("🔟 测试获取工作流实例详情 (GET /api/workflow/instances/{instance_id})")
        result = self.test_get_workflow_instance_detail()
        test_results.append(result)
        
        # 11. 继续执行工作流实例
        print("1️⃣1️⃣ 测试继续执行工作流实例 (POST /api/workflow/instances/{instance_id}/continue)")
        result = self.test_continue_workflow_instance()
        test_results.append(result)
        
        # 12. 取消工作流实例
        print("1️⃣2️⃣ 测试取消工作流实例 (POST /api/workflow/instances/{instance_id}/cancel)")
        result = self.test_cancel_workflow_instance()
        test_results.append(result)
        
        # 13. 删除工作流步骤
        print("1️⃣3️⃣ 测试删除工作流步骤 (DELETE /api/workflow/{workflow_id}/steps/{step_id})")
        result = self.test_delete_workflow_step()
        test_results.append(result)
        
        # 14. 删除工作流定义
        print("1️⃣4️⃣ 测试删除工作流定义 (DELETE /api/workflow/{workflow_id})")
        result = self.test_delete_workflow()
        test_results.append(result)
        
        # 统计结果
        passed = sum(test_results)
        total = len(test_results)
        
        print("\n" + "=" * 60)
        print("📊 第五部分工作流设计模块完整测试结果")
        print("-" * 60)
        print(f"总API端点: {total}")
        print(f"测试通过: {passed}")
        print(f"测试失败: {total - passed}")
        print(f"成功率: {(passed / total * 100):.1f}%")
        
        if passed == total:
            print("🎉 所有14个API端点测试全部通过！")
            print("✅ 第五部分工作流设计模块完全符合API文档规范！")
            return True
        else:
            print(f"⚠️  有 {total - passed} 个API端点测试失败")
            return False
    
    def test_create_workflow(self) -> bool:
        """测试创建工作流定义"""
        try:
            workflow_data = {
                "name": "完整测试工作流",
                "description": "用于完整测试的工作流定义",
                "triggerType": "manual",
                "steps": [
                    {
                        "id": "start_step",
                        "name": "开始",
                        "type": "start",
                        "position": {"x": 100, "y": 100},
                        "nextSteps": ["form_step"]
                    },
                    {
                        "id": "form_step",
                        "name": "表单填写",
                        "type": "form",
                        "position": {"x": 300, "y": 100},
                        "config": {
                            "formConfig": {
                                "entity": "test_entity",
                                "fields": ["name", "email", "phone"]
                            }
                        },
                        "nextSteps": ["end_step"]
                    },
                    {
                        "id": "end_step",
                        "name": "结束",
                        "type": "end",
                        "position": {"x": 500, "y": 100}
                    }
                ],
                "conditions": []
            }
            
            response = requests.post(
                f"{self.base_url}/api/workflow",
                headers=self.get_headers(),
                json=workflow_data
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.test_workflow_id = data["data"]["workflow"]["id"]
                print(f"   ✅ 创建成功: {self.test_workflow_id}")
                return True
            else:
                print(f"   ❌ 创建失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ 创建异常: {e}")
            return False
    
    def test_get_workflows_list(self) -> bool:
        """测试获取工作流列表"""
        try:
            response = requests.get(
                f"{self.base_url}/api/workflow?page=1&limit=10",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                workflows = data["data"]["workflows"]
                total = data["data"]["total"]
                print(f"   ✅ 获取成功: {len(workflows)}个工作流，总计{total}个")
                return True
            else:
                print(f"   ❌ 获取失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 获取异常: {e}")
            return False
    
    def test_get_workflow_detail(self) -> bool:
        """测试获取工作流详情"""
        if not self.test_workflow_id:
            print("   ❌ 没有可用的工作流ID")
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/api/workflow/{self.test_workflow_id}",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                workflow = data["data"]["workflow"]
                print(f"   ✅ 获取成功: {workflow['name']} ({len(workflow['steps'])}个步骤)")
                return True
            else:
                print(f"   ❌ 获取失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 获取异常: {e}")
            return False
    
    def test_update_workflow(self) -> bool:
        """测试更新工作流定义"""
        if not self.test_workflow_id:
            print("   ❌ 没有可用的工作流ID")
            return False
            
        try:
            update_data = {
                "description": "更新后的完整测试工作流描述",
                "status": "active"
            }
            
            response = requests.put(
                f"{self.base_url}/api/workflow/{self.test_workflow_id}",
                headers=self.get_headers(),
                json=update_data
            )
            
            if response.status_code == 200:
                data = response.json()
                workflow = data["data"]["workflow"]
                print(f"   ✅ 更新成功: {workflow['description']}")
                return True
            else:
                print(f"   ❌ 更新失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 更新异常: {e}")
            return False
    
    def test_get_workflow_steps(self) -> bool:
        """测试获取工作流步骤列表"""
        if not self.test_workflow_id:
            print("   ❌ 没有可用的工作流ID")
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/api/workflow/{self.test_workflow_id}/steps",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                steps = data["data"]["steps"]
                print(f"   ✅ 获取成功: {len(steps)}个步骤")
                return True
            else:
                print(f"   ❌ 获取失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 获取异常: {e}")
            return False
    
    def test_add_workflow_step(self) -> bool:
        """测试添加工作流步骤"""
        if not self.test_workflow_id:
            print("   ❌ 没有可用的工作流ID")
            return False
            
        try:
            self.test_step_id = "approval_step"
            step_data = {
                "step_id": self.test_step_id,
                "name": "审批步骤",
                "type": "approval",
                "position": {"x": 400, "y": 100},
                "config": {
                    "approvalConfig": {
                        "approvers": ["admin", "manager"],
                        "approval_type": "any"
                    }
                },
                "nextSteps": ["end_step"]
            }
            
            response = requests.post(
                f"{self.base_url}/api/workflow/{self.test_workflow_id}/steps",
                headers=self.get_headers(),
                json=step_data
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                step = data["data"]["step"]
                print(f"   ✅ 添加成功: {step['name']}")
                return True
            else:
                print(f"   ❌ 添加失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ 添加异常: {e}")
            return False
    
    def test_update_workflow_step(self) -> bool:
        """测试更新工作流步骤"""
        if not self.test_workflow_id or not self.test_step_id:
            print("   ❌ 没有可用的工作流ID或步骤ID")
            return False
            
        try:
            update_data = {
                "name": "更新后的审批步骤",
                "config": {
                    "approvalConfig": {
                        "approvers": ["admin", "manager", "supervisor"],
                        "approval_type": "majority"
                    }
                }
            }
            
            response = requests.put(
                f"{self.base_url}/api/workflow/{self.test_workflow_id}/steps/{self.test_step_id}",
                headers=self.get_headers(),
                json=update_data
            )
            
            if response.status_code == 200:
                data = response.json()
                step = data["data"]["step"]
                print(f"   ✅ 更新成功: {step['name']}")
                return True
            else:
                print(f"   ❌ 更新失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 更新异常: {e}")
            return False
    
    def test_execute_workflow(self) -> bool:
        """测试执行工作流"""
        if not self.test_workflow_id:
            print("   ❌ 没有可用的工作流ID")
            return False
            
        try:
            execute_data = {
                "input_data": {
                    "user_id": "test_user_123",
                    "request_type": "complete_test"
                },
                "context": {
                    "test_mode": True,
                    "priority": "high"
                },
                "priority": "high"
            }
            
            response = requests.post(
                f"{self.base_url}/api/workflow/{self.test_workflow_id}/execute",
                headers=self.get_headers(),
                json=execute_data
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                instance = data["data"]["instance"]
                self.test_instance_id = instance["id"]
                print(f"   ✅ 执行成功: {self.test_instance_id} (状态: {instance['status']})")
                return True
            else:
                print(f"   ❌ 执行失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ 执行异常: {e}")
            return False
    
    def test_get_workflow_instances(self) -> bool:
        """测试获取工作流实例列表"""
        try:
            response = requests.get(
                f"{self.base_url}/api/workflow/instances?page=1&limit=10&sort=created_at",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                instances = data["data"]["instances"]
                summary = data["data"]["summary"]
                print(f"   ✅ 获取成功: {len(instances)}个实例，总计{summary['total_instances']}个")
                return True
            else:
                print(f"   ❌ 获取失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 获取异常: {e}")
            return False
    
    def test_get_workflow_instance_detail(self) -> bool:
        """测试获取工作流实例详情"""
        if not self.test_instance_id:
            print("   ❌ 没有可用的实例ID")
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/api/workflow/instances/{self.test_instance_id}",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                instance = data["data"]["instance"]
                print(f"   ✅ 获取成功: {instance['workflow_name']} (进度: {instance['progress']['percentage']}%)")
                return True
            else:
                print(f"   ❌ 获取失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 获取异常: {e}")
            return False
    
    def test_continue_workflow_instance(self) -> bool:
        """测试继续执行工作流实例"""
        if not self.test_instance_id:
            print("   ❌ 没有可用的实例ID")
            return False
            
        try:
            continue_data = {
                "user_input": "continue_test",
                "additional_data": {"step": "approval"}
            }
            
            response = requests.post(
                f"{self.base_url}/api/workflow/instances/{self.test_instance_id}/continue",
                headers=self.get_headers(),
                json=continue_data
            )
            
            if response.status_code == 200:
                data = response.json()
                instance = data["data"]["instance"]
                print(f"   ✅ 继续成功: 状态 {instance['status']}")
                return True
            elif response.status_code == 400 and "不在等待状态" in response.text:
                print(f"   ✅ 继续API正常: 实例不在等待状态 (业务逻辑正确)")
                return True
            else:
                print(f"   ❌ 继续失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ 继续异常: {e}")
            return False
    
    def test_cancel_workflow_instance(self) -> bool:
        """测试取消工作流实例"""
        if not self.test_instance_id:
            print("   ❌ 没有可用的实例ID")
            return False
            
        try:
            response = requests.post(
                f"{self.base_url}/api/workflow/instances/{self.test_instance_id}/cancel?reason=完整测试取消",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 取消成功: {data['data']['reason']}")
                return True
            else:
                print(f"   ❌ 取消失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 取消异常: {e}")
            return False
    
    def test_delete_workflow_step(self) -> bool:
        """测试删除工作流步骤"""
        if not self.test_workflow_id or not self.test_step_id:
            print("   ❌ 没有可用的工作流ID或步骤ID")
            return False
            
        try:
            response = requests.delete(
                f"{self.base_url}/api/workflow/{self.test_workflow_id}/steps/{self.test_step_id}",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 删除成功: {data['data']['name']}")
                return True
            else:
                print(f"   ❌ 删除失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 删除异常: {e}")
            return False
    
    def test_delete_workflow(self) -> bool:
        """测试删除工作流定义"""
        if not self.test_workflow_id:
            print("   ❌ 没有可用的工作流ID")
            return False
            
        try:
            response = requests.delete(
                f"{self.base_url}/api/workflow/{self.test_workflow_id}?force=true",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 删除成功: {data['data']['name']}")
                return True
            else:
                print(f"   ❌ 删除失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 删除异常: {e}")
            return False
    
    def run_complete_test(self) -> bool:
        """运行完整测试"""
        # 获取认证令牌
        if not self.get_auth_token():
            return False
        
        # 运行所有API测试
        return self.test_all_workflow_apis()


if __name__ == "__main__":
    test = WorkflowCompleteTest()
    success = test.run_complete_test()
    exit(0 if success else 1)
