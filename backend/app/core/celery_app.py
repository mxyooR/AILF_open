"""
Celery 应用配置
"""
from celery import Celery

from app.config import settings


celery_app = Celery(
    "ailf-backend-client",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
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
)
