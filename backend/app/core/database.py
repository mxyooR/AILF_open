"""
数据库连接和会话管理
"""
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Generator
import logging

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

def create_database_engine(url):
    """按数据库类型配置引擎，让隔离测试复用生产环境的事务和会话代码。"""
    backend = make_url(url).get_backend_name()
    if backend == "sqlite":
        options = {"connect_args": {"check_same_thread": False}}
        if make_url(url).database in (None, "", ":memory:"):
            options["poolclass"] = StaticPool
        created = create_engine(url, pool_pre_ping=True, **options)

        @event.listens_for(created, "connect")
        def enable_foreign_keys(connection, _):
            # SQLite 默认不检查外键；启用后回归测试才能发现孤立元数据。
            connection.execute("PRAGMA foreign_keys=ON")
        return created
    options = dict(pool_pre_ping=True, pool_recycle=3600, pool_size=20, max_overflow=30, pool_timeout=30)
    if backend == "mysql":
        options["connect_args"] = {
            "charset": "utf8mb4", "autocommit": False, "connect_timeout": 10,
            "read_timeout": 30, "write_timeout": 30,
        }
    return create_engine(url, echo=False, **options)


engine = create_database_engine(settings.DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 仅显式业务事务复用会话。ContextVar 将并发请求隔离，普通服务仍使用独立会话。
_business_session = ContextVar("ailf_business_session", default=None)

# 创建基础模型类
Base = declarative_base()

# 元数据
metadata = Base.metadata


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    用于FastAPI依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_engine():
    """
    获取数据库引擎
    用于数据库初始化和管理
    """
    return engine


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话的上下文管理器
    用于服务层直接使用
    """
    shared = _business_session.get()
    if shared is not None:
        try:
            yield shared
        except Exception:
            # 即使下层把异常转成响应，上层也不能提交已经失败的事务。
            shared.info["business_rollback_only"] = True
            raise
        return
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def business_transaction() -> Generator[Session, None, None]:
    """支付、订单及后置动作共用一次提交；任何一步失败都回滚整笔业务。"""
    with get_db_session() as db:
        marker = _business_session.set(db)
        try:
            yield db
            if db.info.get("business_rollback_only"):
                raise RuntimeError("业务事务中存在失败操作")
        finally:
            _business_session.reset(marker)


def create_tables():
    """创建所有表"""
    import app.models  # 先注册所有模型，确保建表时能解析外键依赖。

    Base.metadata.create_all(bind=engine)


def ensure_entity_field_aliases_column():
    """兼容旧数据库，补齐实体字段的 aliases 列，供字段别名映射使用。"""
    from sqlalchemy import inspect, text
    with engine.begin() as conn:
        inspector = inspect(conn)
        if "entity_fields" not in inspector.get_table_names():
            return
        columns = [col.get("name") for col in inspector.get_columns("entity_fields")]
        if "aliases" in columns:
            return
        column_type = "TEXT" if conn.dialect.name == "sqlite" else "JSON"
        conn.execute(text(f"ALTER TABLE entity_fields ADD COLUMN aliases {column_type}"))


def drop_tables():
    """删除所有表"""
    Base.metadata.drop_all(bind=engine)


class DatabaseManager:
    """数据库连接管理器"""

    def __init__(self):
        self._engine = engine
        self._session_factory = SessionLocal

    def get_connection_info(self):
        """获取连接池信息"""
        pool = self._engine.pool
        try:
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "total_connections": pool.size() + pool.overflow()
            }
        except AttributeError:
            # 某些连接池类型可能没有所有方法
            return {
                "pool_size": getattr(pool, 'size', lambda: 0)(),
                "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
                "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
                "overflow": getattr(pool, 'overflow', lambda: 0)(),
                "total_connections": "unknown"
            }

    def health_check(self):
        """数据库健康检查"""
        try:
            with self._engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("SELECT 1 as health_check"))
                return {"status": "healthy", "result": result.scalar()}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def optimize_connection(self):
        """优化数据库连接"""
        try:
            # 清理无效连接
            self._engine.dispose()
            return {"status": "optimized", "message": "连接池已重新创建"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}


# 全局数据库管理器实例
db_manager = DatabaseManager()


def init_database():
    """初始化数据库"""
    try:
        # 测试数据库连接
        health = db_manager.health_check()
        if health["status"] != "healthy":
            raise Exception(f"数据库连接失败: {health.get('error')}")

        # 创建表
        create_tables()
        # 兼容老库：补齐新列
        ensure_entity_field_aliases_column()

        logger.info("✅ 数据库初始化成功")
        logger.debug(f"连接池状态: {db_manager.get_connection_info()}")
        return True
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        return False
