"""
应用配置API - 简单的两个路由
"""
from fastapi import APIRouter, HTTPException, Header, Depends, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import os
import json
import math
import copy
import time
import asyncio
from threading import Lock
from datetime import datetime, timezone
from urllib.parse import urlparse
from app.core.logging_config import get_logger
from typing import Optional, Literal, List, Dict, Any, Callable
from app.services.auth_service import auth_service
from app.services.security_audit_service import log_security_event
from app.core.auth import verify_developer_token
from app.core.response import UnifiedResponse
from app.core.celery_app import celery_app
from app.config import settings

router = APIRouter(prefix="/config", tags=["应用配置"])
logger = get_logger(__name__)

_RUNTIME_CACHE: Dict[str, Dict[str, Any]] = {}
_RUNTIME_CACHE_LOCK = Lock()
_RUNTIME_KEY_LOCKS: Dict[str, Lock] = {}
_RUNTIME_KEY_LOCKS_LOCK = Lock()
_RUNTIME_CACHE_TTL_SECONDS = 20.0
_RUNTIME_REDIS_CLIENTS: Dict[str, Any] = {}
_RUNTIME_REDIS_CLIENTS_LOCK = Lock()
_RUNTIME_CELERY_INSPECT_TIMEOUT_SECONDS = float(os.getenv("RUNTIME_CELERY_INSPECT_TIMEOUT_SECONDS", "0.5"))
_RUNTIME_INCLUDE_QUEUE_DETAILS = os.getenv("RUNTIME_INCLUDE_QUEUE_DETAILS", "0").strip().lower() in {"1", "true", "yes", "on"}


class AppConfigRequest(BaseModel):
    title: str
    subtitle: str
    backgroundStyle: Optional[Literal['mesh', 'ribbon']] = 'mesh'


class AppConfigResponse(BaseModel):
    title: str
    subtitle: str
    backgroundStyle: str = 'mesh'


