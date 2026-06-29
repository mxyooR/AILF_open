"""
Celery Worker 独立配置。
不依赖 backend/app/config.py，便于单独打包部署到算力机。
"""
import os
from pathlib import Path
from dotenv import load_dotenv


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class WorkerSettings:
    def __init__(self) -> None:
        self.WORKER_DIR = Path(__file__).resolve().parent
        self.PROJECT_ROOT = self.WORKER_DIR.parent

        # 优先级：命令行环境变量 > worker/.env > 项目根/.env > backend/.env
        for dotenv_file in (
            self.WORKER_DIR / ".env",
            self.PROJECT_ROOT / ".env",
            self.PROJECT_ROOT / "backend" / ".env",
        ):
            if dotenv_file.exists():
                load_dotenv(dotenv_path=dotenv_file, override=False)

        # Celery
        self.CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
        self.CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", self.CELERY_BROKER_URL)
        self.CELERY_RESULT_EXPIRES = int(os.getenv("CELERY_RESULT_EXPIRES", "3600"))
        self.CELERY_AI_QUEUE = os.getenv("CELERY_AI_QUEUE", "ai_inference")
        self.CELERY_TASK_ACKS_LATE = _to_bool(os.getenv("CELERY_TASK_ACKS_LATE"), True)
        self.CELERY_TASK_REJECT_ON_WORKER_LOST = _to_bool(os.getenv("CELERY_TASK_REJECT_ON_WORKER_LOST"), True)
        self.CELERY_WORKER_PREFETCH_MULTIPLIER = int(os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "1"))
        self.CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "180"))
        self.CELERY_TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT", "240"))
        self.CELERY_BROKER_VISIBILITY_TIMEOUT = int(os.getenv("CELERY_BROKER_VISIBILITY_TIMEOUT", "3600"))
        self.CELERY_INFERENCE_METRICS_ENABLED = _to_bool(os.getenv("CELERY_INFERENCE_METRICS_ENABLED"), True)
        self.CELERY_INFERENCE_METRICS_KEY = os.getenv("CELERY_INFERENCE_METRICS_KEY", "ai:inference:metrics:full")
        self.CELERY_INFERENCE_METRICS_AGG_KEY = os.getenv("CELERY_INFERENCE_METRICS_AGG_KEY", "ai:inference:metrics:aggregate")
        self.CELERY_INFERENCE_METRICS_MAX_SAMPLES = int(os.getenv("CELERY_INFERENCE_METRICS_MAX_SAMPLES", "240"))

        # 模型推理
        self.MODEL_PRELOAD_ON_WORKER_START = _to_bool(os.getenv("MODEL_PRELOAD_ON_WORKER_START"), True)
        self.MODEL_LOAD_ON_CELERY_TASK = _to_bool(os.getenv("MODEL_LOAD_ON_CELERY_TASK"), True)
        self.LOCAL_MODEL_BASE_PATH = os.getenv(
            "LOCAL_MODEL_BASE_PATH",
            str(self.PROJECT_ROOT / "Qwen" / "Qwen3-4B"),
        )
        self.LOCAL_MODEL_LORA_PATH = os.getenv(
            "LOCAL_MODEL_LORA_PATH",
            str(self.PROJECT_ROOT / "Model" / "checkpoint_epoch_2"),
        )
        self.LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.9"))
        self.LLM_MAX_NEW_TOKENS = int(os.getenv("LLM_MAX_NEW_TOKENS", "4096"))

        # Embedding（图裁剪）
        self.EMBEDDING_MODEL_PATH = os.getenv(
            "EMBEDDING_MODEL_PATH",
            str(self.PROJECT_ROOT / "Model" / "bge-small-zh-v1.5"),
        )
        self.EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cuda:0")
        self.EMBEDDING_USE_API = _to_bool(os.getenv("EMBEDDING_USE_API"), False)
        self.EGO_GRAPH_TOP_K_API = int(os.getenv("EGO_GRAPH_TOP_K_API", "15"))
        self.EGO_GRAPH_TOP_K_WORKFLOW = int(os.getenv("EGO_GRAPH_TOP_K_WORKFLOW", "5"))
        self.EGO_GRAPH_TOP_K = int(os.getenv("EGO_GRAPH_TOP_K", "15"))
        self.EGO_GRAPH_HOP = int(os.getenv("EGO_GRAPH_HOP", "1"))


settings = WorkerSettings()
