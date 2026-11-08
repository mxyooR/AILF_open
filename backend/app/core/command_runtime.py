"""Bounded async orchestration, independent of models, databases and HTTP routes."""
from __future__ import annotations

import asyncio
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import logging
import secrets
import time
from typing import Any, Awaitable, Callable, Optional
import uuid

logger = logging.getLogger(__name__)
TERMINAL_STATES = {"SUCCESS", "FAILURE"}


class CommandCapacityError(RuntimeError):
    """The process has reached its outstanding command limit."""


class CommandRuntimeClosed(RuntimeError):
    """The application is draining and cannot accept commands."""


class TaskStateStore:
    """Async Redis storage with an expiring, bounded process-local fallback.

    Absolute expiry travels with each record, so polling cannot renew its lifetime.
    A short cooldown avoids repeated connection waits when Redis is unavailable.
    """
    def __init__(self, backend=None, *, ttl: float = 3600, max_entries: int = 1024,
                 clock: Callable[[], float] = time.time, retry_seconds: float = 10):
        if ttl <= 0 or max_entries < 1:
            raise ValueError("Task store limits must be positive")
        self.backend = backend
        self.ttl = ttl
        self.max_entries = max_entries
        self.clock = clock
        self.retry_seconds = retry_seconds
        self._retry_at = 0.0
        self._memory: OrderedDict[str, dict] = OrderedDict()

    def _cache(self, task_id: str, record: dict) -> None:
        now = self.clock()
        for key, cached in list(self._memory.items()):
            if cached["expires_at"] <= now:
                del self._memory[key]
        if record["expires_at"] <= now:
            self._memory.pop(task_id, None)
            return
        self._memory[task_id] = deepcopy(record)
        self._memory.move_to_end(task_id)
        while len(self._memory) > self.max_entries:
            key = next((key for key, value in self._memory.items()
                        if value["payload"].get("status") in TERMINAL_STATES), next(iter(self._memory)))
            del self._memory[key]

    def _unavailable(self) -> None:
        self._retry_at = self.clock() + self.retry_seconds
        logger.warning("Task state backend unavailable; using bounded local fallback")

    async def save(self, task_id: str, payload: dict) -> None:
        now = self.clock()
        record = {"expires_at": now + self.ttl, "saved_at": now, "payload": deepcopy(payload)}
        self._cache(task_id, record)
        if self.backend is not None and now >= self._retry_at:
            try:
                await self.backend.setex(f"ai:command:task:{task_id}", max(1, int(self.ttl)), json.dumps(record, ensure_ascii=False, default=str))
            except Exception:
                self._unavailable()

    async def load(self, task_id: str) -> Optional[dict]:
        now = self.clock()
        local = self._memory.get(task_id)
        if local is not None and local["expires_at"] <= now:
            del self._memory[task_id]
            local = None
        remote = None
        if self.backend is not None and now >= self._retry_at:
            try:
                raw = await self.backend.get(f"ai:command:task:{task_id}")
                if raw:
                    candidate = json.loads(raw)
                    # Old deployment records lack an envelope and polling digest.
                    if isinstance(candidate, dict) and {"expires_at", "saved_at", "payload"} <= candidate.keys() and isinstance(candidate["payload"], dict):
                        remote = candidate
            except Exception:
                self._unavailable()
        # A state transition may finish while the Redis read is awaiting I/O.
        # Re-read local state before caching a potentially older remote snapshot.
        now = self.clock()
        record = self._memory.get(task_id)
        if remote is not None and (record is None or remote["saved_at"] > record["saved_at"]):
            record = remote
        if record is None or record["expires_at"] <= now:
            self._memory.pop(task_id, None)
            return None
        self._cache(task_id, record)
        return deepcopy(record["payload"])

    async def close(self) -> None:
        if self.backend is not None:
            await self.backend.aclose()


