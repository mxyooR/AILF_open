"""
Start 节点策略
"""
from typing import Dict, Any, Optional
from .base import NodeStrategy
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class StartNodeStrategy(NodeStrategy):
    """Start 节点策略"""
    
    def can_handle(self, node: Dict[str, Any]) -> bool:
        """判断是否为 start 节点"""
        return node.get("type") == "start"
    
    def generate_schema(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None,
        user_instruction: str = "",
        slot_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成 start 节点界面（通常会被跳过）"""
        logger.info(f"生成 Start 节点 Schema: {node.get('id', '')}")
        body = {
            "type": "alert",
            "level": "info",
            "body": "正在启动工作流...",
            "showIcon": True
        }
        
        return self.build_base_page(workflow, node, body)
