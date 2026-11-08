"""Integration regressions without a running server, model, Redis or business database."""
import asyncio
import copy
from datetime import datetime, timedelta
import fnmatch
import json
import threading
import time
import unittest
from unittest.mock import AsyncMock, patch

from _support import DatabaseTestCase, database, node, session_service, workflow
from app.services.workflow_execution_service import WorkflowExecutionService
from app.services.workflow_graph import normalize_nodes
from app.services.workflow_session_service import WorkflowSession


class MemoryRedis:
    """Only the Redis operations used by workflow snapshots, with real TTL semantics."""
    def __init__(self):
        self.values = {}
        self.fail_reads = False
        self.fail_writes = False
        self.scans = 0

    def get(self, key):
        if self.fail_reads:
            raise ConnectionError("fixture read outage")
        item = self.values.get(key)
        if item is None:
            return None
        if item[0] <= time.time():
            self.values.pop(key, None)
            return None
        return item[1]

    def setex(self, key, ttl, value):
        if self.fail_writes:
            raise ConnectionError("fixture write outage")
        self.values[key] = (time.time() + ttl, value)

    def pipeline(self, transaction=True):
        owner = self

        class Pipeline:
            def __init__(self):
                self.commands = []

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def watch(self, *keys):
                pass

            def get(self, key):
                return owner.get(key)

            def multi(self):
                pass

            def setex(self, *args):
                self.commands.append(args)
                return self

            def execute(self):
                if owner.fail_writes:
                    raise ConnectionError("fixture write outage")
                for args in self.commands:
                    owner.setex(*args)
        return Pipeline()

    def scan_iter(self, match, count=100):
        self.scans += 1
        return [key for key in list(self.values) if fnmatch.fnmatch(key, match) and self.get(key)]


def redis_session_service(redis):
    service = session_service()
    service._redis_enabled = True
    service._redis = redis
    return service


class RedisSnapshotTests(unittest.TestCase):
    def test_dirty_snapshot_recovers_after_a_write_outage(self):
        redis = MemoryRedis()
        service = redis_session_service(redis)
        service.create_session("snapshot_user", "regression_flow", workflow())
        redis.fail_writes = True
        service.update_session_step("snapshot_user", "regression_flow", "edit_1", {"quantity": 5})
        redis.fail_writes = False
        restored = service.get_active_session("snapshot_user")
        self.assertEqual(restored.step_data["quantity"], 5)
        remote = WorkflowSession.from_dict(json.loads(redis.get(service._session_key("snapshot_user"))))
        self.assertEqual(remote.step_data["quantity"], 5)

    def test_dirty_snapshot_never_overwrites_a_newer_remote_instance(self):
        redis = MemoryRedis()
        first, second = redis_session_service(redis), redis_session_service(redis)
        local = first.create_session("snapshot_user", "regression_flow", workflow())
        redis.fail_writes = True
        first.update_session_step("snapshot_user", "regression_flow", "edit_1", {"quantity": 1})
        redis.fail_writes = False
        replacement = second.create_session("snapshot_user", "regression_flow", workflow())
        second.update_session_step("snapshot_user", "regression_flow", "edit_1", {"quantity": 9})
        self.assertNotEqual(local.id, replacement.id)
        restored = first.get_active_session("snapshot_user")
        self.assertEqual(restored.id, replacement.id)
        self.assertEqual(restored.step_data["quantity"], 9)
        remote = WorkflowSession.from_dict(json.loads(redis.get(first._session_key("snapshot_user"))))
        self.assertEqual(remote.id, replacement.id)

    def test_dirty_snapshot_never_overwrites_a_newer_remote_step(self):
        redis = MemoryRedis()
        first, second = redis_session_service(redis), redis_session_service(redis)
        session = first.create_session("snapshot_user", "regression_flow", workflow())
        redis.fail_writes = True
        first.update_session_step("snapshot_user", "regression_flow", "edit_1", {"quantity": 1})
        redis.fail_writes = False
        second.update_session_step("snapshot_user", "regression_flow", "edit_1", {"quantity": 9})
        restored = first.get_instance(session.id)
        self.assertEqual(restored.step_data["quantity"], 9)

    def test_expired_dirty_memory_does_not_resurrect_a_session(self):
        redis = MemoryRedis()
        service = redis_session_service(redis)
        session = service.create_session("snapshot_user", "regression_flow", workflow())
        redis.fail_writes = True
        service.update_session_step("snapshot_user", "regression_flow", "edit_1", {"quantity": 1})
        session = service._memory["snapshot_user"]
        session.updated_at = datetime.now() - timedelta(seconds=service.ttl + 1)
        for key, (_, value) in list(redis.values.items()):
            redis.values[key] = (time.time() - 1, value)
        redis.fail_writes = False
        self.assertIsNone(service.get_active_session("snapshot_user"))
        self.assertIsNone(service.get_instance(session.id))
        self.assertEqual(service.list_sessions(), [])

    def test_local_capacity_expires_and_retains_active_sessions(self):
        from app.services.workflow_session_service import WorkflowSessionService
        with patch.object(WorkflowSessionService, "_init_redis"):
            service = WorkflowSessionService(capacity=1, ttl=10)
        session = service.create_session("first_user", "regression_flow", workflow())
        with self.assertRaises(RuntimeError):
            service.create_session("second_user", "regression_flow", workflow())
        service.end_session("first_user")
        service.create_session("second_user", "regression_flow", workflow())
        self.assertIsNone(service.get_instance(session.id))
        self.assertEqual(len(service.list_sessions()), 1)

    def test_remote_instance_lists_are_complete_even_with_a_small_cache(self):
        redis = MemoryRedis()
        service = redis_session_service(redis)
        service.capacity = 1
        first = service.create_session("first_user", "regression_flow", workflow())
        second = service.create_session("second_user", "regression_flow", workflow())
        self.assertEqual({item.id for item in service.list_sessions()}, {first.id, second.id})
        self.assertLessEqual(len(service._instances), 1)

    def test_list_prefers_the_remote_revision_when_timestamps_are_equal(self):
        redis = MemoryRedis()
        service = redis_session_service(redis)
        local = service.create_session("snapshot_user", "regression_flow", workflow())
        remote = copy.deepcopy(local)
        remote.revision += 1
        remote.step_data["quantity"] = 9
        payload = json.dumps(remote.to_dict())
        redis.setex(service._instance_key(local.id), service.ttl, payload)
        redis.setex(service._session_key(local.user_id), service.ttl, payload)
        listed = service.list_sessions()
        self.assertEqual(listed[0].step_data.get("quantity"), 9)


class ExtendedExecutionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.executor = WorkflowExecutionService()
        self.executor._session_service = session_service()
        self.executor._api_executor = type("API", (), {
            "_find_api_route": lambda _, **kwargs: {"parameters_config": []},
            "_resolve_template_variables": lambda _, values, data: values,
            "_substitute_path_params": lambda _, endpoint, data: endpoint,
        })()
        self.executor._generate_step_schema = AsyncMock(return_value={"type": "page", "body": []})
        self.executor._execute_api_call_node = AsyncMock(return_value={
            "success": True, "data": {"code": 201, "data": {"id": "created-record", "approved": True}}
        })

    def begin(self, data=None, step="edit_1"):
        service = self.executor.session_service
        session = service.create_session("execution_user", "regression_flow", data or workflow())
        service.update_session_step("execution_user", "regression_flow", step)
        return session

    async def test_concurrent_submissions_call_the_write_api_once(self):
        session = self.begin()
        results = await asyncio.gather(*[
            self.executor.execute_step(
                "execution_user", "regression_flow", "edit_1", {"name": "demo"},
                {"action": "submit", "instance_id": session.id}
            ) for _ in range(2)
        ])
        self.assertEqual(sum(result.success for result in results), 1)
        self.executor._execute_api_call_node.assert_awaited_once()

    async def test_instance_mismatch_is_rejected_before_any_mutation(self):
        old = self.begin()
        self.begin()
        result = await self.executor.execute_step(
            "execution_user", "regression_flow", "edit_1", {"name": "stale"},
            {"action": "submit", "instance_id": old.id}
        )
        self.assertFalse(result.success)
        self.assertNotIn("name", self.executor.session_service.get_active_session("execution_user").step_data)
        self.executor._execute_api_call_node.assert_not_awaited()

    async def test_automatic_condition_uses_api_output_and_custom_end(self):
        data = workflow()
        data["nodes"][1]["child_nodes"][0]["node_id"] = "decision"
        data["nodes"].extend([
            node("decision", "condition", ["finish_1", "rejected"], config={
                "evaluation_expression": "edit_1_result.approved == true"
            }),
            node("rejected", "end"),
        ])
        session = self.begin(data)
        result = await self.executor.execute_step(
            "execution_user", "regression_flow", "edit_1", {"name": "demo"},
            {"action": "submit", "instance_id": session.id}
        )
        self.assertTrue(result.workflow_completed, result)
        snapshot = self.executor.session_service.get_instance(session.id)
        self.assertEqual(snapshot.current_step, "finish_1")
        self.assertIn("decision", snapshot.completed_steps)

    async def test_api_failure_stays_on_the_failed_node(self):
        session = self.begin()
        self.executor._execute_api_call_node.return_value = {
            "success": True, "data": {"code": 409, "message": "Duplicate record", "data": None}
        }
        result = await self.executor.execute_step(
            "execution_user", "regression_flow", "edit_1", {"name": "demo"},
            {"action": "submit", "instance_id": session.id}
        )
        self.assertFalse(result.success)
        current = self.executor.session_service.get_active_session("execution_user")
        self.assertEqual(current.current_step, "edit_1")
        self.assertEqual(current.completed_steps, [])
        self.assertNotIn("edit_1_result", current.step_data)

    async def test_automatic_cycle_stops_without_repeating_side_effects(self):
        data = workflow()
        data["nodes"][1]["child_nodes"][0]["node_id"] = "loop"
        data["nodes"].append(node("loop", "condition", ["loop", "finish_1"]))
        session = self.begin(data)
        result = await self.executor.execute_step(
            "execution_user", "regression_flow", "edit_1", {"name": "demo"},
            {"action": "submit", "instance_id": session.id}
        )
        self.assertFalse(result.success)
        self.assertIn("循环", result.error)
        self.executor._execute_api_call_node.assert_awaited_once()

    async def test_generated_schema_accepts_string_and_null_api_data(self):
        session = self.begin()
        self.executor._generate_step_schema.return_value = {
            "type": "page", "body": [
                {"type": "form", "api": {"url": "/api/v1/workflow/state", "data": "${form_data}"}},
                {"type": "button", "api": {"url": "/api/v1/workflow/state", "data": None}},
                {"type": "form", "api": "post:/api/v1/workflow/state"},
            ]
        }
        result = await self.executor.execute_step(
            "execution_user", "regression_flow", "edit_1", {}, {"action": "next", "instance_id": session.id}
        )
        self.assertTrue(result.success, result.error)
        self.assertEqual(result.amis_schema["instance_id"], session.id)
        for component in result.amis_schema["body"]:
            self.assertEqual(component["api"]["data"]["instance_id"], session.id)

    async def test_notification_templates_and_deduplication_follow_the_instance(self):
        current = node("notice", "notification", ["finish_1"], config={
            "message": "订单 ${order.items[0].id}，数量 ${quantity}", "notification_type": "success"
        })
        sent = AsyncMock(return_value={"code": 200, "data": {"sent": True}})
        with patch("app.services.service_dispatcher.dispatch_service_call", sent):
            for instance_id in ("first-instance", "second-instance"):
                result = await self.executor._execute_notification_node(
                    current, "regression_flow", "notice", "execution_user",
                    {"order": {"items": [{"id": "fixture-order"}]}, "quantity": 0},
                    {"instance_id": instance_id}
                )
                self.assertTrue(result["success"], result)
        bodies = [call.kwargs["request_data"]["body"] for call in sent.await_args_list]
        self.assertEqual(bodies[0]["message"], "订单 fixture-order，数量 0")
        self.assertNotEqual(bodies[0]["idempotency_key"], bodies[1]["idempotency_key"])