def _parse_expected_workers() -> List[str]:
    """
    解析预期推理机列表，支持逗号或分号分隔。
    环境变量示例:
    CELERY_EXPECTED_WORKERS=inference@GPU-01,inference@GPU-02
    """
    raw = os.getenv("CELERY_EXPECTED_WORKERS", "").strip()
    if not raw:
        return []
    normalized = raw.replace(";", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def _to_int_or_none(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _sum_task_total(task_total: Any) -> int:
    if not isinstance(task_total, dict):
        return 0
    total = 0
    for value in task_total.values():
        if isinstance(value, (int, float)):
            total += int(value)
    return total


def _shorten_text(text: Any, max_len: int = 240) -> str:
    if text is None:
        return ""
    raw = str(text)
    if len(raw) <= max_len:
        return raw
    return raw[:max_len] + "..."


def _parse_redis_db_index(redis_url: str, default_db: int = 0) -> int:
    try:
        path = (urlparse(redis_url).path or "").strip("/")
        if path == "":
            return default_db
        return int(path)
    except (ValueError, TypeError):
        return default_db


def _scan_keys_limited(redis_client: Any, pattern: str, limit: int = 100) -> List[str]:
    keys: List[str] = []
    cursor = 0
    while True:
        cursor, batch = redis_client.scan(cursor=cursor, match=pattern, count=min(200, limit))
        if batch:
            keys.extend(batch)
        if cursor == 0 or len(keys) >= limit:
            break
    return keys[:limit]


def _decode_json_string(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, str) or not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _preview_redis_value(redis_client: Any, key: str) -> Dict[str, Any]:
    try:
        key_type = redis_client.type(key)
        ttl = redis_client.ttl(key)

        if key_type == "string":
            value = redis_client.get(key)
            preview = _shorten_text(value, 220)
        elif key_type == "hash":
            preview = _shorten_text(json.dumps(redis_client.hgetall(key), ensure_ascii=False), 220)
        elif key_type == "list":
            preview = _shorten_text(json.dumps(redis_client.lrange(key, 0, 4), ensure_ascii=False), 220)
        elif key_type == "set":
            cursor, members = redis_client.sscan(key, cursor=0, count=5)
            preview = _shorten_text(json.dumps(members, ensure_ascii=False), 220)
        elif key_type == "zset":
            cursor, members = redis_client.zscan(key, cursor=0, count=5)
            preview = _shorten_text(json.dumps(members, ensure_ascii=False), 220)
        else:
            preview = ""

        return {
            "key": key,
            "type": key_type,
            "ttl": ttl,
            "preview": preview
        }
    except Exception as exc:
        return {
            "key": key,
            "type": "unknown",
            "ttl": None,
            "preview": f"读取失败: {_shorten_text(exc, 180)}"
        }


def _load_cached_runtime_payload(
    cache_key: str,
    loader: Callable[[], Dict[str, Any]],
    ttl_seconds: float = _RUNTIME_CACHE_TTL_SECONDS
) -> Dict[str, Any]:
    now = time.monotonic()
    with _RUNTIME_CACHE_LOCK:
        cache_entry = _RUNTIME_CACHE.get(cache_key)
        if cache_entry and (now - float(cache_entry.get("ts", 0.0))) < ttl_seconds:
            logger.debug(f"runtime cache hit(fast): key={cache_key}, pid={os.getpid()}")
            return copy.deepcopy(cache_entry.get("data") or {})

    with _RUNTIME_KEY_LOCKS_LOCK:
        key_lock = _RUNTIME_KEY_LOCKS.setdefault(cache_key, Lock())

    with key_lock:
        now = time.monotonic()
        with _RUNTIME_CACHE_LOCK:
            cache_entry = _RUNTIME_CACHE.get(cache_key)
            if cache_entry and (now - float(cache_entry.get("ts", 0.0))) < ttl_seconds:
                logger.debug(f"runtime cache hit(locked): key={cache_key}, pid={os.getpid()}")
                return copy.deepcopy(cache_entry.get("data") or {})

        logger.debug(f"runtime cache miss: key={cache_key}, pid={os.getpid()}")
        loaded = loader()
        with _RUNTIME_CACHE_LOCK:
            _RUNTIME_CACHE[cache_key] = {
                "ts": time.monotonic(),
                "data": loaded
            }
        return copy.deepcopy(loaded)


def _get_or_create_runtime_redis_client(client_key: str, factory: Callable[[], Any]) -> Any:
    with _RUNTIME_REDIS_CLIENTS_LOCK:
        cached = _RUNTIME_REDIS_CLIENTS.get(client_key)
        if cached is not None:
            return cached
        created = factory()
        _RUNTIME_REDIS_CLIENTS[client_key] = created
        return created


def _drop_runtime_redis_client(client_key: str) -> None:
    with _RUNTIME_REDIS_CLIENTS_LOCK:
        _RUNTIME_REDIS_CLIENTS.pop(client_key, None)


def _collect_inference_worker_status(include_performance: bool = True) -> Dict[str, Any]:
    checked_at = datetime.now(timezone.utc).astimezone().isoformat()
    expected_workers = _parse_expected_workers()

    ping_result: Dict[str, Any] = {}
    stats_result: Dict[str, Any] = {}
    queues_result: Dict[str, Any] = {}
    broker_connected = True
    inspect_error: Optional[str] = None

    try:
        inspect = celery_app.control.inspect(timeout=_RUNTIME_CELERY_INSPECT_TIMEOUT_SECONDS)
        stats_result = inspect.stats() or {}
        if stats_result:
            ping_result = {worker_name: {"ok": "stats"} for worker_name in stats_result.keys()}
        else:
            ping_result = inspect.ping() or {}
        if _RUNTIME_INCLUDE_QUEUE_DETAILS:
            queues_result = inspect.active_queues() or {}
    except Exception as exc:
        broker_connected = False
        inspect_error = str(exc)
        logger.warning(f"获取推理机状态失败（Celery inspect）: {inspect_error}")

    discovered_workers = set(ping_result.keys()) | set(stats_result.keys()) | set(queues_result.keys())
    all_workers = sorted(set(expected_workers) | discovered_workers)

    worker_items: List[Dict[str, Any]] = []
    for worker_name in all_workers:
        worker_stats = stats_result.get(worker_name) if isinstance(stats_result, dict) else None
        worker_stats = worker_stats if isinstance(worker_stats, dict) else {}

        pool_stats = worker_stats.get("pool") if isinstance(worker_stats.get("pool"), dict) else {}
        broker_stats = worker_stats.get("broker") if isinstance(worker_stats.get("broker"), dict) else {}
        worker_queues = queues_result.get(worker_name) if isinstance(queues_result, dict) else []
        worker_queues = worker_queues if isinstance(worker_queues, list) else []

        queue_names: List[str] = []
        for queue_item in worker_queues:
            if isinstance(queue_item, dict):
                queue_name = queue_item.get("name")
                if isinstance(queue_name, str) and queue_name:
                    queue_names.append(queue_name)

        is_online = worker_name in ping_result
        is_expected = worker_name in expected_workers
        status = "online" if is_online else ("offline" if is_expected else "unreachable")
        if not queue_names and is_online and settings.CELERY_AI_QUEUE:
            queue_names = [settings.CELERY_AI_QUEUE]

        worker_items.append({
            "worker_name": worker_name,
            "status": status,
            "connected": is_online,
            "is_expected": is_expected,
            "pid": _to_int_or_none(worker_stats.get("pid")),
            "max_concurrency": _to_int_or_none(pool_stats.get("max-concurrency")),
            "process_count": len(pool_stats.get("processes", [])) if isinstance(pool_stats.get("processes"), list) else None,
            "uptime_seconds": _to_int_or_none(worker_stats.get("uptime")),
            "processed_tasks": _sum_task_total(worker_stats.get("total")),
            "queue_names": queue_names,
            "broker_transport": broker_stats.get("transport"),
            "broker_host": broker_stats.get("hostname"),
        })

    online_workers = sum(1 for worker in worker_items if worker["status"] == "online")
    offline_workers = sum(1 for worker in worker_items if worker["status"] == "offline")
    unexpected_workers = sum(1 for worker in worker_items if not worker["is_expected"])
    performance_data = _collect_inference_task_performance() if include_performance else None

    return {
        "summary": {
            "checked_at": checked_at,
            "queue": settings.CELERY_AI_QUEUE,
            "broker_connected": broker_connected,
            "total_workers": len(worker_items),
            "online_workers": online_workers,
            "offline_workers": offline_workers,
            "expected_workers": len(expected_workers),
            "unexpected_workers": unexpected_workers,
            "inspect_error": inspect_error
        },
        "workers": worker_items,
        "performance": performance_data,
    }


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _calculate_p95(values: List[int]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * 0.95) - 1))
    return float(ordered[index])


