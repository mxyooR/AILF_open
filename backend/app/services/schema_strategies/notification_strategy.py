"""
Notification 节点策略
"""
from typing import Dict, Any, Optional
import re
from .base import NodeStrategy
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class NotificationNodeStrategy(NodeStrategy):
    """Notification 节点策略"""
    
    def can_handle(self, node: Dict[str, Any]) -> bool:
        """判断是否为 notification 节点"""
        return node.get("type") == "notification"
    
    def generate_schema(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None,
        user_instruction: str = "",
        slot_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成 notification 节点界面
        
        显示通知消息，用户确认后继续
        """
        config = node.get("config", {})
        message_template = config.get("message_template", "")
        ai_instructions = node.get("ai_instructions", {})
        action = ai_instructions.get("action", "")
        
        message = message_template or action or node.get("description", "提示信息")
        
        # 替换上下文变量 ${xxx}
        context_data = context_data or {}
        message = self._replace_context_variables(message, context_data)
        
        # 基于文案推断通知级别（兼容旧配置未显式保存 notification_type 的情况）
        is_error = any(kw in message for kw in ["拒绝", "失败", "错误", "不足", "无法", "异常"])
        is_success = (not is_error) and any(kw in message for kw in ["成功", "完成", "已"])
        alert_level = "warning" if is_error else ("success" if is_success else "info")
        logger.info(f"生成 Notification 节点 Schema: {node.get('id', '')}, level={alert_level}")
        
        body_content = [
            {
                "type": "alert",
                "level": alert_level,
                "body": message,
                "showIcon": True
            },
            {
                "type": "form",
                "api": self.build_workflow_api(
                    workflow_id=workflow["id"],
                    node_id=node.get("id", ""),
                    action="next"
                ),
                "body": [],
                "actions": [
                    {
                        "type": "submit",
                        "label": "确认" if is_error else "继续",
                        "level": "primary"
                    }
                ]
            }
        ]
        
        return self.build_base_page(workflow, node, body_content)
    
    def _replace_context_variables(
        self,
        message: str,
        context_data: Dict[str, Any]
    ) -> str:
        """
        替换消息中的上下文变量
        
        Args:
            message: 消息模板
            context_data: 上下文数据
        
        Returns:
            替换后的消息
        """
        def replace_var(match):
            var_name = match.group(1)
            value = context_data.get(var_name)
            if value is not None:
                if isinstance(value, (dict, list)):
                    return str(value)
                return str(value)
            return match.group(0)  # 保留原样
        
        return re.sub(r'\$\{(\w+)\}', replace_var, message)
