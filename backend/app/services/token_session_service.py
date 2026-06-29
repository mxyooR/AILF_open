"""
Token 会话与吊销服务
- 支持 Redis 存储（优先）
- Redis 不可用时自动降级为进程内内存存储
"""
from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional
import time
import uuid

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TokenSessionService:
    def __init__(self) -> None:
        self._redis_client = None
        self._redis_lock = Lock()

        self._memory_lock = Lock()
        self._memory_sessions: Dict[str, Dict[str, Any]] = {}
        self._memory_user_sessions: Dict[str, List[str]] = {}
        self._memory_revoked_jti_exp: Dict[str, float] = {}

    @staticmethod
    def _now_ts() -> float:
        return time.time()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).astimezone().isoformat()

    def _get_redis(self):
        with self._redis_lock:
            if self._redis_client is not None:
                return self._redis_client
            try:
                import redis  # type: ignore
                client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.AUTH_SESSION_REDIS_DB,
                    password=settings.REDIS_PASSWORD or None,
                    decode_responses=True,
                    socket_timeout=1.0,
                    socket_connect_timeout=1.0,
                )
                client.ping()
                self._redis_client = client
                return client
            except Exception as exc:
                logger.warning(f"TokenSessionService Redis 不可用，降级到内存模式: {exc}")
                self._redis_client = None
                return None

    def _session_key(self, sid: str) -> str:
        return f"{settings.AUTH_TOKEN_PREFIX}:session:{sid}"

    def _user_sessions_key(self, user_type: str, user_id: str) -> str:
        return f"{settings.AUTH_TOKEN_PREFIX}:sessions:{user_type}:{user_id}"

    def _revoked_jti_key(self, jti: str) -> str:
        return f"{settings.AUTH_TOKEN_PREFIX}:revoked:jti:{jti}"

    def _cleanup_memory_revoked(self) -> None:
        now = self._now_ts()
        expired = [jti for jti, exp_ts in self._memory_revoked_jti_exp.items() if exp_ts <= now]
        for jti in expired:
            self._memory_revoked_jti_exp.pop(jti, None)

    def create_session(
        self,
        user_type: str,
        user_id: str,
        max_sessions: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        sid = uuid.uuid4().hex
        now_ts = self._now_ts()
        now_iso = self._now_iso()
        max_sessions = max(1, int(max_sessions))
        ttl_seconds = max(
            int(settings.USER_REFRESH_TOKEN_EXPIRE_SECONDS),
            int(settings.DEVELOPER_REFRESH_TOKEN_EXPIRE_SECONDS),
        ) + 3600

        payload = {
            "sid": sid,
            "user_type": user_type,
            "user_id": str(user_id),
            "status": "active",
            "created_at": now_iso,
            "last_seen_at": now_iso,
            "metadata": metadata or {},
        }

        client = self._get_redis()
        if client is not None:
            user_key = self._user_sessions_key(user_type, str(user_id))
            session_key = self._session_key(sid)
            try:
                pipe = client.pipeline()
                pipe.hset(session_key, mapping={
                    "user_type": user_type,
                    "user_id": str(user_id),
                    "status": "active",
                    "created_at": now_iso,
                    "last_seen_at": now_iso,
                    "metadata": str(metadata or {}),
                })
                pipe.expire(session_key, ttl_seconds)
                pipe.zadd(user_key, {sid: now_ts})
                pipe.expire(user_key, ttl_seconds)
                pipe.execute()

                total = int(client.zcard(user_key) or 0)
                overflow = total - max_sessions
                if overflow > 0:
                    oldest = client.zrange(user_key, 0, overflow - 1) or []
                    for old_sid in oldest:
                        self.revoke_session(str(old_sid), reason="session_limit_exceeded")
                return sid
            except Exception as exc:
                logger.warning(f"Redis 创建 token 会话失败，使用内存模式: {exc}")
                self._redis_client = None

        with self._memory_lock:
            self._memory_sessions[sid] = payload
            user_key = f"{user_type}:{user_id}"
            session_list = self._memory_user_sessions.setdefault(user_key, [])
            session_list.append(sid)
            if len(session_list) > max_sessions:
                overflow = len(session_list) - max_sessions
                old_sessions = session_list[:overflow]
                self._memory_user_sessions[user_key] = session_list[overflow:]
                for old_sid in old_sessions:
                    sess = self._memory_sessions.get(old_sid)
                    if sess:
                        sess["status"] = "revoked"
                        sess["revoke_reason"] = "session_limit_exceeded"
                        sess["revoked_at"] = now_iso
        return sid

    def touch_session(self, sid: Optional[str]) -> None:
        if not sid:
            return
        now_iso = self._now_iso()
        now_ts = self._now_ts()

        client = self._get_redis()
        if client is not None:
            session_key = self._session_key(sid)
            try:
                session_data = client.hgetall(session_key) or {}
                if session_data:
                    user_key = self._user_sessions_key(
                        session_data.get("user_type", "unknown"),
                        session_data.get("user_id", "unknown")
                    )
                    pipe = client.pipeline()
                    pipe.hset(session_key, mapping={"last_seen_at": now_iso})
                    pipe.zadd(user_key, {sid: now_ts})
                    pipe.execute()
                return
            except Exception:
                self._redis_client = None

        with self._memory_lock:
            session = self._memory_sessions.get(sid)
            if session:
                session["last_seen_at"] = now_iso

    def is_session_active(self, sid: Optional[str], user_type: str, user_id: str) -> bool:
        if not sid:
            return False

        client = self._get_redis()
        if client is not None:
            session_key = self._session_key(sid)
            try:
                session_data = client.hgetall(session_key) or {}
                if not session_data:
                    return False
                return (
                    session_data.get("status") == "active"
                    and session_data.get("user_type") == user_type
                    and session_data.get("user_id") == str(user_id)
                )
            except Exception:
                self._redis_client = None

        with self._memory_lock:
            session = self._memory_sessions.get(sid)
            if not session:
                return False
            return (
                session.get("status") == "active"
                and session.get("user_type") == user_type
                and str(session.get("user_id")) == str(user_id)
            )

    def revoke_session(self, sid: Optional[str], reason: str = "manual") -> None:
        if not sid:
            return
        now_iso = self._now_iso()

        client = self._get_redis()
        if client is not None:
            session_key = self._session_key(sid)
            try:
                session_data = client.hgetall(session_key) or {}
                if session_data:
                    user_key = self._user_sessions_key(
                        session_data.get("user_type", "unknown"),
                        session_data.get("user_id", "unknown")
                    )
                    pipe = client.pipeline()
                    pipe.hset(session_key, mapping={
                        "status": "revoked",
                        "revoke_reason": reason,
                        "revoked_at": now_iso,
                    })
                    pipe.zrem(user_key, sid)
                    pipe.execute()
                return
            except Exception:
                self._redis_client = None

        with self._memory_lock:
            session = self._memory_sessions.get(sid)
            if session:
                session["status"] = "revoked"
                session["revoke_reason"] = reason
                session["revoked_at"] = now_iso
                user_key = f"{session.get('user_type')}:{session.get('user_id')}"
                sessions = self._memory_user_sessions.get(user_key, [])
                self._memory_user_sessions[user_key] = [item for item in sessions if item != sid]

    def revoke_token_jti(self, jti: Optional[str], exp_ts: Optional[float], reason: str = "manual") -> None:
        if not jti:
            return
        now_ts = self._now_ts()
        ttl_seconds = int(max(60.0, (float(exp_ts or now_ts + 3600.0) - now_ts)))

        client = self._get_redis()
        if client is not None:
            try:
                client.setex(self._revoked_jti_key(jti), ttl_seconds, reason)
                return
            except Exception:
                self._redis_client = None

        with self._memory_lock:
            self._cleanup_memory_revoked()
            self._memory_revoked_jti_exp[jti] = now_ts + ttl_seconds

    def is_token_revoked(self, jti: Optional[str]) -> bool:
        if not jti:
            return False
        client = self._get_redis()
        if client is not None:
            try:
                return bool(client.exists(self._revoked_jti_key(jti)))
            except Exception:
                self._redis_client = None

        with self._memory_lock:
            self._cleanup_memory_revoked()
            exp_ts = self._memory_revoked_jti_exp.get(jti)
            if exp_ts is None:
                return False
            return exp_ts > self._now_ts()


token_session_service = TokenSessionService()

