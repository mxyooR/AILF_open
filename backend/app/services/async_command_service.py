"""Wire the bounded command runtime to the AI orchestrator and async Redis client."""
from redis.asyncio import Redis

from app.config import settings
from app.core.command_runtime import CommandRuntime, TaskStateStore
from app.services.ai_service import ai_service_simple


def create_command_service() -> CommandRuntime:
    # Constructing the client performs no network I/O during module import.
    redis_client = Redis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD or None, decode_responses=True,
        socket_timeout=0.5, socket_connect_timeout=0.5,
    )
    store = TaskStateStore(redis_client, ttl=settings.REDIS_AI_TASK_TTL, max_entries=settings.AI_COMMAND_CACHE_SIZE)
    return CommandRuntime(
        ai_service_simple.process_command, store,
        max_concurrent=settings.AI_COMMAND_MAX_CONCURRENT,
        max_pending=settings.AI_COMMAND_MAX_PENDING,
        timeout=settings.AI_COMMAND_TIMEOUT_SECONDS,
    )


async_command_service = create_command_service()
