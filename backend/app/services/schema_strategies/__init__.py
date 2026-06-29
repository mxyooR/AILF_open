"""
Schema 生成策略模块

使用策略模式处理不同节点类型，避免 if-else 树
"""
from .base import NodeStrategy
from .api_call_strategy import ApiCallStrategy
from .start_strategy import StartNodeStrategy
from .end_strategy import EndNodeStrategy
from .condition_strategy import ConditionNodeStrategy
from .notification_strategy import NotificationNodeStrategy
from .chart_strategy import ChartStrategy

__all__ = [
    'NodeStrategy',
    'ApiCallStrategy',
    'StartNodeStrategy',
    'EndNodeStrategy',
    'ConditionNodeStrategy',
    'NotificationNodeStrategy',
    'ChartStrategy'
]
