"""
End 节点策略
"""
from typing import Dict, Any, Optional
from .base import NodeStrategy
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EndNodeStrategy(NodeStrategy):
    """End 节点策略"""
    
    def can_handle(self, node: Dict[str, Any]) -> bool:
        """判断是否为 end 节点"""
        return node.get("type") == "end"
    
    def generate_schema(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None,
        user_instruction: str = "",
        slot_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成 end 节点界面（完成提示）"""
        logger.info(f"生成 End 节点 Schema: {node.get('id', '')}")
        ai_instructions = node.get("ai_instructions", {})
        action = ai_instructions.get("action", "工作流已完成")
        
        body = [
            {
                "type": "alert",
                "level": "success",
                "title": "操作完成",
                "body": action,
                "showIcon": True
            },
            {
                "type": "button",
                "label": "返回首页",
                "level": "primary",
                "onEvent": {
                    "click": {
                        "actions": [
                            {
                                "actionType": "custom",
                                "script": "window.location.reload();"
                            }
                        ]
                    }
                }
            }
        ]
        
        return self.build_base_page(workflow, node, body)