def _calculate_percentile(values: List[int], percentile: float) -> float:
    if not values:
        return 0.0
    ratio = max(0.0, min(1.0, percentile))
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * ratio) - 1))
    return float(ordered[index])


def _calculate_stddev(values: List[int]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def _build_duration_group_stats(tasks: List[Dict[str, Any]], group_field: str) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for task in tasks:
        key_value = task.get(group_field)
        if not isinstance(key_value, str) or not key_value.strip():
            key_value = "unknown"
        grouped.setdefault(key_value, []).append(task)

    results: List[Dict[str, Any]] = []
    for group_name, group_tasks in grouped.items():
        durations = [int(_safe_float(task.get("duration_ms"))) for task in group_tasks]
        success_count = sum(1 for task in group_tasks if bool(task.get("success", True)))
        fail_count = len(group_tasks) - success_count
        results.append({
            "name": group_name,
            "total_tasks": len(group_tasks),
            "success_tasks": success_count,
            "fail_tasks": fail_count,
            "success_rate": (success_count / len(group_tasks) * 100.0) if group_tasks else 0.0,
            "avg_duration_ms": (sum(durations) / len(durations)) if durations else 0.0,
            "p95_duration_ms": _calculate_percentile(durations, 0.95),
            "min_duration_ms": float(min(durations)) if durations else 0.0,
            "max_duration_ms": float(max(durations)) if durations else 0.0,
        })

    results.sort(key=lambda item: (item.get("total_tasks", 0), item.get("avg_duration_ms", 0.0)), reverse=True)
    return results


def _build_duration_timeline(tasks: List[Dict[str, Any]], bucket_seconds: int = 60) -> List[Dict[str, Any]]:
    if bucket_seconds <= 0:
        bucket_seconds = 60

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for task in tasks:
        raw_timestamp = task.get("timestamp")
        if not isinstance(raw_timestamp, str):
            continue
        try:
            parsed = datetime.fromisoformat(raw_timestamp)
        except Exception:
            continue
        bucket_dt = parsed.replace(second=0, microsecond=0)
        bucket_key = bucket_dt.isoformat()
        grouped.setdefault(bucket_key, []).append(task)

    timeline: List[Dict[str, Any]] = []
    for bucket_key in sorted(grouped.keys()):
        bucket_tasks = grouped[bucket_key]
        durations = [int(_safe_float(task.get("duration_ms"))) for task in bucket_tasks]
        success_count = sum(1 for task in bucket_tasks if bool(task.get("success", True)))
        fail_count = len(bucket_tasks) - success_count
        timeline.append({
            "timestamp": bucket_key,
            "task_count": len(bucket_tasks),
            "success_tasks": success_count,
            "fail_tasks": fail_count,
            "success_rate": (success_count / len(bucket_tasks) * 100.0) if bucket_tasks else 0.0,
            "avg_duration_ms": (sum(durations) / len(durations)) if durations else 0.0,
            "p95_duration_ms": _calculate_percentile(durations, 0.95),
            "min_duration_ms": float(min(durations)) if durations else 0.0,
            "max_duration_ms": float(max(durations)) if durations else 0.0,
        })

    return timeline


def _collect_inference_task_performance() -> Dict[str, Any]:
    """
    采集完整推理任务（两轮合并）耗时统计。
    数据来源：celery_worker 写入的 Redis list/hash。
    """
    sample_size = max(1, settings.CELERY_INFERENCE_METRICS_SAMPLE_SIZE)
    summary: Dict[str, Any] = {
        "total_tasks": 0,
        "success_tasks": 0,
        "fail_tasks": 0,
        "avg_duration_ms": 0.0,
        "min_duration_ms": 0.0,
        "max_duration_ms": 0.0,
        "p50_duration_ms": 0.0,
        "p90_duration_ms": 0.0,
        "p95_duration_ms": 0.0,
        "p99_duration_ms": 0.0,
        "std_duration_ms": 0.0,
        "last_duration_ms": 0.0,
        "last_timestamp": None,
        "last_worker_name": None,
        "sampled_tasks": 0,
        "sample_success_rate": 0.0,
        "sample_window_start": None,
        "sample_window_end": None,
        "error": None,
    }
    recent_tasks: List[Dict[str, Any]] = []
    timeline: List[Dict[str, Any]] = []
    by_method: List[Dict[str, Any]] = []
    by_worker: List[Dict[str, Any]] = []

    try:
        import redis  # type: ignore
    except Exception as exc:
        summary["error"] = f"redis 模块不可用: {exc}"
        return {"summary": summary, "recent_tasks": recent_tasks}

    redis_url = settings.CELERY_RESULT_BACKEND or settings.CELERY_BROKER_URL
    try:
        client = _get_or_create_runtime_redis_client(
            "metrics",
            lambda: redis.Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=0.8,
                socket_connect_timeout=0.8,
            )
        )
        client.ping()
        metrics_key = settings.CELERY_INFERENCE_METRICS_KEY
        agg_key = settings.CELERY_INFERENCE_METRICS_AGG_KEY

        agg_data = client.hgetall(agg_key) or {}
        sample_raw = client.lrange(metrics_key, 0, sample_size - 1) or []

        for item_raw in sample_raw:
            try:
                parsed = json.loads(item_raw)
            except Exception:
                continue
            if not isinstance(parsed, dict):
                continue
            if parsed.get("task_scope") not in (None, "full_two_round"):
                continue

            duration_ms = _safe_float(parsed.get("duration_ms"))
            timestamp = parsed.get("timestamp")
            if not isinstance(timestamp, str):
                continue
            recent_tasks.append({
                "timestamp": timestamp,
                "duration_ms": duration_ms,
                "worker_name": parsed.get("worker_name"),
                "method": parsed.get("method"),
                "service": parsed.get("service"),
                "task_id": parsed.get("task_id"),
                "success": bool(parsed.get("success", True)),
            })

        # list 是 LPUSH（最新在前），前端图表按时间正序更直观
        recent_tasks.sort(key=lambda item: item.get("timestamp") or "")
        durations = [int(task["duration_ms"]) for task in recent_tasks if task.get("duration_ms") is not None]

        summary["total_tasks"] = _safe_int(agg_data.get("total_count"), default=len(recent_tasks))
        summary["success_tasks"] = _safe_int(agg_data.get("success_count"), default=0)
        summary["fail_tasks"] = _safe_int(agg_data.get("fail_count"), default=0)
        summary["last_duration_ms"] = _safe_float(agg_data.get("last_duration_ms"))
        summary["last_timestamp"] = agg_data.get("last_timestamp")
        summary["last_worker_name"] = agg_data.get("last_worker_name")

        total_duration_ms = _safe_float(agg_data.get("total_duration_ms"), default=0.0)
        if summary["total_tasks"] > 0 and total_duration_ms > 0:
            summary["avg_duration_ms"] = total_duration_ms / summary["total_tasks"]
        elif durations:
            summary["avg_duration_ms"] = sum(durations) / len(durations)
        summary["p95_duration_ms"] = _calculate_p95(durations)

        if durations:
            summary["min_duration_ms"] = float(min(durations))
            summary["max_duration_ms"] = float(max(durations))
            summary["p50_duration_ms"] = _calculate_percentile(durations, 0.50)
            summary["p90_duration_ms"] = _calculate_percentile(durations, 0.90)
            summary["p99_duration_ms"] = _calculate_percentile(durations, 0.99)
            summary["std_duration_ms"] = _calculate_stddev(durations)

        summary["sampled_tasks"] = len(recent_tasks)
        sample_success_tasks = sum(1 for task in recent_tasks if bool(task.get("success", True)))
        summary["sample_success_rate"] = (sample_success_tasks / len(recent_tasks) * 100.0) if recent_tasks else 0.0
        summary["sample_window_start"] = recent_tasks[0]["timestamp"] if recent_tasks else None
        summary["sample_window_end"] = recent_tasks[-1]["timestamp"] if recent_tasks else None

        timeline = _build_duration_timeline(recent_tasks, bucket_seconds=60)
        by_method = _build_duration_group_stats(recent_tasks, "method")
        by_worker = _build_duration_group_stats(recent_tasks, "worker_name")
    except Exception as exc:
        _drop_runtime_redis_client("metrics")
        summary["error"] = f"推理耗时统计读取失败: {exc}"

    return {
        "summary": summary,
        "recent_tasks": recent_tasks,
        "timeline": timeline,
        "by_method": by_method,
        "by_worker": by_worker,
    }


