"""
Celery Worker 推理任务（纯推理层）。
"""
from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from celery.signals import worker_process_init, worker_ready

from celery_worker.celery_app import celery_app
from celery_worker.config import settings
from celery_worker.logging_config import get_logger
from celery_worker.model.ego_graph_service import ego_graph_service
from celery_worker.model.pure_llm_model_service import pure_llm_model_service

logger = get_logger(__name__)

_MODEL_REQUIRED_METHODS = {
    "identify_intent",
    "_generate_single_turn",
    "generate_slot_values",
    "generate_two_round",
    "generate_two_round_async",
}
_FULL_INFERENCE_METHODS = {
    "generate_two_round",
    "generate_two_round_async",
}
_TRACE_START_METHODS = {
    "identify_intent",
    "generate_two_round",
    "generate_two_round_async",
}
_TRACE_FINISH_METHODS = {
    "generate_slot_values",
    "_generate_single_turn",
    "generate_two_round",
    "generate_two_round_async",
}
_METRICS_TRACE_ID_KWARG = "__metrics_trace_id"
_TRACE_START_KEY_PREFIX = "ai:inference:trace:start:"
_TRACE_DONE_KEY_PREFIX = "ai:inference:trace:done:"
_TRACE_KEY_TTL_SECONDS = 900
_PRELOAD_LOCK = threading.Lock()
_PRELOAD_DONE = False
_METRICS_LOCK = threading.Lock()
_METRICS_REDIS_CLIENT = None
_METRICS_REDIS_INIT_FAILED = False


def _preload_model_once(trigger: str) -> None:
    """
    Worker 启动阶段预加载模型，降低首个任务时延。
    """
    global _PRELOAD_DONE

    if not settings.MODEL_PRELOAD_ON_WORKER_START:
        logger.info("MODEL_PRELOAD_ON_WORKER_START=false，跳过启动预加载。")
        return

    if _PRELOAD_DONE or pure_llm_model_service.is_loaded:
        return

    with _PRELOAD_LOCK:
        if _PRELOAD_DONE or pure_llm_model_service.is_loaded:
            return
        logger.info(f"Celery Worker 启动预加载模型中（trigger={trigger}）...")
        pure_llm_model_service.load_model()
        _PRELOAD_DONE = True
        logger.info("Celery Worker 启动预加载完成。")


@worker_process_init.connect
def _on_worker_process_init(**kwargs) -> None:
    _preload_model_once("worker_process_init")


@worker_ready.connect
def _on_worker_ready(**kwargs) -> None:
    _preload_model_once("worker_ready")


def _ensure_worker_model_loaded(method: str) -> None:
    """
    在需要模型推理的方法上执行懒加载。
    """
    if method not in _MODEL_REQUIRED_METHODS:
        return
    if not settings.MODEL_LOAD_ON_CELERY_TASK:
        return
    if pure_llm_model_service.is_loaded:
        return
    logger.info("Celery Worker 检测到模型未加载，开始加载模型...")
    pure_llm_model_service.load_model()


def _resolve_service(service: str):
    if service == "pure_llm":
        return pure_llm_model_service
    if service == "ego_graph":
        return ego_graph_service
    raise ValueError(f"不支持的推理服务: {service}")


def _is_full_inference_task(service: str, method: str) -> bool:
    """
    仅把“第一轮+第二轮合并”的完整对话视为一次推理任务。
    """
    return service == "pure_llm" and method in _FULL_INFERENCE_METHODS


def _get_metrics_redis_client():
    """
    获取用于推理耗时埋点的 Redis 客户端。
    """
    global _METRICS_REDIS_CLIENT, _METRICS_REDIS_INIT_FAILED

    if not settings.CELERY_INFERENCE_METRICS_ENABLED:
        return None

    if _METRICS_REDIS_CLIENT is not None:
        return _METRICS_REDIS_CLIENT

    if _METRICS_REDIS_INIT_FAILED:
        return None

    with _METRICS_LOCK:
        if _METRICS_REDIS_CLIENT is not None:
            return _METRICS_REDIS_CLIENT
        if _METRICS_REDIS_INIT_FAILED:
            return None

        try:
            import redis  # type: ignore
            redis_url = settings.CELERY_RESULT_BACKEND or settings.CELERY_BROKER_URL
            client = redis.Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=1.5,
                socket_connect_timeout=1.5,
            )
            client.ping()
            _METRICS_REDIS_CLIENT = client
            return _METRICS_REDIS_CLIENT
        except Exception as exc:
            _METRICS_REDIS_INIT_FAILED = True
            logger.warning(f"推理耗时埋点 Redis 初始化失败: {exc}")
            return None


