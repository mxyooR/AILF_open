"""工作流会话：Redis 保存有期限的快照，故障时退回容量受限的本地缓存。"""
import asyncio
from contextlib import asynccontextmanager
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from weakref import WeakValueDictionary
import ast
import json
import math
import re
import time
import uuid

from app.config import settings
from app.core.logging_config import get_logger
from app.services.workflow_context import MISSING, resolve_context_value
from app.services.workflow_graph import normalize_nodes

logger = get_logger(__name__)


class WorkflowSession:
    """一个流程执行实例，保存定义快照、当前节点、输入、输出和执行历史。"""
    def __init__(self, user_id, workflow_id, workflow_data):
        self.id = uuid.uuid4().hex
        self.user_id = user_id
        self.workflow_id = workflow_id
        self.workflow_data = deepcopy(workflow_data)
        self.workflow_data["nodes"] = normalize_nodes(workflow_data.get("nodes") or [])
        starts = [node["id"] for node in self.workflow_data["nodes"] if node.get("type") == "start"]
        if len(starts) != 1:
            raise ValueError("工作流需要一个开始节点")
        self.current_step = starts[0]
        self.step_data = {}
        self.input_data = {}
        self.completed_steps = []
        self.execution_history = []
        self.priority = "normal"
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.status = "active"
        self.revision = 0

    def to_dict(self):
        """序列化快照，包括版本号；版本用于处理系统时钟精度不足时的冲突。"""
        return {
            "id": self.id, "user_id": self.user_id, "workflow_id": self.workflow_id,
            "workflow_data": self.workflow_data, "current_step": self.current_step,
            "step_data": self.step_data, "input_data": self.input_data,
            "completed_steps": self.completed_steps, "execution_history": self.execution_history,
            "priority": self.priority, "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(), "status": self.status, "revision": self.revision,
        }

    @classmethod
    def from_dict(cls, data):
        """恢复会话快照，并为没有实例 ID 的旧会话生成稳定 ID。"""
        session = cls(data["user_id"], data["workflow_id"], data["workflow_data"])
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.updated_at = datetime.fromisoformat(data.get("updated_at", data["created_at"]))
        session.id = data.get("id") or uuid.uuid5(
            uuid.NAMESPACE_URL, f"{session.user_id}:{session.workflow_id}:{data['created_at']}"
        ).hex
        session.current_step = data.get("current_step", session.current_step)
        session.step_data = data.get("step_data") or {}
        session.input_data = data.get("input_data") or {}
        session.completed_steps = data.get("completed_steps") or []
        session.execution_history = data.get("execution_history") or []
        session.priority = data.get("priority", "normal")
        session.status = data.get("status", "active")
        session.revision = int(data.get("revision", 0))
        return session