def _collect_redis_runtime_status(
    include_workflow_sessions: bool = True,
    include_async_tasks: bool = True,
    include_key_samples: bool = True,
) -> Dict[str, Any]:
    checked_at = datetime.now(timezone.utc).astimezone().isoformat()
    backend_key_samples: List[Dict[str, Any]] = []
    workflow_sessions: List[Dict[str, Any]] = []
    async_tasks: List[Dict[str, Any]] = []
    databases: List[Dict[str, Any]] = []

    summary: Dict[str, Any] = {
        "checked_at": checked_at,
        "backend_connected": False,
        "broker_connected": False,
        "backend_db_key_count": 0,
        "broker_db_key_count": 0,
        "workflow_session_count": 0,
        "async_task_count": 0,
        "errors": []
    }

    try:
        import redis  # type: ignore
    except Exception as exc:
        summary["errors"].append(f"redis 模块不可用: {exc}")
        return {
            "summary": summary,
            "databases": databases,
            "workflow_sessions": workflow_sessions,
            "async_tasks": async_tasks,
            "key_samples": backend_key_samples
        }

    backend_client = None
    try:
        backend_client = _get_or_create_runtime_redis_client(
            "backend",
            lambda: redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True,
                socket_timeout=0.8,
                socket_connect_timeout=0.8,
            )
        )
        backend_client.ping()
        summary["backend_connected"] = True

        backend_db_keys = backend_client.dbsize()
        summary["backend_db_key_count"] = backend_db_keys

        session_keys = _scan_keys_limited(backend_client, "wf:session:*", limit=100)
        task_keys = _scan_keys_limited(backend_client, "ai:command:task:*", limit=100)
        summary["workflow_session_count"] = len(session_keys)
        summary["async_task_count"] = len(task_keys)

        if include_workflow_sessions:
            for key in session_keys[:8]:
                raw = backend_client.get(key)
                payload = _decode_json_string(raw)
                step_data = payload.get("step_data") if isinstance(payload.get("step_data"), dict) else {}
                workflow_sessions.append({
                    "key": key,
                    "user_id": payload.get("user_id"),
                    "workflow_id": payload.get("workflow_id"),
                    "current_step": payload.get("current_step"),
                    "status": payload.get("status"),
                    "updated_at": payload.get("updated_at"),
                    "step_data_keys": list(step_data.keys())[:8]
                })

        if include_async_tasks:
            for key in task_keys[:8]:
                raw = backend_client.get(key)
                payload = _decode_json_string(raw)
                async_tasks.append({
                    "key": key,
                    "task_id": payload.get("task_id"),
                    "status": payload.get("status"),
                    "updated_at": payload.get("updated_at"),
                    "error": _shorten_text(payload.get("error"), 120)
                })

        sample_keys: List[str] = []
        if include_key_samples:
            sample_keys = _scan_keys_limited(backend_client, "*", limit=12)
            backend_key_samples.extend([{"database": "backend", **_preview_redis_value(backend_client, key)} for key in sample_keys])

        databases.append({
            "name": "backend",
            "host": f"{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            "db_index": settings.REDIS_DB,
            "connected": True,
            "key_count": backend_db_keys,
            "sample_key_count": len(sample_keys),
            "error": None
        })
    except Exception as exc:
        _drop_runtime_redis_client("backend")
        summary["errors"].append(f"backend redis 连接失败: {exc}")
        databases.append({
            "name": "backend",
            "host": f"{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            "db_index": settings.REDIS_DB,
            "connected": False,
            "key_count": 0,
            "sample_key_count": 0,
            "error": str(exc)
        })

    broker_url = settings.CELERY_BROKER_URL
    broker_db_index = _parse_redis_db_index(broker_url, default_db=1)
    try:
        broker_client = _get_or_create_runtime_redis_client(
            "broker",
            lambda: redis.Redis.from_url(
                broker_url,
                decode_responses=True,
                socket_timeout=0.8,
                socket_connect_timeout=0.8,
            )
        )
        broker_client.ping()
        summary["broker_connected"] = True
        broker_db_keys = broker_client.dbsize()
        summary["broker_db_key_count"] = broker_db_keys

        broker_sample_keys: List[str] = []
        if include_key_samples:
            broker_sample_keys = _scan_keys_limited(broker_client, "*", limit=12)
            backend_key_samples.extend([{"database": "broker", **_preview_redis_value(broker_client, key)} for key in broker_sample_keys])

        databases.append({
            "name": "broker",
            "host": urlparse(broker_url).netloc,
            "db_index": broker_db_index,
            "connected": True,
            "key_count": broker_db_keys,
            "sample_key_count": len(broker_sample_keys),
            "error": None
        })
    except Exception as exc:
        _drop_runtime_redis_client("broker")
        summary["errors"].append(f"broker redis 连接失败: {exc}")
        databases.append({
            "name": "broker",
            "host": urlparse(broker_url).netloc,
            "db_index": broker_db_index,
            "connected": False,
            "key_count": 0,
            "sample_key_count": 0,
            "error": str(exc)
        })

    return {
        "summary": summary,
        "databases": databases,
        "workflow_sessions": workflow_sessions,
        "async_tasks": async_tasks,
        "key_samples": backend_key_samples[:24]
    }


