"""
AILF Backend Configuration
配置管理模块
"""
import os
from pathlib import Path
from urllib.parse import quote
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量文件
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / "backend" / ".env", override=False)
load_dotenv(PROJECT_ROOT / ".env", override=False)


def _parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _require_secret(name: str, minimum_length: int) -> str:
    configured = os.getenv(name, "")
    placeholder = configured.strip().lower().startswith(("your-", "change-me", "replace-me"))
    if len(configured.strip()) < minimum_length or placeholder:
        raise ValueError(
            f"{name} must be configured with at least {minimum_length} characters. "
            "Run python scripts/setup_env.py from the project root."
        )
    return configured


class Settings:
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "AILF Backend"
    VERSION: str = "2.0.0"
    DEBUG: bool = _parse_bool(os.getenv("DEBUG"), default=False)
    
    # 服务器配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5000"))
    
    # JWT配置
    JWT_SECRET_KEY: str = _require_secret("JWT_SECRET_KEY", 32)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = int(os.getenv("JWT_EXPIRE_HOURS", "24"))  # 保留历史字段，兼容旧逻辑
    JWT_CLOCK_SKEW_SECONDS: int = int(os.getenv("JWT_CLOCK_SKEW_SECONDS", "30"))
    DEVELOPER_ACCESS_TOKEN_EXPIRE_SECONDS: int = int(os.getenv("DEVELOPER_ACCESS_TOKEN_EXPIRE_SECONDS", "3600"))
    DEVELOPER_REFRESH_TOKEN_EXPIRE_SECONDS: int = int(os.getenv("DEVELOPER_REFRESH_TOKEN_EXPIRE_SECONDS", "604800"))
    USER_ACCESS_TOKEN_EXPIRE_SECONDS: int = int(os.getenv("USER_ACCESS_TOKEN_EXPIRE_SECONDS", "3600"))
    USER_REFRESH_TOKEN_EXPIRE_SECONDS: int = int(os.getenv("USER_REFRESH_TOKEN_EXPIRE_SECONDS", "604800"))
    MAX_ACTIVE_DEVELOPER_SESSIONS: int = int(os.getenv("MAX_ACTIVE_DEVELOPER_SESSIONS", "2"))
    MAX_ACTIVE_USER_SESSIONS: int = int(os.getenv("MAX_ACTIVE_USER_SESSIONS", "3"))
    AUTH_SESSION_REDIS_DB: int = int(os.getenv("AUTH_SESSION_REDIS_DB", "2"))
    AUTH_TOKEN_PREFIX: str = os.getenv("AUTH_TOKEN_PREFIX", "auth")
    AUTH_ALLOW_LEGACY_TOKENS: bool = _parse_bool(os.getenv("AUTH_ALLOW_LEGACY_TOKENS"), default=True)
    
    # 开发者认证配置
    DEVELOPER_PASSWORD: str = _require_secret("DEVELOPER_PASSWORD", 12)
    SEED_DEMO_USERS: bool = _parse_bool(os.getenv("SEED_DEMO_USERS"), default=False)
    DEMO_USER_PASSWORD: str = _require_secret("DEMO_USER_PASSWORD", 12) if SEED_DEMO_USERS else ""
    SECURITY_AUDIT_ENABLED: bool = _parse_bool(os.getenv("SECURITY_AUDIT_ENABLED"), default=True)

    # 应用界面配置
    APP_TITLE: str = os.getenv("APP_TITLE", "AILF")
    APP_SUBTITLE: str = os.getenv("APP_SUBTITLE", "开发者配置面板")

    # 用户注册配置
    DEFAULT_REGISTER_ROLE_CODE: str = os.getenv("DEFAULT_REGISTER_ROLE_CODE", "regular_user")  # 默认注册角色代码
    ALLOW_PUBLIC_REGISTRATION: bool = os.getenv("ALLOW_PUBLIC_REGISTRATION", "true").lower() == "true"  # 是否允许公开注册

    # 配置完成状态控制
    CONFIGURATION_COMPLETED: bool = os.getenv("CONFIGURATION_COMPLETED", "false").lower() == "true"  # 是否跳过配置检查

    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")  # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_DIR: str = os.getenv("LOG_DIR", "")  # 日志目录，默认为 backend/logs
    ENABLE_FILE_LOGGING: bool = os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"  # 是否启用文件日志
    ENABLE_CONSOLE_LOGGING: bool = os.getenv("ENABLE_CONSOLE_LOGGING", "true").lower() == "true"  # 是否启用控制台日志
    ENABLE_ACCESS_LOG: bool = os.getenv("ENABLE_ACCESS_LOG", "true").lower() == "true"  # 是否启用 API 请求日志

    # 数据库配置
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "ailf")
    DB_PASSWORD: str = _require_secret("DB_PASSWORD", 12)
    DB_NAME: str = os.getenv("DB_NAME", "ailf_db")

    @property
    def DATABASE_URL(self) -> str:
        """数据库连接URL"""
        return (
            f"mysql+pymysql://{quote(self.DB_USER, safe='')}:{quote(self.DB_PASSWORD, safe='')}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{quote(self.DB_NAME, safe='')}?charset=utf8mb4"
        )

    # CORS配置
    CORS_ORIGINS: list = [
        "http://127.0.0.1:3001",
        "http://localhost:3001",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    # Redis 配置（工作流会话存储）
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    REDIS_SESSION_TTL: int = int(os.getenv("REDIS_SESSION_TTL", "86400"))  # 会话过期时间，默认24小时

    # Celery 配置（异步任务）
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
    CELERY_RESULT_EXPIRES: int = int(os.getenv("CELERY_RESULT_EXPIRES", "3600"))
    AI_COMMAND_MAX_CONCURRENT: int = int(os.getenv("AI_COMMAND_MAX_CONCURRENT", "2"))
    AI_COMMAND_MAX_PENDING: int = int(os.getenv("AI_COMMAND_MAX_PENDING", "64"))
    AI_COMMAND_TIMEOUT_SECONDS: int = int(os.getenv("AI_COMMAND_TIMEOUT_SECONDS", "540"))
    AI_COMMAND_CACHE_SIZE: int = int(os.getenv("AI_COMMAND_CACHE_SIZE", "1024"))
    REDIS_AI_TASK_TTL: int = int(os.getenv("REDIS_AI_TASK_TTL", "3600"))
    CELERY_AI_QUEUE: str = os.getenv("CELERY_AI_QUEUE", "ai_inference")
    CELERY_INFERENCE_METRICS_KEY: str = os.getenv("CELERY_INFERENCE_METRICS_KEY", "ai:inference:metrics:full")
    CELERY_INFERENCE_METRICS_AGG_KEY: str = os.getenv("CELERY_INFERENCE_METRICS_AGG_KEY", "ai:inference:metrics:aggregate")
    CELERY_INFERENCE_METRICS_SAMPLE_SIZE: int = int(os.getenv("CELERY_INFERENCE_METRICS_SAMPLE_SIZE", "24"))

    # 图裁剪配置（V9 扩大召回范围）
    # API 召回: 12-20 个，Workflow 召回: 3-6 个
    EGO_GRAPH_TOP_K_API: int = int(os.getenv("EGO_GRAPH_TOP_K_API", "15"))  # API 召回数量
    EGO_GRAPH_TOP_K_WORKFLOW: int = int(os.getenv("EGO_GRAPH_TOP_K_WORKFLOW", "5"))  # Workflow 召回数量
    
    # ========== LLM 生成参数（统一配置）==========
    # 与 inference_constrained.py 蓝本完全一致
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    LLM_TOP_P: float = float(os.getenv("LLM_TOP_P", "0.9"))
    LLM_MAX_NEW_TOKENS: int = int(os.getenv("LLM_MAX_NEW_TOKENS", "4096"))


# 全局配置实例
settings = Settings()