class WorkflowSessionService:
    """每个用户只有一个当前会话；结束的实例在 TTL 内仍可查询。"""
    def __init__(self, *, capacity=1024, ttl=None):
        # _memory 是用户到当前实例的索引，_instances 保存仍未过期的历史快照。
        self._memory: Dict[str, WorkflowSession] = {}
        self._instances: Dict[str, WorkflowSession] = {}
        self._dirty = set()  # Redis 写入失败、尚待比较并同步的本地实例。
        self._locks = WeakValueDictionary()
        self.capacity = max(1, capacity)
        self.ttl = max(1, ttl if ttl is not None else settings.REDIS_SESSION_TTL)
        self._redis = None
        self._redis_enabled = False
        self._init_redis()

    def _init_redis(self):
        try:
            import redis
            self._redis = redis.Redis(
                host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None, decode_responses=True,
                socket_timeout=2, socket_connect_timeout=2,
            )
            self._redis.ping()
            self._redis_enabled = True
        except Exception:
            self._redis = None
            self._redis_enabled = False
            logger.warning("Redis 不可用，工作流会话使用内存存储")

    def _session_key(self, user_id):
        return f"wf:session:{user_id}"

    @staticmethod
    def _instance_key(instance_id):
        return f"wf:instance:{instance_id}"

    def _expired(self, session):
        """只根据最后一次状态变更判断过期，查询不会延长会话寿命。"""
        return time.time() - session.updated_at.timestamp() >= self.ttl

    def _prune(self):
        """清理过期项，容量不足时先淘汰已经结束的快照。"""
        for instance_id, session in list(self._instances.items()):
            if self._expired(session):
                self._instances.pop(instance_id, None)
                self._dirty.discard(instance_id)
                if self._memory.get(session.user_id) is session:
                    self._memory.pop(session.user_id, None)
        while len(self._instances) > self.capacity:
            oldest = min(self._instances.values(), key=lambda item: (
                item.status == "active", item.updated_at.timestamp()
            ))
            self._instances.pop(oldest.id, None)
            self._dirty.discard(oldest.id)
            if self._memory.get(oldest.user_id) is oldest:
                self._memory.pop(oldest.user_id, None)

    def _cache(self, session):
        """更新用户索引和实例缓存，同时保持本地容量有界。"""
        self._instances[session.id] = session
        previous = self._memory.get(session.user_id)
        if previous is None or previous.created_at.timestamp() <= session.created_at.timestamp():
            self._memory[session.user_id] = session
        self._prune()

    def _read_snapshot(self, raw):
        """解码 Redis 数据并过滤逻辑上已过期的快照。"""
        if not raw:
            return None
        session = WorkflowSession.from_dict(json.loads(raw))
        return None if self._expired(session) else session

    @staticmethod
    def _select_snapshot(local, remote, *, prefer_remote=False):
        """先区分新旧实例，再比较同一实例版本，恢复时以已发布的远端版本为准。"""
        if local is None:
            return remote
        if remote is None:
            return local
        if local.id != remote.id:
            return remote if remote.created_at >= local.created_at else local
        # 同一实例先看版本。离线写回遇到相同版本时，以已发布的远端状态为准。
        if remote.revision > local.revision or remote.updated_at > local.updated_at:
            return remote
        if prefer_remote and remote.revision == local.revision:
            return remote
        return local

    def _save_session(self, session):
        """先比较远端快照再写入；写失败时保留本地状态，恢复时避免覆盖新实例。"""
        if self._expired(session):
            self._prune()
            return False
        self._cache(session)
        if not self._redis_enabled or self._redis is None:
            self._dirty.add(session.id)
            return True
        try:
            from redis.exceptions import WatchError
            for _ in range(3):
                try:
                    # 读取和恢复也可能与其他进程竞争；WATCH 让比较和写入成为一次条件事务。
                    with self._redis.pipeline(transaction=True) as pipeline:
                        pipeline.watch(self._instance_key(session.id), self._session_key(session.user_id))
                        remote = self._read_snapshot(pipeline.get(self._instance_key(session.id)))
                        pointer = self._read_snapshot(pipeline.get(self._session_key(session.user_id)))
                        if remote is not None and self._select_snapshot(
                            session, remote, prefer_remote=session.id in self._dirty
                        ) is remote:
                            self._dirty.discard(session.id)
                            self._cache(remote)
                            if pointer is not None:
                                self._cache(pointer)
                            return False
                        if pointer is not None and pointer.id != session.id and pointer.created_at >= session.created_at:
                            self._dirty.discard(session.id)
                            if remote is not None:
                                self._cache(remote)
                            self._cache(pointer)
                            return False
                        payload = json.dumps(session.to_dict(), ensure_ascii=False, default=str)
                        remaining = min(self.ttl, max(1, math.ceil(self.ttl - (time.time() - session.updated_at.timestamp()))))
                        pipeline.multi()
                        pipeline.setex(self._instance_key(session.id), remaining, payload)
                        pipeline.setex(self._session_key(session.user_id), remaining, payload)
                        pipeline.execute()
                    self._dirty.discard(session.id)
                    return True
                except WatchError:
                    continue
            logger.warning("Redis 状态被并发更新，保留本地状态等待重新读取")
        except Exception:
            logger.warning("Redis 写入失败，保留较新的本地工作流状态")
        self._dirty.add(session.id)
        return True

    def _load_session(self, user_id):
        """读取当前会话，在远端可用时先比较版本，故障时返回尚未过期的本地数据。"""
        self._prune()
        local = self._memory.get(user_id)
        if self._redis_enabled and self._redis is not None:
            try:
                remote = self._read_snapshot(self._redis.get(self._session_key(user_id)))
                if remote is None and (local is None or local.id not in self._dirty):
                    self._memory.pop(user_id, None)
                    return None
                selected = self._select_snapshot(
                    local, remote, prefer_remote=local is not None and local.id in self._dirty
                )
                if selected is local and local is not None and local.id in self._dirty:
                    self._save_session(local)
                    return self._memory.get(user_id)
                if selected is not None:
                    if local is not None and selected is remote:
                        self._dirty.discard(local.id)
                    self._cache(selected)
                return selected
            except Exception:
                logger.warning("Redis 读取失败，使用未过期的本地工作流状态")
        return local

    def get_instance(self, instance_id):
        """读取指定实例，包括已结束但仍在 TTL 内的快照。"""
        self._prune()
        local = self._instances.get(instance_id)
        if self._redis_enabled and self._redis is not None:
            try:
                remote = self._read_snapshot(self._redis.get(self._instance_key(instance_id)))
                if remote is None and (local is None or instance_id not in self._dirty):
                    self._instances.pop(instance_id, None)
                    return None
                selected = self._select_snapshot(
                    local, remote, prefer_remote=local is not None and local.id in self._dirty
                )
                if selected is local and local is not None and instance_id in self._dirty:
                    self._save_session(local)
                    return self._instances.get(instance_id)
                if selected is not None:
                    if selected is remote:
                        self._dirty.discard(instance_id)
                    self._cache(selected)
                return selected
            except Exception:
                logger.warning("Redis 实例读取失败，使用未过期的本地工作流状态")
        return local

    def list_sessions(self):
        """合并 Redis 与本地的未过期快照，供实例列表和统计使用。"""
        self._prune()
        # 列表结果与缓存分开收集；缓存容量只能限制本进程内存，不能截断 Redis 中的实例。
        sessions = dict(self._instances)
        if self._redis_enabled and self._redis is not None:
            try:
                # 同时读取旧的用户快照，兼容尚未生成独立 instance 键的历史会话。
                for pattern in ("wf:instance:*", "wf:session:*"):
                    for key in self._redis.scan_iter(match=pattern, count=100):
                        try:
                            remote = self._read_snapshot(self._redis.get(key))
                        except (ValueError, TypeError, KeyError):
                            logger.warning("忽略格式不完整的工作流快照")
                            continue
                        if remote is None:
                            continue
                        selected = self._select_snapshot(
                            sessions.get(remote.id), remote, prefer_remote=remote.id in self._dirty
                        )
                        if selected is remote:
                            self._dirty.discard(remote.id)
                        sessions[remote.id] = selected
                        self._cache(selected)
            except Exception:
                logger.warning("Redis 实例列表读取失败，使用本地工作流状态")
        self._prune()
        return [session for session in sessions.values() if not self._expired(session)]

    @asynccontextmanager
    async def execution_lock(self, user_id):
        """同一用户的重建和提交串行执行；Redis 可用时同时取得跨进程锁。"""
        lock = self._locks.get(user_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[user_id] = lock
        async with lock:
            remote_lock = None
            if self._redis_enabled and self._redis is not None:
                try:
                    remote_lock = self._redis.lock(
                        # 部分旧部署尚无异步命令超时配置，缺少该配置不能导致跨进程锁被跳过。
                        f"wf:lock:{user_id}", timeout=max(600, getattr(settings, "AI_COMMAND_TIMEOUT_SECONDS", 540) * 2),
                        thread_local=False,
                    )
                    acquired = await asyncio.to_thread(remote_lock.acquire, blocking=False)
                except Exception:
                    remote_lock = None
                    acquired = True
                    logger.warning("Redis 锁不可用，工作流执行由本进程串行保护")
                if not acquired:
                    raise RuntimeError("工作流正在执行，请稍后重试")
            try:
                yield
            finally:
                if remote_lock is not None:
                    try:
                        await asyncio.to_thread(remote_lock.release)
                    except Exception:
                        logger.warning("工作流执行锁释放失败")

    def create_session(self, user_id, workflow_id, workflow_data):
        """验证新定义后替换当前会话，避免错误的新流程取消可用的旧实例。"""
        self._prune()
        existing = self.get_active_session(user_id)
        if not existing and not self._redis_enabled and sum(
            item.status == "active" for item in self._instances.values()
        ) >= self.capacity:
            raise RuntimeError("工作流会话容量已满")
        # 先验证新定义，再取消旧实例；新定义有误时仍保留用户原来的流程。
        session = WorkflowSession(user_id, workflow_id, workflow_data)
        if existing:
            self.end_session(user_id, "cancelled")
        # Windows 的时钟可能连续返回同一个时间，保证同一用户的新实例严格晚于旧实例。
        previous = self._memory.get(user_id)
        if previous is not None and session.created_at <= previous.updated_at:
            session.created_at = previous.updated_at + timedelta(microseconds=1)
            session.updated_at = session.created_at
        self._save_session(session)
        return session

    def get_active_session(self, user_id):
        """只返回尚未过期且仍在运行的当前实例。"""
        session = self._load_session(user_id)
        return session if session is not None and session.status == "active" else None

    @staticmethod
    def _touch(session):
        """推进快照版本，同时保证更新时间在系统时钟回拨或精度不足时仍递增。"""
        session.revision += 1
        session.updated_at = max(datetime.now(), session.updated_at + timedelta(microseconds=1))

    def update_session_step(self, user_id, workflow_id, new_step, step_data=None):
        """节点必须存在且工作流 ID 一致，更新后推进快照版本。"""
        session = self.get_active_session(user_id)
        if session is None or session.workflow_id != workflow_id:
            return False
        if not any(node["id"] == new_step for node in session.workflow_data["nodes"]):
            return False
        session.current_step = new_step
        if step_data is not None:
            session.step_data.update(deepcopy(step_data))
        self._touch(session)
        return self._save_session(session)

    def mark_step_completed(self, user_id, node_id, input_data=None, output_data=None):
        """记录完成步骤和输入输出历史，限制历史长度避免无限增长。"""
        session = self.get_active_session(user_id)
        if session is None or session.current_step != node_id:
            return False
        if node_id not in session.completed_steps:
            session.completed_steps.append(node_id)
        node = next(item for item in session.workflow_data["nodes"] if item["id"] == node_id)
        now = datetime.now()
        session.execution_history.append({
            "step_id": node_id, "step_name": node.get("name", node_id), "status": "completed",
            "started_at": session.updated_at.isoformat(), "completed_at": now.isoformat(),
            "input_data": deepcopy(input_data or {}), "output_data": deepcopy(output_data),
        })
        session.execution_history = session.execution_history[-1000:]
        self._touch(session)
        return self._save_session(session)

    def end_session(self, user_id, status="completed"):
        """记录完成、取消或失败状态，并保留可查询的结束快照。"""
        session = self.get_active_session(user_id)
        if session is None or status not in {"completed", "cancelled", "failed"}:
            return False
        session.status = status
        self._touch(session)
        return self._save_session(session)

    def get_current_step_info(self, user_id):
        """提供当前节点、流程名称和累计数据，供前端或 AI 继续流程。"""
        session = self.get_active_session(user_id)
        if session is None:
            return None
        node = next((item for item in session.workflow_data["nodes"]
                     if item["id"] == session.current_step), None)
        return {"session": session.to_dict(), "current_node": node,
                "workflow_name": session.workflow_data.get("name", ""), "step_data": session.step_data}

    def get_next_step(self, user_id, current_data=None):
        """按有序出边匹配条件，同时兼容旧条件节点的内部条件配置。"""
        session = self.get_active_session(user_id)
        if session is None:
            return None
        return self.get_next_step_for_session(session, current_data)

    def get_next_step_for_session(self, session, current_data=None):
        """只计算给定快照的下一步，不写存储；新入口可在替换旧会话前验证。"""
        node = next((item for item in session.workflow_data["nodes"]
                     if item["id"] == session.current_step), None)
        if node is None:
            return None
        if node.get("type") == "end":
            return node["id"]
        edges = node.get("child_nodes") or []
        if not edges:
            return None
        data = {**session.step_data, **(current_data or {}),
                "__form_completed__": session.current_step in session.completed_steps}
        config = node.get("config") or {}
        if node.get("type") == "condition" and (
            config.get("conditions") or config.get("evaluation_expression")
        ) and all(not edge.get("condition") or edge["condition"].get("type") == "always" for edge in edges):
            if config.get("evaluation_expression"):
                outcome = self._evaluate_expression(config["evaluation_expression"], data)
            else:
                values = [self._evaluate_condition(item, data, {}) for item in config["conditions"]]
                outcome = any(values) if config.get("logic", "and") == "or" else all(values)
            instructions = node.get("ai_instructions") or {}
            target = instructions.get("true_path" if outcome else "false_path")
            targets = {item["node_id"] for item in edges}
            if target in targets:
                return target
            index = 0 if outcome else 1
            return edges[index]["node_id"] if len(edges) > index else None
        for edge in edges:
            if self._evaluate_condition(edge.get("condition"), data, {}):
                return edge["node_id"]
        return None

    def _evaluate_condition(self, condition, current_data=None, accumulated_data=None):
        """只解释支持的条件类型，不执行动态代码；缺失数据按不满足处理。"""
        if not condition:
            return True
        data = {**(accumulated_data or {}), **(current_data or {})}
        kind = condition.get("type")
        if kind == "always":
            return True
        if kind == "never":
            return False
        if kind == "form_completed":
            return bool(data.get("__form_completed__")) and all(
                resolve_context_value(field, data) not in (None, "", [], {})
                for field in condition.get("required_fields", [])
            )
        if kind == "expression" and condition.get("expression"):
            return self._evaluate_expression(condition["expression"], data)
        field, operator = condition.get("field"), condition.get("operator")
        operator = {
            "equals": "==", "not_equals": "!=", "greater_than": ">", "less_than": "<",
            "not_contains": "not_contains", "greater_than_or_equal": ">=", "less_than_or_equal": "<=",
        }.get(operator, operator)
        actual = resolve_context_value(field, data, MISSING) if field else MISSING
        expected = condition.get("value")
        if operator == "exists":
            return actual is not MISSING
        if operator == "not_exists":
            return actual is MISSING
        if actual is MISSING:
            return False
        if operator == "is_empty":
            return actual in (None, "", [], {})
        if operator == "is_not_empty":
            return actual not in (None, "", [], {})
        try:
            if operator in {"in", "not_in"}:
                return (actual in expected) if operator == "in" else (actual not in expected)
            if operator in {"contains", "not_contains"}:
                found = expected in actual if isinstance(actual, (str, list, tuple, dict)) else False
                return found if operator == "contains" else not found
            return self._compare_values(actual, operator, expected)
        except (TypeError, ValueError):
            return False

    def _safe_numeric_compare(self, field, actual, operator, expected):
        try:
            if isinstance(actual, bool) or isinstance(expected, bool):
                return False
            left, right = float(actual), float(expected)
            if not math.isfinite(left) or not math.isfinite(right):
                return False
            return {">": lambda: left > right, "<": lambda: left < right,
                    ">=": lambda: left >= right, "<=": lambda: left <= right,
                    "==": lambda: left == right, "!=": lambda: left != right}[operator]()
        except (TypeError, ValueError, KeyError, OverflowError):
            return False

    def _evaluate_expression(self, expression, data):
        """只解析单字段比较，支持嵌套路径和数组下标，不使用 eval。"""
        match = re.fullmatch(r"\s*([\w.\[\]]+)\s*(==|!=|>=|<=|>|<)\s*(.+?)\s*", expression or "")
        if match is None:
            return False
        actual = resolve_context_value(match[1], data, MISSING)
        if actual is MISSING:
            return False
        return self._compare_values(actual, match[2], self._parse_expression_value(match[3]))

    def _parse_expression_value(self, value):
        value = value.strip()
        if value.lower() in {"null", "none"}:
            return None
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value

    def _compare_values(self, actual, operator, expected):
        if operator in {">", "<", ">=", "<="}:
            return self._safe_numeric_compare("", actual, operator, expected)
        if operator not in {"==", "!="}:
            return False
        if isinstance(expected, bool):
            if isinstance(actual, str) and actual.lower() in {"true", "false", "1", "0"}:
                actual = actual.lower() in {"true", "1"}
            equals = isinstance(actual, bool) and actual is expected
        elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
            return self._safe_numeric_compare("", actual, operator, expected)
        elif isinstance(expected, str):
            equals = isinstance(actual, str) and actual == expected
        else:
            equals = actual == expected
        return equals if operator == "==" else not equals


workflow_session_service = WorkflowSessionService()
