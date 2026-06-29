"""
Celery Worker 独立日志配置。
"""
from __future__ import annotations

import logging
import os


def _ensure_basic_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    level = os.getenv("CELERY_WORKER_LOGLEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    _ensure_basic_logging()
    return logging.getLogger(name)