class CommandRuntime:
    def __init__(self, handler: Callable[..., Awaitable[dict]], store: TaskStateStore, *,
                 max_concurrent: int = 2, max_pending: int = 64, timeout: float = 540):
        if max_concurrent < 1 or max_pending < max_concurrent or timeout <= 0 or store.ttl <= timeout or store.max_entries < max_pending:
            raise ValueError("Invalid command limits: require cache >= pending >= concurrent and TTL > timeout > 0")
        self.handler = handler
        self.store = store
        self.max_pending = max_pending
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._accept_lock = asyncio.Lock()
        self._tasks: dict[str, asyncio.Task] = {}
        self._payloads: dict[str, dict] = {}
        self._closing = False

    async def submit(self, command: str, context: Optional[dict] = None) -> dict[str, str]:
        async with self._accept_lock:
            if self._closing:
                raise CommandRuntimeClosed("Command runtime is closing")
            if len(self._tasks) >= self.max_pending:
                raise CommandCapacityError("Outstanding command limit reached")
            loop = asyncio.get_running_loop()
            task_id = uuid.uuid4().hex
            poll_token = secrets.token_urlsafe(32)
            payload = {"task_id": task_id, "status": "PENDING", "result": None, "error": None,
                       "_poll_digest": hashlib.sha256(poll_token.encode()).hexdigest()}
            runtime_context = deepcopy(context or {})
            runtime_context["_inference_trace_id"] = task_id
            await self._update(payload, "PENDING")
            task = loop.create_task(self._execute(payload, command, runtime_context), name=f"ailf-command-{task_id}")
            self._tasks[task_id] = task
            self._payloads[task_id] = payload
            def release(completed):
                self._tasks.pop(task_id, None)
                self._payloads.pop(task_id, None)
            task.add_done_callback(release)
            return {"task_id": task_id, "poll_token": poll_token}

    async def _update(self, payload: dict, status: str, *, result: Any = None, error: Optional[str] = None) -> None:
        payload.update(status=status, result=result, error=error, updated_at=datetime.now(timezone.utc).isoformat())
        await self.store.save(payload["task_id"], payload)

    async def _execute(self, payload: dict, command: str, context: dict) -> None:
        async def run():
            async with self._semaphore:
                await self._update(payload, "STARTED")
                return await self.handler(command=command, context=context)
        try:
            result = await asyncio.wait_for(run(), timeout=self.timeout)
            await self._update(payload, "SUCCESS", result=result)
        except asyncio.TimeoutError:
            await self._update(payload, "FAILURE", error="任务等待或执行超时，请稍后重试")
        except asyncio.CancelledError:
            await self._update(payload, "FAILURE", error="服务正在关闭，请重新提交任务")
            raise
        except Exception as error:
            logger.error("Async command failed: task_id=%s error_type=%s", payload["task_id"], type(error).__name__)
            await self._update(payload, "FAILURE", error="任务执行失败，请稍后重试")

    async def get(self, task_id: str, poll_token: str) -> Optional[dict]:
        if not poll_token or len(poll_token) > 256 or len(task_id) != 32:
            return None
        payload = await self.store.load(task_id)
        if payload is None or not secrets.compare_digest(payload.get("_poll_digest", ""), hashlib.sha256(poll_token.encode()).hexdigest()):
            return None
        return {key: value for key, value in payload.items() if not key.startswith("_")}

    async def shutdown(self) -> None:
        async with self._accept_lock:
            self._closing = True
            jobs = [(task, self._payloads[task_id]) for task_id, task in self._tasks.items()]
        for task, payload in jobs:
            task.cancel()
        await asyncio.gather(*(task for task, payload in jobs), return_exceptions=True)
        # A task cancelled before its first event-loop turn never enters _execute.
        for task, payload in jobs:
            if payload["status"] not in TERMINAL_STATES:
                await self._update(payload, "FAILURE", error="服务正在关闭，请重新提交任务")
        await self.store.close()
