"""回归测试只使用隔离数据库，不读取本地 .env、业务账号或模型权重。"""
import os
import logging
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

_TEST_ENV = {
    "JWT_SECRET_KEY": "regression-jwt-" + "x" * 40,
    "DEVELOPER_PASSWORD": "regression-developer-" + "x" * 16,
    "DB_PASSWORD": "regression-database-" + "x" * 16,
    "ENABLE_FILE_LOGGING": "false",
    "ENABLE_CONSOLE_LOGGING": "false",
    "ENABLE_ACCESS_LOG": "false",
    "SEED_DEMO_USERS": "false",
}
_logger = logging.getLogger("backend-regression")
_logger.disabled = True
with patch.dict(os.environ, _TEST_ENV), patch("dotenv.load_dotenv"), patch("app.core.logging_config.get_logger", return_value=_logger):
    from app.core import database
    import app.models
    from app.services.workflow_service import WorkflowService
    from app.services.entity_service import EntityService
    from app.services.api_executor_service import APIExecutorService
    with patch("redis.Redis.ping", side_effect=ConnectionError("offline fixture")):
        from app.services.workflow_session_service import WorkflowSessionService
    from app.services.workflow_execution_service import WorkflowExecutionService
    from app.core.dynamic_router import DynamicRouteHandler
    from app.services.ai_service import AIServiceSimple
    from app.core import role_db_init, permission_control_db_init, user_db_init

from sqlalchemy import MetaData
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker


class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        # MySQL 仅供 CI 的临时测试库使用，业务 DATABASE_URL 不会进入测试。
        test_url = os.environ.get("AILF_REGRESSION_DATABASE_URL", "sqlite://")
        parsed = make_url(test_url)
        if parsed.get_backend_name() != "sqlite":
            if parsed.get_backend_name() != "mysql" or not (parsed.database or "").startswith("ailf_regression_"):
                raise RuntimeError("回归测试只允许 SQLite 或 ailf_regression_ 前缀的 MySQL 测试库")
            if parsed.host not in {"localhost", "127.0.0.1"}:
                raise RuntimeError("MySQL 回归测试只允许本机临时服务")
        self.engine = database.create_database_engine(test_url)
        if parsed.get_backend_name() == "mysql":
            # 每个用例重建专用测试库中的表，避免前一个用例的 DDL 和记录影响结果。
            fixture_metadata = MetaData()
            fixture_metadata.reflect(self.engine)
            fixture_metadata.drop_all(self.engine)
        database.Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine, autoflush=False)
        for item in (
            patch.object(database, "engine", self.engine),
            patch.object(database, "SessionLocal", self.factory),
            patch.object(database.db_manager, "_engine", self.engine),
            patch.object(database.db_manager, "_session_factory", self.factory),
        ):
            item.start()
            self.addCleanup(item.stop)
        self.addCleanup(self.engine.dispose)
        self.workflows = WorkflowService()
        self.workflows._session_service = session_service()
        self.entities = EntityService()


def session_service():
    with patch.object(WorkflowSessionService, "_init_redis"):
        return WorkflowSessionService()


def node(node_id, node_type, children=(), **extra):
    return {
        "id": node_id, "name": node_id, "type": node_type,
        "child_nodes": [
            {"node_id": child, "condition": {"type": "always", "description": ""}}
            for child in children
        ],
        "parent_nodes": [], **extra,
    }


def workflow():
    return {
        "id": "regression_flow", "name": "regression_flow", "status": "ACTIVE",
        "business_scenario": "regression", "user_intents": [], "trigger_keywords": [],
        "nodes": [
            node("entry_1", "start", ["edit_1"]),
            node("edit_1", "api_call", ["finish_1"], config={
                "api_id": "regression_api", "api_endpoint": "/regression",
                "method": "POST", "ui_mode": "form", "parameters": {"name": "${name}"},
            }),
            node("finish_1", "end"),
        ],
    }