def _record_inference_metrics(
    *,
    service: str,
    method: str,
    duration_ms: int,
    success: bool,
    task_id: Optional[str],
    worker_name: str,
    task_scope: str = "full_two_round",
    trace_id: Optional[str] = None,
) -> None:
    """
    记录推理任务耗时。
    """
    client = _get_metrics_redis_client()
    if client is None:
        return

    payload = {
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
        "service": service,
        "method": method,
        "duration_ms": max(0, int(duration_ms)),
        "success": bool(success),
        "task_id": task_id,
        "worker_name": worker_name,
        "task_scope": task_scope,
        "trace_id": trace_id,
    }

    try:
        max_samples = max(10, settings.CELERY_INFERENCE_METRICS_MAX_SAMPLES)
        metrics_key = settings.CELERY_INFERENCE_METRICS_KEY
        agg_key = settings.CELERY_INFERENCE_METRICS_AGG_KEY

        pipe = client.pipeline()
        pipe.lpush(metrics_key, json.dumps(payload, ensure_ascii=False))
        pipe.ltrim(metrics_key, 0, max_samples - 1)
        pipe.hincrby(agg_key, "total_count", 1)
        pipe.hincrby(agg_key, "success_count", 1 if success else 0)
        pipe.hincrby(agg_key, "fail_count", 0 if success else 1)
        pipe.hincrbyfloat(agg_key, "total_duration_ms", float(payload["duration_ms"]))
        pipe.hset(
            agg_key,
            mapping={
                "last_duration_ms": payload["duration_ms"],
                "last_timestamp": payload["timestamp"],
                "last_worker_name": worker_name,
                "last_task_id": task_id or "",
            }
        )
        pipe.execute()
    except Exception as exc:
        logger.warning(f"推理耗时埋点写入失败: {exc}")


def _record_full_inference_metrics(
    *,
    service: str,
    method: str,
    duration_ms: int,
    success: bool,
    task_id: Optional[str],
    worker_name: str,
    trace_id: Optional[str],
) -> None:
    """
    统计“完整推理任务”耗时：
    - 优先使用 trace_id，把 identify_intent + 第二轮调用 合并为一次 full_two_round；
    - 兼容历史 two-round 单调用（generate_two_round*）直接记一次。
    """
    if service != "pure_llm":
        return

    if method in _FULL_INFERENCE_METHODS:
        _record_inference_metrics(
            service=service,
            method=method,
            duration_ms=duration_ms,
            success=success,
            task_id=task_id,
            worker_name=worker_name,
            task_scope="full_two_round",
            trace_id=trace_id,
        )
        return

    if not trace_id:
        return

    client = _get_metrics_redis_client()
    if client is None:
        return

    now_ms = int(time.time() * 1000)
    start_key = f"{_TRACE_START_KEY_PREFIX}{trace_id}"
    done_key = f"{_TRACE_DONE_KEY_PREFIX}{trace_id}"

    try:
        if method in _TRACE_START_METHODS:
            client.set(start_key, now_ms, ex=_TRACE_KEY_TTL_SECONDS, nx=True)

        if method not in _TRACE_FINISH_METHODS:
            return

        # 防止同一 trace 重复记账（例如二次重试、重复调用）。
        marked = client.set(done_key, now_ms, ex=_TRACE_KEY_TTL_SECONDS, nx=True)
        if not marked:
            return

        start_raw = client.get(start_key)
        if start_raw is not None:
            try:
                start_ms = int(float(start_raw))
                full_duration_ms = max(0, now_ms - start_ms)
            except Exception:
                full_duration_ms = max(0, int(duration_ms))
        else:
            full_duration_ms = max(0, int(duration_ms))

        _record_inference_metrics(
            service=service,
            method=method,
            duration_ms=full_duration_ms,
            success=success,
            task_id=task_id,
            worker_name=worker_name,
            task_scope="full_two_round",
            trace_id=trace_id,
        )
    except Exception as exc:
        logger.warning(f"完整推理耗时聚合失败: {exc}")
    finally:
        try:
            client.delete(start_key)
        except Exception:
            pass


@celery_app.task(name="app.tasks.ai.invoke")
def invoke_ai_task(
    service: str,
    method: str,
    args: List[Any] | None = None,
    kwargs: Dict[str, Any] | None = None,
) -> Any:
    """
    通用推理任务：执行指定服务的方法并返回结果。
    """
    args = args or []
    kwargs = dict(kwargs or {})
    trace_id_raw = kwargs.pop(_METRICS_TRACE_ID_KWARG, None)
    trace_id = str(trace_id_raw).strip() if trace_id_raw is not None else None
    if trace_id == "":
        trace_id = None
    started_at = time.perf_counter()
    task_request = getattr(invoke_ai_task, "request", None)
    task_id = getattr(task_request, "id", None)
    worker_name = getattr(task_request, "hostname", None) or f"inference@{socket.gethostname()}"
    success = False

    try:
        target_service = _resolve_service(service)
        _ensure_worker_model_loaded(method)

        if not hasattr(target_service, method):
            raise AttributeError(f"{service} 不存在方法: {method}")

        target = getattr(target_service, method)
        if callable(target):
            result = target(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = asyncio.run(result)
            success = True
            return result

        if args or kwargs:
            raise ValueError(f"属性访问不允许携带参数: {service}.{method}")
        success = True
        return target
    finally:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        _record_full_inference_metrics(
            service=service,
            method=method,
            duration_ms=duration_ms,
            success=success,
            task_id=task_id,
            worker_name=worker_name,
            trace_id=trace_id,
        )


@celery_app.task(name="app.tasks.ai.ping")
def ping_task() -> Dict[str, Any]:
    """用于部署验证的轻量任务，不触发模型推理。"""
    return {
        "status": "ok",
        "worker_host": socket.gethostname(),
        "timestamp": datetime.now().isoformat(),
    }
