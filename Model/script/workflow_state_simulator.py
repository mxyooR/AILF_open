"""
Workflow State Simulator - 工作流状态模拟器
按照工作流的实际执行顺序生成训练样本，而不是随机选择节点
"""

import random
from typing import Dict, List, Any, Optional, Tuple


class WorkflowStateSimulator:
    """工作流状态模拟器"""
    
    def __init__(self):
        self.mock_data_generators = {
            "string": lambda label: self._generate_mock_string(label),
            "str": lambda label: self._generate_mock_string(label),
            "integer": lambda label: random.randint(1, 100),
            "int": lambda label: random.randint(1, 100),
            "number": lambda label: round(random.uniform(10.0, 1000.0), 2),
            "float": lambda label: round(random.uniform(10.0, 1000.0), 2),
            "date": lambda label: "2024-11-24",
            "time": lambda label: "14:30:00",
            "datetime": lambda label: "2024-11-24 14:30:00",
            "boolean": lambda label: random.choice([True, False]),
            "bool": lambda label: random.choice([True, False]),
            "select": lambda label: "选项1",
            "file": lambda label: "/tmp/upload.jpg",
            "array": lambda label: ["item1", "item2"]
        }
    
    def simulate_workflow_path(self, workflow: Dict[str, Any], domain: str) -> List[Dict[str, Any]]:
        """
        模拟工作流的完整执行路径，生成有序的样本
        
        返回：包含多个样本的列表，每个样本代表工作流的一个状态
        """
        samples = []
        nodes = workflow.get("nodes", [])
        
        if not nodes:
            return samples
        
        # Step 1: 找到入口节点（第一个 api_call 节点）
        # 已移除 user_input 支持
        entry_node = self._find_entry_node(nodes)
        if entry_node:
            entry_sample = self._generate_entry_sample(workflow, entry_node, domain)
            if entry_sample:
                samples.append(entry_sample)
        
        # Step 2: 遍历工作流路径，生成后续样本
        current_node = entry_node
        visited_nodes = set()
        mock_context = {}
        
        while current_node:
            node_id = current_node.get("id")
            
            # 防止死循环
            if node_id in visited_nodes:
                break
            visited_nodes.add(node_id)
            
            # 如果当前节点是 api_call POST，生成 mock 数据
            if current_node.get("type") == "api_call":
                config = current_node.get("config", {})
                if config.get("method", "GET").upper() == "POST":
                    mock_context.update(self._generate_mock_context(current_node))
            
            # 找到下一个节点
            next_node_id = current_node.get("next")
            if not next_node_id:
                break
            
            next_node = self._find_node_by_id(nodes, next_node_id)
            if not next_node:
                break
            
            # 根据下一个节点的类型生成样本
            if next_node.get("type") == "api_call":
                # 生成 workflow_execute 样本
                execute_sample = self._generate_execute_sample(
                    workflow, current_node, next_node, mock_context, domain
                )
                if execute_sample:
                    samples.append(execute_sample)
            
            elif next_node.get("type") == "display":
                # 生成结果展示样本
                display_sample = self._generate_display_sample(
                    workflow, current_node, next_node, mock_context, domain
                )
                if display_sample:
                    samples.append(display_sample)
            
            # 移动到下一个节点
            current_node = next_node
        
        return samples
    
    def _find_entry_node(self, nodes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """找到工作流的入口节点（第一个节点）"""
        if not nodes:
            return None
        
        # 通常第一个节点就是入口
        return nodes[0]
    
    def _find_node_by_id(self, nodes: List[Dict[str, Any]], node_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 查找节点"""
        for node in nodes:
            if node.get("id") == node_id:
                return node
        return None
    
    def _generate_entry_sample(self, workflow: Dict[str, Any], entry_node: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """生成入口样本（workflow_input）"""
        return {
            "type": "workflow_input",
            "workflow": workflow,
            "current_node_id": "START",
            "next_node": entry_node,
            "mock_context": {},
            "domain": domain,
            "instruction": random.choice([
                workflow.get("name", ""),
                *workflow.get("trigger_keywords", [])
            ])
        }
    
    def _generate_input_sample(self, workflow: Dict[str, Any], current_node: Dict[str, Any], 
                               next_node: Dict[str, Any], mock_context: Dict[str, Any], 
                               domain: str) -> Dict[str, Any]:
        """生成输入样本（workflow_input）"""
        return {
            "type": "workflow_input",
            "workflow": workflow,
            "current_node_id": current_node.get("id"),
            "next_node": next_node,
            "mock_context": mock_context.copy(),
            "domain": domain,
            "instruction": f"{workflow.get('name', '')} - {next_node.get('desc', '')}"
        }
    
    def _generate_execute_sample(self, workflow: Dict[str, Any], current_node: Dict[str, Any],
                                 next_node: Dict[str, Any], mock_context: Dict[str, Any],
                                 domain: str) -> Dict[str, Any]:
        """生成执行样本（workflow_execute）"""
        return {
            "type": "workflow_execute",
            "workflow": workflow,
            "current_node_id": current_node.get("id"),
            "next_node": next_node,
            "api_id": next_node.get("api_id"),
            "mock_context": mock_context.copy(),
            "domain": domain,
            "instruction": random.choice(["提交", "下一步", "继续", "执行"])
        }
    
    def _generate_display_sample(self, workflow: Dict[str, Any], current_node: Dict[str, Any],
                                 next_node: Dict[str, Any], mock_context: Dict[str, Any],
                                 domain: str) -> Dict[str, Any]:
        """生成展示样本（workflow_display）"""
        return {
            "type": "workflow_display",
            "workflow": workflow,
            "current_node_id": current_node.get("id"),
            "next_node": next_node,
            "mock_context": mock_context.copy(),
            "domain": domain,
            "instruction": "查看结果"
        }
    
    def _generate_mock_context(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """根据节点的字段生成 mock 数据"""
        mock_data = {}
        fields = node.get("fields", [])
        
        for field in fields:
            field_name = field.get("name")
            field_type = field.get("type", "string")
            field_label = field.get("label", field_name)
            
            generator = self.mock_data_generators.get(field_type)
            if generator:
                mock_data[field_name] = generator(field_label)
            else:
                mock_data[field_name] = self._generate_mock_string(field_label)
        
        return mock_data
    
    def _generate_mock_string(self, label: str) -> str:
        """生成 mock 字符串数据"""
        # 根据标签生成合适的 mock 数据
        label_lower = label.lower()
        
        if "姓名" in label or "name" in label_lower:
            return random.choice(["张三", "李四", "王五", "赵六", "钱七"])
        elif "手机" in label or "phone" in label_lower:
            return f"138{random.randint(10000000, 99999999)}"
        elif "邮箱" in label or "email" in label_lower:
            return f"user{random.randint(1, 999)}@example.com"
        elif "地址" in label or "address" in label_lower:
            return random.choice(["北京市朝阳区", "上海市浦东新区", "广州市天河区", "深圳市南山区"])
        elif "身份证" in label or "id_card" in label_lower:
            return f"11010119900101{random.randint(1000, 9999)}"
        elif "金额" in label or "amount" in label_lower or "价格" in label or "price" in label_lower:
            return str(round(random.uniform(10.0, 10000.0), 2))
        elif "数量" in label or "quantity" in label_lower or "count" in label_lower:
            return str(random.randint(1, 100))
        elif "编号" in label or "id" in label_lower or "code" in label_lower:
            return f"{random.choice(['A', 'B', 'C', 'D'])}{random.randint(100000, 999999)}"
        elif "描述" in label or "desc" in label_lower or "reason" in label_lower:
            return random.choice(["测试数据", "示例内容", "业务需求", "正常申请"])
        else:
            return f"测试_{label}_{random.randint(1, 999)}"
    
    def get_workflow_step_count(self, workflow: Dict[str, Any]) -> int:
        """获取工作流的步骤数量"""
        nodes = workflow.get("nodes", [])
        return len(nodes)
    
    def get_workflow_complexity(self, workflow: Dict[str, Any]) -> str:
        """评估工作流的复杂度"""
        step_count = self.get_workflow_step_count(workflow)
        
        if step_count <= 3:
            return "simple"
        elif step_count <= 6:
            return "medium"
        else:
            return "complex"
