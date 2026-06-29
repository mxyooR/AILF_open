"""
Ego-Graph 推理客户端（后端代理层）。

职责：
- 后端只发起召回请求；
- 召回计算在 celery_worker 侧执行。
"""
from __future__ import annotations

import os
from typing import Any, Dict

from celery.exceptions import TimeoutError as CeleryTimeoutError

from app.config import settings
from app.core.celery_app import celery_app
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """兼容占位类。"""
    pass


class VectorIndex:
    """兼容占位类。"""
    pass


class GraphStructure:
    """兼容占位类。"""
    pass


class EgoGraphService:
    """Ego-Graph 服务代理。"""

    def __init__(self):
        self._invoke_task_name = "app.tasks.ai.invoke"
        self._timeout = int(os.getenv("CELERY_INFERENCE_TIMEOUT", "240"))

    def _invoke_remote(self, method: str, *args: Any, **kwargs: Any) -> Any:
        task = celery_app.send_task(
            self._invoke_task_name,
            args=["ego_graph", method, list(args), kwargs],
            queue=settings.CELERY_AI_QUEUE,
        )
        try:
            return task.get(timeout=self._timeout)
        except CeleryTimeoutError as exc:
            logger.error(f"Ego-Graph 调用超时: method={method}, task_id={task.id}")
            raise RuntimeError(f"图召回超时: {method}") from exc
        except Exception as exc:
            logger.error(f"Ego-Graph 调用失败: method={method}, task_id={task.id}, error={exc}")
            raise

    def __getattr__(self, name: str):
        def _sync_proxy(*args: Any, **kwargs: Any) -> Any:
            return self._invoke_remote(name, *args, **kwargs)

        return _sync_proxy


ego_graph_service = EgoGraphService()