class DynamicRecordTests(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        from app.core.dynamic_router import DynamicRouteHandler
        from fastapi import FastAPI
        from app.schemas.entity import EntityCreateRequest
        self.handler = DynamicRouteHandler(FastAPI())
        self.entity_name = "dynamic_regression"
        request = EntityCreateRequest(name=self.entity_name, displayName="Dynamic regression", fields=[
            {"name": "name", "displayName": "Name", "type": "text", "required": True, "unique": True},
            {"name": "enabled", "displayName": "Enabled", "type": "boolean", "defaultValue": False},
            {"name": "quantity", "displayName": "Quantity", "type": "number", "defaultValue": 0},
            {"name": "tags", "displayName": "Tags", "type": "multiselect", "defaultValue": []},
        ])
        result = asyncio.run(self.entities.create_entity(request))
        self.assertTrue(result["success"], result)
        self.entity_id = result["data"]["entity"].id

    def request(self, method, data=None, record_id=None, query=""):
        from starlette.requests import Request
        scope = {
            "type": "http", "method": method, "path": "/dynamic-regression" + ("/" + record_id if record_id else ""),
            "query_string": query.encode(), "headers": [],
            "path_params": {"id": record_id} if record_id else {},
        }
        request = Request(scope)
        request._json = data or {}
        return request

    def invoke(self, operation, request):
        from app.models.entity import EntityDBModel
        from types import SimpleNamespace
        with database.get_db_session() as db:
            entity = db.get(EntityDBModel, self.entity_id)
            fields = {field.name: field for field in entity.fields}
            fields["id"] = SimpleNamespace(name="id", type="text")
            fields["created_at"] = SimpleNamespace(name="created_at", type="datetime")
            fields["updated_at"] = SimpleNamespace(name="updated_at", type="datetime")
            args = [self.entity_name, entity, fields, request, db]
            if operation in ("create", "update"):
                args.append("regression_api")
            return asyncio.run(getattr(self.handler, "_handle_entity_" + operation)(*args))

    def test_dynamic_crud_round_trips_types_and_record_counts(self):
        created = self.invoke("create", self.request("POST", {"name": "demo"}))
        self.assertEqual(created["code"], 201, created)
        record_id = created["data"]["id"]
        self.assertIs(created["data"]["enabled"], False)
        self.assertEqual(created["data"]["tags"], [])
        updated = self.invoke("update", self.request("PUT", {"enabled": True, "tags": ["alpha"]}, record_id))
        self.assertEqual(updated["code"], 200, updated)
        fetched = self.invoke("get", self.request("GET", record_id=record_id))
        self.assertEqual(fetched["code"], 200, fetched)
        self.assertIs(fetched["data"]["enabled"], True)
        self.assertEqual(fetched["data"]["tags"], ["alpha"])
        listed = self.invoke("list", self.request("GET"))
        self.assertEqual(listed["code"], 200, listed)
        self.assertEqual(listed["data"]["total"], 1)
        self.assertIs(listed["data"]["items"][0]["enabled"], True)
        from app.models.entity import EntityDBModel
        with database.get_db_session() as db:
            self.assertEqual(db.get(EntityDBModel, self.entity_id).record_count, 1)
        deleted = self.invoke("delete", self.request("DELETE", record_id=record_id))
        self.assertEqual(deleted["code"], 200, deleted)
        with database.get_db_session() as db:
            self.assertEqual(db.get(EntityDBModel, self.entity_id).record_count, 0)
        self.assertEqual(self.invoke("get", self.request("GET", record_id=record_id))["code"], 404)

    def test_invalid_boolean_and_duplicate_values_do_not_create_records(self):
        first = self.invoke("create", self.request("POST", {"name": "demo"}))
        self.assertEqual(first["code"], 201, first)
        duplicate = self.invoke("create", self.request("POST", {"name": "demo"}))
        self.assertEqual(duplicate["code"], 400, duplicate)
        invalid = self.invoke("create", self.request("POST", {"name": "other", "enabled": "maybe"}))
        self.assertEqual(invalid["code"], 400, invalid)
        from sqlalchemy import text
        from app.models.entity import EntityDBModel
        with database.get_db_session() as db:
            self.assertEqual(db.execute(text("SELECT COUNT(*) FROM entity_dynamic_regression")).scalar(), 1)
            self.assertEqual(db.get(EntityDBModel, self.entity_id).record_count, 1)


class GraphCompatibilityTests(unittest.TestCase):
    def test_explicitly_clearing_edges_does_not_restore_legacy_edges(self):
        data = workflow()
        data["nodes"][0]["nextSteps"] = ["edit_1"]
        data["nodes"][0]["child_nodes"] = []
        saved = normalize_nodes(data["nodes"])
        self.assertEqual(saved[0]["child_nodes"], [])
        self.assertEqual(saved[1]["parent_nodes"], [])


if __name__ == "__main__":
    unittest.main()
