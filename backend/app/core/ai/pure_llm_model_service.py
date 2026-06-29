"""
纯 LLM 推理客户端（后端代理层）。

职责：
- 后端仅保留业务编排，不加载模型；
- 通过 Celery 任务把推理请求转发到 celery_worker 执行。
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

from celery.exceptions import TimeoutError as CeleryTimeoutError

from app.config import settings
from app.core.celery_app import celery_app
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EndpointValidator:
    """
    兼容占位类。
    真实 URL 校验逻辑在 worker 侧模型服务内执行。
    """

    def __init__(self, graph_nodes: Optional[List[Dict[str, Any]]] = None):
        self.graph_nodes = graph_nodes or []

    def find_best_match(self, url: str) -> Optional[str]:
        return url

    def fix_urls_in_json(self, schema: Dict[str, Any], user_input: str = ""):
        return schema, []


class PureLLMModelService:
    """
    纯 LLM 服务代理：把方法调用转成 Celery RPC。
    """

    _ASYNC_METHODS = {
        "generate_two_round_async",
        "generate_slot_values",
    }

    def __init__(self):
        self._invoke_task_name = "app.tasks.ai.invoke"
        self._timeout = int(os.getenv("CELERY_INFERENCE_TIMEOUT", "240"))

    @property
    def is_loaded(self) -> bool:
        """
        后端不本地加载模型，统一返回 True，实际加载由 worker 懒加载控制。
        """
        return True

    def load_model(self) -> bool:
        """兼容旧调用：后端不执行本地加载。"""
        return True

    def unload_model(self) -> bool:
        """兼容旧调用：后端不执行本地卸载。"""
        return True

    def _invoke_remote(self, method: str, *args: Any, **kwargs: Any) -> Any:
        task = celery_app.send_task(
            self._invoke_task_name,
            args=["pure_llm", method, list(args), kwargs],
            queue=settings.CELERY_AI_QUEUE,
        )
        try:
            return task.get(timeout=self._timeout)
        except CeleryTimeoutError as exc:
            logger.error(f"LLM 推理超时: method={method}, task_id={task.id}")
            raise RuntimeError(f"推理超时: {method}") from exc
        except Exception as exc:
            logger.error(f"LLM 推理失败: method={method}, task_id={task.id}, error={exc}")
            raise

    async def _invoke_remote_async(self, method: str, *args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self._invoke_remote(method, *args, **kwargs))

    def __getattr__(self, name: str):
        if name in self._ASYNC_METHODS:
            async def _async_proxy(*args: Any, **kwargs: Any) -> Any:
                return await self._invoke_remote_async(name, *args, **kwargs)
            return _async_proxy

        def _sync_proxy(*args: Any, **kwargs: Any) -> Any:
            return self._invoke_remote(name, *args, **kwargs)

        return _sync_proxy


pure_llm_model_service = PureLLMModelService()


def init_pure_llm_model() -> bool:
    """
    兼容旧入口：主后端不加载模型，返回 True。
    """
    return True
