"""可选集成测试：只允许 CI 提供的临时 MySQL 库和专用 Redis 15 号库。"""
import asyncio
import copy
import json
import os
from urllib.parse import urlparse
import uuid
import unittest
from unittest.mock import patch

from _support import DatabaseTestCase, database, session_service, workflow
from app.schemas.entity import EntityCreateRequest, EntityUpdateRequest


@unittest.skipUnless(os.environ.get("AILF_REGRESSION_REDIS_URL"), "未配置隔离 Redis，默认离线验证")
class RedisIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        from redis import Redis
        url = os.environ["AILF_REGRESSION_REDIS_URL"]
        parsed = urlparse(url)
        if parsed.scheme != "redis" or parsed.hostname not in {"localhost", "127.0.0.1"} or parsed.path != "/15":
            raise RuntimeError("Redis 集成测试只允许本机临时服务的 15 号库")
        self.redis = Redis.from_url(url, decode_responses=True)
        self.redis.ping()
        self.user_id = "backend_regression_" + uuid.uuid4().hex
        self.ids = []

    def service(self):
        service = session_service()
        service._redis = self.redis
        service._redis_enabled = True
        return service

    def begin(self, service):
        session = service.create_session(self.user_id, "regression_flow", workflow())
        self.ids.append(session.id)
        return session

    def tearDown(self):
        # 只清理本用例生成的随机键，不使用 FLUSHDB，也不扫描删除其他数据。
        keys = ["wf:session:" + self.user_id, "wf:lock:" + self.user_id]
        keys.extend("wf:instance:" + instance_id for instance_id in self.ids)
        self.redis.delete(*keys)
        self.redis.close()

    async def test_redis_lock_excludes_a_second_worker(self):
        first, second = self.service(), self.service()
        async with first.execution_lock(self.user_id):
            with self.assertRaisesRegex(RuntimeError, "正在执行"):
                async with second.execution_lock(self.user_id):
                    self.fail("另一个进程不能进入同一会话的临界区")

    async def test_real_snapshots_expire_without_read_renewal(self):
        service = self.service()
        service.ttl = 1
        session = self.begin(service)
        self.assertGreater(self.redis.ttl("wf:instance:" + session.id), 0)
        service.get_active_session(self.user_id)
        await asyncio.sleep(1.2)
        self.assertIsNone(service.get_active_session(self.user_id))
        self.assertIsNone(service.get_instance(session.id))

    async def test_write_outage_recovery_keeps_the_new_remote_instance(self):
        first, second = self.service(), self.service()
        self.begin(first)
        with patch.object(self.redis, "pipeline", side_effect=ConnectionError("fixture outage")):
            first.update_session_step(self.user_id, "regression_flow", "edit_1", {"quantity": 1})
        replacement = self.begin(second)
        second.update_session_step(self.user_id, "regression_flow", "edit_1", {"quantity": 9})
        restored = first.get_active_session(self.user_id)
        self.assertEqual(restored.id, replacement.id)
        self.assertEqual(restored.step_data["quantity"], 9)

    async def test_watch_prevents_a_read_then_write_race(self):
        first, second = self.service(), self.service()
        session = self.begin(first)
        session.step_data["quantity"] = 1
        first._touch(session)
        original_pipeline = self.redis.pipeline
        injected = False

        def pipeline(*args, **kwargs):
            real = original_pipeline(*args, **kwargs)

            class Wrapper:
                def __enter__(self):
                    real.__enter__()
                    return self

                def __exit__(self, *values):
                    return real.__exit__(*values)

                def __getattr__(self, name):
                    return getattr(real, name)

                def execute(self):
                    nonlocal injected
                    if not injected:
                        injected = True
                        second.update_session_step(self_user, "regression_flow", "edit_1", {"quantity": 9})
                    return real.execute()
            return Wrapper()
        self_user = self.user_id
        with patch.object(self.redis, "pipeline", side_effect=pipeline):
            self.assertFalse(first._save_session(session))
        remote = json.loads(self.redis.get("wf:instance:" + session.id))
        self.assertEqual(remote["step_data"]["quantity"], 9)


