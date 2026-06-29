"""
Celery Worker 专用应用配置。
"""
from celery import Celery

from celery_worker.config import settings


celery_app = Celery(
    "ailf-worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["celery_worker.ai_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    enable_utc=False,
    timezone="Asia/Shanghai",
    task_track_started=True,
    result_expires=settings.CELERY_RESULT_EXPIRES,
    broker_connection_retry_on_startup=True,
    task_default_queue=settings.CELERY_AI_QUEUE,
    task_routes={
        "app.tasks.ai.invoke": {"queue": settings.CELERY_AI_QUEUE},
        "app.tasks.ai.ping": {"queue": settings.CELERY_AI_QUEUE},
    },
    task_acks_late=settings.CELERY_TASK_ACKS_LATE,
    task_reject_on_worker_lost=settings.CELERY_TASK_REJECT_ON_WORKER_LOST,
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    broker_transport_options={
        "visibility_timeout": settings.CELERY_BROKER_VISIBILITY_TIMEOUT
    },
)
