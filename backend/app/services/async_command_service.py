"""
异步命令编排服务（后端本地调度，Redis 优先 + 内存兜底）。

职责：
- 接收 `/command/async` 提交任务；
- 在后端事件循环中执行 `ai_service` 业务编排；
- 任务状态落 Redis（可选）并提供轮询查询。
"""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from app.config import settings
from app.core.logging_config import get_logger
from app.services.ai_service import ai_service_simple

logger = get_logger(__name__)


class AsyncCommandService:
    """异步命令调度器。"""

    def __init__(self):
        self._memory: Dict[str, Dict[str, Any]] = {}
        self._redis = None
        self._redis_enabled = False
        self._task_ttl = int(os.getenv("REDIS_AI_TASK_TTL", "3600"))
        self._init_redis()
        if self._redis_enabled:
            logger.info("异步命令服务已初始化(Redis + 内存兜底)")
        else:
            logger.warning("异步命令服务已初始化(仅内存，Redis 不可用)")

    def _init_redis(self) -> None:
        try:
            import redis  # type: ignore

            self._redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2,
            )
            self._redis.ping()
            self._redis_enabled = True
        except Exception as e:
            self._redis = None
            self._redis_enabled = False
            logger.warning(f"异步命令服务 Redis 初始化失败，将使用内存: {e}")

    def _task_key(self, task_id: str) -> str:
        return f"ai:command:task:{task_id}"

    def _save(self, task_id: str, payload: Dict[str, Any]) -> None:
        self._memory[task_id] = payload
        if not self._redis_enabled or not self._redis:
            return
        try:
            self._redis.setex(
                self._task_key(task_id),
                self._task_ttl,
                json.dumps(payload, ensure_ascii=False, default=str),
            )
        except Exception as e:
            logger.warning(f"写入 Redis 任务状态失败，已回退内存: task_id={task_id}, error={e}")

    def _load(self, task_id: str) -> Optional[Dict[str, Any]]:
        if self._redis_enabled and self._redis:
            try:
                raw = self._redis.get(self._task_key(task_id))
                if raw:
                    data = json.loads(raw)
                    self._memory[task_id] = data
                    return data
            except Exception as e:
                logger.warning(f"读取 Redis 任务状态失败，回退内存: task_id={task_id}, error={e}")
        return self._memory.get(task_id)

    async def _execute(self, task_id: str, command: str, context: Dict[str, Any]) -> None:
        self._save(
            task_id,
            {
                "task_id": task_id,
                "status": "STARTED",
                "result": None,
                "error": None,
                "updated_at": datetime.now().isoformat(),
            },
        )

        try:
            runtime_context = dict(context or {})
            runtime_context["_inference_trace_id"] = task_id
            result = await ai_service_simple.process_command(command=command, context=runtime_context)
            self._save(
                task_id,
                {
                    "task_id": task_id,
                    "status": "SUCCESS",
                    "result": result,
                    "error": None,
                    "updated_at": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"异步命令执行失败: task_id={task_id}, error={e}")
            self._save(
                task_id,
                {
                    "task_id": task_id,
                    "status": "FAILURE",
                    "result": None,
                    "error": str(e),
                    "updated_at": datetime.now().isoformat(),
                },
            )

    def submit(self, command: str, context: Optional[Dict[str, Any]] = None) -> str:
        task_id = uuid.uuid4().hex
        payload = {
            "task_id": task_id,
            "status": "PENDING",
            "result": None,
            "error": None,
            "updated_at": datetime.now().isoformat(),
        }
        self._save(task_id, payload)

        loop = asyncio.get_running_loop()
        loop.create_task(self._execute(task_id, command, context or {}))
        return task_id

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._load(task_id)


async_command_service = AsyncCommandService()