@unittest.skipUnless(os.environ.get("AILF_REGRESSION_DATABASE_URL"), "未配置隔离 MySQL，默认离线验证")
class MySQLIntegrationTests(DatabaseTestCase):
    def test_ddl_defaults_precision_unique_indexes_and_retained_data(self):
        if self.engine.dialect.name != "mysql":
            self.skipTest("本用例验证 MySQL 8 DDL")
        fields = [
            {"name": "name", "displayName": "Name", "type": "text", "required": True, "unique": True},
            {"name": "amount", "displayName": "Amount", "type": "decimal", "validation": {"precision": 2}},
            {"name": "note", "displayName": "Note", "type": "text", "defaultValue": "100% O'Brian"},
            {"name": "enabled", "displayName": "Enabled", "type": "boolean", "defaultValue": False},
            {"name": "tags", "displayName": "Tags", "type": "multiselect", "defaultValue": []},
        ]
        created = asyncio.run(self.entities.create_entity(EntityCreateRequest(
            name="mysql_regression", displayName="MySQL regression", fields=fields
        )))
        self.assertTrue(created["success"], created)
        entity_id = created["data"]["entity"].id
        # 直接在隔离测试库中省略业务字段，验证真实服务端默认值，避免只测到 Python 默认值。
        from sqlalchemy import text
        with database.get_db_session() as db:
            db.execute(text("INSERT INTO entity_mysql_regression (name) VALUES ('server-default')"))
            row = db.execute(text("SELECT note, enabled, tags FROM entity_mysql_regression")).mappings().one()
            self.assertEqual(row["note"], "100% O'Brian")
            self.assertEqual(row["enabled"], 0)
            self.assertEqual(json.loads(row["tags"]) if isinstance(row["tags"], str) else row["tags"], [])
            db.execute(text("DELETE FROM entity_mysql_regression"))
        fields[0]["unique"] = False
        fields[1]["validation"]["precision"] = 4
        updated = asyncio.run(self.entities.update_entity(entity_id, EntityUpdateRequest(fields=fields)))
        self.assertTrue(updated["success"], updated)
        record = self.entities.create_entity_record(entity_id, {"name": "first", "amount": "1.2345"})
        self.assertTrue(record["success"], record)
        self.assertEqual(record["data"]["record"]["note"], "100% O'Brian")
        self.assertIs(record["data"]["record"]["enabled"], False)
        self.assertEqual(record["data"]["record"]["tags"], [])
        updated = asyncio.run(self.entities.update_entity(entity_id, EntityUpdateRequest(fields=fields[1:])))
        self.assertTrue(updated["success"], updated)
        second = self.entities.create_entity_record(entity_id, {"amount": "2.3456"})
        self.assertTrue(second["success"], second)
        with database.get_db_session() as db:
            names = db.execute(text("SELECT name FROM entity_mysql_regression")).scalars().all()
        self.assertIn("first", names)
        self.assertIn(None, names)
        fields[1]["validation"]["precision"] = 2
        rejected = asyncio.run(self.entities.update_entity(entity_id, EntityUpdateRequest(fields=fields[1:])))
        self.assertFalse(rejected["success"])
        fields[1]["validation"]["precision"] = 4
        # 重新加入之前保留的列，旧值应保留，新列约束也必须实际应用。
        fields[0]["required"] = False
        restored = asyncio.run(self.entities.update_entity(entity_id, EntityUpdateRequest(fields=fields)))
        self.assertTrue(restored["success"], restored)
        fields[0]["type"] = "number"
        rejected = asyncio.run(self.entities.update_entity(entity_id, EntityUpdateRequest(fields=fields)))
        self.assertFalse(rejected["success"])


if __name__ == "__main__":
    unittest.main()
