"""
Condition 节点策略
"""
from typing import Dict, Any, Optional
from .base import NodeStrategy
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ConditionNodeStrategy(NodeStrategy):
    """Condition 节点策略"""
    
    def can_handle(self, node: Dict[str, Any]) -> bool:
        """判断是否为 condition 节点"""
        return node.get("type") == "condition"
    
    def generate_schema(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None,
        user_instruction: str = "",
        slot_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成 condition 节点界面
        
        condition 节点由后端自动评估，不需要用户交互
        这个界面只是一个过渡提示
        """
        body = {
            "type": "alert",
            "level": "info",
            "body": "正在处理中...",
            "showIcon": True
        }
        
        logger.info(f"生成 Condition 节点 Schema: {node.get('id', '')}")
        return self.build_base_page(workflow, node, body)
