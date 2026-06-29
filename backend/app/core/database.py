"""
数据库连接和会话管理
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# 配置日志 - 设置为INFO级别以显示推理日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)  # 只显示警告和错误

# 创建数据库引擎 - 优化连接池配置
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,  # 关闭SQL语句显示
    pool_pre_ping=True,   # 连接池预检查
    pool_recycle=3600,    # 连接回收时间（1小时）
    pool_size=20,         # 连接池大小
    max_overflow=30,      # 最大溢出连接数
    pool_timeout=30,      # 获取连接超时时间
    connect_args={
        "charset": "utf8mb4",
        "autocommit": False,
        "connect_timeout": 10,
        "read_timeout": 30,
        "write_timeout": 30,
    }
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 元数据
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    用于FastAPI依赖注入
    """
    db = SessionLocal()
    try:
        yield db
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
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """创建所有表"""
    # 导入所有模型以确保它们被注册
    # 注意：EntityRecordDBModel已废弃，实体数据现在存储在独立的entity_{name}表中
    from app.models.scenario import ScenarioDBModel
    from app.models.entity import EntityDBModel, EntityFieldDBModel, EntityRelationshipDBModel
    from app.models.workflow import WorkflowDBModel

    Base.metadata.create_all(bind=engine)


def ensure_entity_field_aliases_column():
    """Ensure entity_fields.aliases column exists (for field alias mapping)."""
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
            self._engine.pool.recreate()
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