@router.get("/app")
async def get_app_config():
    """获取应用配置"""
    title = os.getenv('APP_TITLE', 'AILF')
    subtitle = os.getenv('APP_SUBTITLE', '开发者配置面板')
    background_style = os.getenv('APP_BACKGROUND_STYLE', 'mesh')
    
    return UnifiedResponse.success(
        message="获取应用配置成功",
        data={
            "title": title,
            "subtitle": subtitle,
            "backgroundStyle": background_style
        }
    )


@router.post("/app")
async def update_app_config(
    config: AppConfigRequest,
    http_request: Request,
    current_user: dict = Depends(verify_developer_token)
):
    """更新应用配置"""
    try:
        # 更新环境变量文件
        env_file_path = ".env"
        env_lines = []

        # 读取现有的.env文件
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r', encoding='utf-8') as f:
                env_lines = f.readlines()

        # 更新或添加配置项
        updated_lines = []
        title_updated = False
        subtitle_updated = False

        for line in env_lines:
            if line.startswith("APP_TITLE="):
                updated_lines.append(f'APP_TITLE="{config.title}"\n')
                title_updated = True
            elif line.startswith("APP_SUBTITLE="):
                updated_lines.append(f'APP_SUBTITLE="{config.subtitle}"\n')
                subtitle_updated = True
            else:
                updated_lines.append(line)

        # 如果配置项不存在，则添加
        if not title_updated:
            updated_lines.append(f'APP_TITLE="{config.title}"\n')
        if not subtitle_updated:
            updated_lines.append(f'APP_SUBTITLE="{config.subtitle}"\n')
        
        # 处理背景样式
        background_style = config.backgroundStyle or 'mesh'
        bg_updated = False
        final_lines = []
        for line in updated_lines:
            if line.startswith("APP_BACKGROUND_STYLE="):
                final_lines.append(f'APP_BACKGROUND_STYLE="{background_style}"\n')
                bg_updated = True
            else:
                final_lines.append(line)
        if not bg_updated:
            final_lines.append(f'APP_BACKGROUND_STYLE="{background_style}"\n')

        # 写入.env文件
        with open(env_file_path, 'w', encoding='utf-8') as f:
            f.writelines(final_lines)

        # 更新运行时环境变量
        os.environ['APP_TITLE'] = config.title
        os.environ['APP_SUBTITLE'] = config.subtitle
        os.environ['APP_BACKGROUND_STYLE'] = background_style

        logger.info(f"应用配置更新成功: 标题={config.title}, 副标题={config.subtitle}, 背景={background_style}")
        log_security_event(
            event_type="config",
            action="update_app_config",
            actor_type="developer",
            actor_id=str(current_user.get("user_id", "developer")),
            success=True,
            request=http_request,
            target_type="app_config",
            target_id="global",
            details={
                "title": config.title,
                "subtitle": config.subtitle,
                "backgroundStyle": background_style
            }
        )

        return UnifiedResponse.success(
            message="应用配置更新成功",
            data={
                "title": config.title,
                "subtitle": config.subtitle,
                "backgroundStyle": background_style
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新应用配置失败: {str(e)}")
        log_security_event(
            event_type="config",
            action="update_app_config",
            actor_type="developer",
            actor_id=str(current_user.get("user_id", "developer")),
            success=False,
            request=http_request,
            target_type="app_config",
            target_id="global",
            error="update_config_failed",
            details={"reason": str(e)}
        )
        raise UnifiedResponse.internal_error(
            message="更新应用配置失败",
            error_type="update_config_failed",
            details=str(e)
        )


@router.get("/developer/status")
async def get_developer_status(
    authorization: Optional[str] = Header(None)
):
    """获取开发者认证状态"""
    if not authorization:
        raise UnifiedResponse.unauthorized(
            message="未提供认证信息",
            error_type="no_token",
            details={
                "authenticated": False,
                "reason": "no_token"
            }
        )
    
    try:
        # 验证token
        token = authorization.replace("Bearer ", "")
        verify_result = auth_service.verify_token(token)
        is_valid = verify_result.get("success", False)

        return UnifiedResponse.success(
            message="获取开发者状态成功",
            data={
                "authenticated": is_valid,
                "reason": "valid_token" if is_valid else "invalid_token"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="验证开发者状态失败",
            error_type="verification_error",
            details={
                "authenticated": False,
                "reason": "verification_error",
                "error": str(e)
            }
        )


@router.get("/inference/workers")
async def get_inference_worker_status(
    _: dict = Depends(verify_developer_token)
):
    """
    获取推理机（Celery Worker）在线情况。
    """
    inference_data = await run_in_threadpool(
        lambda: _load_cached_runtime_payload(
            "runtime:inference:full",
            lambda: _collect_inference_worker_status(include_performance=True)
        )
    )

    return UnifiedResponse.success(
        message="获取推理机状态成功",
        data=inference_data
    )


@router.get("/runtime/dashboard")
async def get_runtime_dashboard(
    _: dict = Depends(verify_developer_token)
):
    """
    获取运行监控摘要数据（精简版）。
    """
    inference_task = run_in_threadpool(
        lambda: _load_cached_runtime_payload(
            "runtime:inference:full",
            lambda: _collect_inference_worker_status(include_performance=True)
        )
    )
    redis_task = run_in_threadpool(
        lambda: _load_cached_runtime_payload(
            "runtime:redis:full",
            lambda: _collect_redis_runtime_status(
                include_workflow_sessions=True,
                include_async_tasks=True,
                include_key_samples=True,
            )
        )
    )
    inference_data, redis_data = await asyncio.gather(inference_task, redis_task)

    return UnifiedResponse.success(
        message="获取运行监控摘要成功",
        data={
            "checked_at": datetime.now(timezone.utc).astimezone().isoformat(),
            "inference": {
                "summary": inference_data.get("summary", {}),
                "performance": {
                    "summary": (inference_data.get("performance") or {}).get("summary", {}),
                }
            },
            "redis": {
                "summary": redis_data.get("summary", {}),
                "databases": redis_data.get("databases", []),
            }
        }
    )


@router.get("/runtime/inference/overview")
async def get_runtime_inference_overview(
    _: dict = Depends(verify_developer_token)
):
    """
    获取运行监控 - 推理机概览（摘要 + 节点列表）。
    """
    inference_data = await run_in_threadpool(
        lambda: _load_cached_runtime_payload(
            "runtime:inference:full",
            lambda: _collect_inference_worker_status(include_performance=True)
        )
    )
    return UnifiedResponse.success(
        message="获取推理机概览成功",
        data={
            "summary": inference_data.get("summary", {}),
            "workers": inference_data.get("workers", []),
        }
    )


@router.get("/runtime/inference/performance")
async def get_runtime_inference_performance(
    _: dict = Depends(verify_developer_token)
):
    """
    获取运行监控 - 完整推理任务耗时统计。
    """
    inference_data = await run_in_threadpool(
        lambda: _load_cached_runtime_payload(
            "runtime:inference:full",
            lambda: _collect_inference_worker_status(include_performance=True)
        )
    )
    performance_data = inference_data.get("performance") or {"summary": {}, "recent_tasks": []}
    return UnifiedResponse.success(
        message="获取推理耗时统计成功",
        data=performance_data
    )


@router.get("/runtime/redis/overview")
async def get_runtime_redis_overview(
    _: dict = Depends(verify_developer_token)
):
    """
    获取运行监控 - Redis 概览（摘要 + DB 状态）。
    """
    redis_data = await run_in_threadpool(
        lambda: _load_cached_runtime_payload(
            "runtime:redis:full",
            lambda: _collect_redis_runtime_status(
                include_workflow_sessions=True,
                include_async_tasks=True,
                include_key_samples=True,
            )
        )
    )
    return UnifiedResponse.success(
        message="获取 Redis 概览成功",
        data={
            "summary": redis_data.get("summary", {}),
            "databases": redis_data.get("databases", []),
        }
    )


@router.get("/runtime/redis/workflow-sessions")
async def get_runtime_redis_workflow_sessions(
    _: dict = Depends(verify_developer_token)
):
    """
    获取运行监控 - 工作流会话样本。
    """
    redis_data = await run_in_threadpool(
        lambda: _load_cached_runtime_payload(
            "runtime:redis:full",
            lambda: _collect_redis_runtime_status(
                include_workflow_sessions=True,
                include_async_tasks=True,
                include_key_samples=True,
            )
        )
    )
    return UnifiedResponse.success(
        message="获取工作流会话样本成功",
        data={
            "workflow_sessions": redis_data.get("workflow_sessions", [])
        }
    )


@router.get("/runtime/redis/async-tasks")
async def get_runtime_redis_async_tasks(
    _: dict = Depends(verify_developer_token)
):
    """
    获取运行监控 - 异步任务样本。
    """
    redis_data = await run_in_threadpool(
        lambda: _load_cached_runtime_payload(
            "runtime:redis:full",
            lambda: _collect_redis_runtime_status(
                include_workflow_sessions=True,
                include_async_tasks=True,
                include_key_samples=True,
            )
        )
    )
    return UnifiedResponse.success(
        message="获取异步任务样本成功",
        data={
            "async_tasks": redis_data.get("async_tasks", [])
        }
    )


@router.get("/runtime/redis/key-samples")
async def get_runtime_redis_key_samples(
    _: dict = Depends(verify_developer_token)
):
    """
    获取运行监控 - Redis Key 样本。
    """
    redis_data = await run_in_threadpool(
        lambda: _load_cached_runtime_payload(
            "runtime:redis:full",
            lambda: _collect_redis_runtime_status(
                include_workflow_sessions=True,
                include_async_tasks=True,
                include_key_samples=True,
            )
        )
    )
    return UnifiedResponse.success(
        message="获取 Redis Key 样本成功",
        data={
            "key_samples": redis_data.get("key_samples", [])
        }
    )
