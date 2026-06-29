"""
节点策略基类

定义所有节点策略的接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from jinja2 import Template


class NodeStrategy(ABC):
    """节点策略基类"""
    
    def __init__(self, template_loader=None):
        """
        Args:
            template_loader: 模板加载器（可选）
        """
        self.template_loader = template_loader
    
    @abstractmethod
    def can_handle(self, node: Dict[str, Any]) -> bool:
        """
        判断是否可以处理该节点
        
        Args:
            node: 节点定义
        
        Returns:
            是否可以处理
        """
        pass
    
    @abstractmethod
    def generate_schema(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None,
        user_instruction: str = "",
        slot_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成 AMIS Schema
        
        Args:
            workflow: 工作流定义
            node: 当前节点
            context_data: 上下文数据
            user_instruction: 用户指令（用于 AI 槽填充）
            slot_values: AI 槽位值（可选）
        
        Returns:
            AMIS Schema
        """
        pass
    
    def render_template(self, template_str: str, **kwargs) -> str:
        """
        渲染 Jinja2 模板
        
        Args:
            template_str: 模板字符串
            **kwargs: 模板变量
        
        Returns:
            渲染后的字符串
        """
        template = Template(template_str)
        return template.render(**kwargs)
    
    def build_base_page(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        body: Any
    ) -> Dict[str, Any]:
        """
        构建基础 Page 结构
        
        Args:
            workflow: 工作流定义
            node: 当前节点
            body: 页面内容
        
        Returns:
            Page Schema
        """
        workflow_id = workflow.get("id") or workflow.get("workflow_id", "")
        return {
            "type": "page",
            "title": workflow.get("name", "工作流"),
            "workflow_id": workflow_id,
            "current_node_id": node.get("id", ""),
            "body": body
        }
    
    def build_workflow_api(
        self,
        workflow_id: str,
        node_id: str,
        action: str = "next"
    ) -> Dict[str, Any]:
        """
        构建工作流 API 配置
        
        Args:
            workflow_id: 工作流 ID
            node_id: 节点 ID
            action: 动作（next/submit）
        
        Returns:
            API 配置
        """
        return {
            "method": "post",
            "url": "/api/v1/workflow/state",
            "data": {
                "workflow_id": workflow_id,
                "node_id": node_id,
                "action": action,
            }
        }
    
    def extract_context_value(
        self,
        context_data: Optional[Dict[str, Any]],
        key: str,
        default: Any = None
    ) -> Any:
        """
        从上下文中提取值
        
        Args:
            context_data: 上下文数据
            key: 键名
            default: 默认值
        
        Returns:
            值
        """
        if not context_data:
            return default
        return context_data.get(key, default)
