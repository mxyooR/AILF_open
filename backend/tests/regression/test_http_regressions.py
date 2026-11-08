"""HTTP 与 AI 入口回归：真实执行路由和事务，模型输出与登录令牌使用测试替身。"""
import asyncio
import copy
import importlib
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from _support import (
    DatabaseTestCase, database, node, session_service, workflow,
    WorkflowExecutionService, APIExecutorService, AIServiceSimple,
)
from app.schemas.workflow import WorkflowCreateRequest, WorkflowExecuteRequest
from app.services.ai_service import workflow_session_service as default_sessions
from app.services import ai_service as ai_module


class HTTPWorkflowTests(DatabaseTestCase, unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        super().setUp()
        from app.core import logging_config
        from app.core.auth.jwt_handler import jwt_handler
        from app.core import role_db_init, permission_control_db_init, user_db_init, dynamic_router
        # 只跳过启动时的真实初始化；请求使用 DatabaseTestCase 提供的隔离会话。
        with patch.object(logging_config, "init_logging"), patch.object(logging_config, "get_logger"), \
             patch.object(database, "init_database", return_value=True), \
             patch.object(role_db_init, "init_role_database", return_value=True), \
             patch.object(permission_control_db_init, "init_permission_control_database", return_value=True), \
             patch.object(user_db_init, "init_user_database", return_value=True), \
             patch.object(dynamic_router, "init_dynamic_router"):
            self.main = importlib.import_module("app.main")
            self.app = self.main.create_app()
        from app.api.v1 import workflow as workflow_module
        from app.services import workflow_execution_service as execution_module
        self.workflow_module = workflow_module
        self.app.dependency_overrides[workflow_module.verify_developer_token] = lambda: {"user_type": "developer"}
        self.executor = WorkflowExecutionService()
        self.executor._session_service = self.workflows.sessions
        self.executor._workflow_service = self.workflows
        self.executor._api_executor = APIExecutorService()
        self.executor._generate_step_schema = AsyncMock(return_value={
            "type": "page", "body": {
                "type": "form", "api": {"url": "/api/v1/workflow/state", "data": {"&": "$$", "action": "submit"}},
                "body": [{"type": "input-text", "name": "name"}],
            }
        })
        for item in (
            patch.object(workflow_module, "workflow_service", self.workflows),
            patch.object(execution_module, "workflow_execution_service", self.executor),
        ):
            item.start()
            self.addCleanup(item.stop)
        self.jwt_handler = jwt_handler
        self.dynamic = dynamic_router.DynamicRouteHandler(self.app)

    async def asyncSetUp(self):
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://fixture")
        self.executor._api_executor._http_client = self.client

    async def asyncTearDown(self):
        await self.client.aclose()

    def token(self, user_id="developer", user_type="developer"):
        return patch.object(self.jwt_handler, "verify_token", return_value={
            "valid": True, "user_type": user_type,
            "payload": {"user_id": user_id, "user_type": user_type},
        })

    async def create_active_workflow(self):
        data = workflow()
        data.pop("id")
        data.pop("status")
        response = await self.client.post("/api/v1/workflow", json=data)
        self.assertEqual(response.status_code, 201, response.text)
        flow_id = response.json()["data"]["workflow"]["id"]
        response = await self.client.put("/api/v1/workflow/" + flow_id, json={"status": "active"})
        self.assertEqual(response.status_code, 200, response.text)
        return flow_id

    async def test_validation_errors_from_custom_validators_return_422(self):
        response = await self.client.post("/api/v1/entities", json={
            "name": "invalid-name", "displayName": "Invalid", "fields": []
        })
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(response.json()["data"]["error"], "validation_error")
        self.assertIsInstance(response.json()["data"]["details"][0]["ctx"]["error"], str)

    async def test_static_workflow_routes_are_not_consumed_as_ids(self):
        await self.create_active_workflow()
        response = await self.client.get("/api/v1/workflow/for-amis")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()["data"]["options"]), 1)
        response = await self.client.get("/api/v1/workflow/instances")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["data"]["instances"], [])

    async def test_anonymous_and_invalid_tokens_cannot_create_workflow_sessions(self):
        body = {"workflow_id": "regression_flow", "node_id": "entry_1"}
        anonymous = await self.client.post("/api/v1/workflow/state", json=body)
        self.assertEqual(anonymous.status_code, 401)
        with patch.object(self.jwt_handler, "verify_token", return_value={"valid": False}):
            invalid = await self.client.post("/api/v1/workflow/state", json=body,
                                             headers={"Authorization": "Bearer fixture-token"})
        self.assertEqual(invalid.status_code, 401)
        self.assertEqual(self.workflows.sessions.list_sessions(), [])

    async def test_active_users_are_authenticated_with_the_actual_user_model(self):
        from app.models.role import RoleDBModel
        from app.models.user import User
        with database.get_db_session() as db:
            db.add(RoleDBModel(id="fixture_role", name="Fixture role", code="fixture_role"))
            db.flush()
            db.add(User(id=7, username="fixture_user", password_hash="fixture-hash", role_id="fixture_role", is_active=True))
        with self.token("7", "user"), patch("app.services.permission_service.permission_service.get_user_accessible_apis", return_value=[]):
            response = await self.client.post("/api/v1/workflow/state",
                json={"workflow_id": "missing", "node_id": "entry_1"},
                headers={"Authorization": "Bearer fixture-token"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], 1)
        with database.get_db_session() as db:
            db.get(User, 7).is_active = False
        with self.token("7", "user"):
            response = await self.client.post("/api/v1/workflow/state",
                json={"workflow_id": "missing", "node_id": "entry_1"},
                headers={"Authorization": "Bearer fixture-token"})
        self.assertEqual(response.status_code, 403, response.text)

    async def test_form_submission_executes_dynamic_api_and_persists_once(self):
        from app.schemas.entity import EntityCreateRequest
        from app.models.api_route import APIRouteDBModel, RouteStatus
        from app.models.entity import EntityDBModel
        from sqlalchemy import text
        created = await self.entities.create_entity(EntityCreateRequest(
            name="http_regression", displayName="HTTP regression", fields=[
                {"name": "name", "displayName": "Name", "type": "text", "required": True, "unique": True},
                {"name": "enabled", "displayName": "Enabled", "type": "boolean", "defaultValue": False},
            ]
        ))
        self.assertTrue(created["success"], created)
        entity_id = created["data"]["entity"].id
        with database.get_db_session() as db:
            db.add(APIRouteDBModel(
                id="http_route", api_id="regression_api", name="Fixture create",
                endpoint="/regression", method="POST", auth_required=False, status=RouteStatus.ACTIVE,
                handler_type="entity_crud", handler_config={"entity": "http_regression", "operation": "create"},
                parameters_config=[{"name": "name", "location": "body", "type": "string", "required": True}],
            ))
        self.dynamic._load_active_routes_from_database()
        flow_id = await self.create_active_workflow()
        headers = {"Authorization": "Bearer fixture-token"}
        with self.token():
            response = await self.client.post("/api/v1/workflow/" + flow_id + "/execute", json={"input_data": {}})
            self.assertEqual(response.status_code, 201, response.text)
            data = response.json()["data"]
            instance_id = data["instance"]["id"]
            self.assertEqual(data["amis_schema"]["body"]["api"]["data"]["instance_id"], instance_id)
            form = {"workflow_id": flow_id, "node_id": "edit_1", "action": "submit", "instance_id": instance_id, "name": "demo"}
            response = await self.client.post("/api/v1/workflow/state", json=form, headers=headers)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["status"], 0, response.text)
            repeated = await self.client.post("/api/v1/workflow/state", json=form, headers=headers)
            self.assertEqual(repeated.json()["status"], 1, repeated.text)
        with database.get_db_session() as db:
            row = db.execute(text("SELECT name, enabled FROM entity_http_regression")).one()
            self.assertEqual(tuple(row), ("demo", 0))
            self.assertEqual(db.get(EntityDBModel, entity_id).record_count, 1)
        instance = self.workflows.get_workflow_instance_detail(instance_id)["data"]["instance"]
        self.assertEqual(instance["status"], "completed")
        self.assertEqual(instance["progress"]["percentage"], 100)

    async def test_cancelled_instance_cannot_cancel_a_replacement(self):
        flow_id = await self.create_active_workflow()
        first = self.workflows.sessions.create_session("developer", flow_id, self.workflows.get_workflow_detail(flow_id)["data"]["workflow"])
        second = self.workflows.sessions.create_session("developer", flow_id, self.workflows.get_workflow_detail(flow_id)["data"]["workflow"])
        response = await self.client.post("/api/v1/workflow/instances/" + first.id + "/cancel")
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(self.workflows.sessions.get_active_session("developer").id, second.id)

    async def test_async_command_to_authenticated_api_form_branch_notification_and_database(self):
        """贯通真实路由、规则模板、事务和通知，只有模型推理及令牌校验使用替身。"""
        import inspect
        import json
        from app.api.v1 import ai as ai_api
        from app.services import async_command_service as command_module
        from app.services.ai_amis_service import ai_amis_service
        from app.schemas.entity import EntityCreateRequest
        from app.models.api_route import APIRouteDBModel, RouteStatus

        for name, fields in (
            ("command_record", [("name", "text")]),
            ("notification", [("notification_type", "text"), ("title", "text"), ("message", "text"),
                              ("status", "text"), ("user_id", "text"), ("idempotency_key", "text")]),
        ):
            created = await self.entities.create_entity(EntityCreateRequest(name=name, displayName=name,
                fields=[{"name": key, "displayName": key, "type": kind} for key, kind in fields]))
            self.assertTrue(created["success"], created)
        with database.get_db_session() as db:
            for method, api_id, operation in (("GET", "read_fixture", "list"), ("POST", "regression_api", "create")):
                db.add(APIRouteDBModel(id=api_id, api_id=api_id, name=api_id, endpoint="/command-records",
                    method=method, auth_required=True, status=RouteStatus.ACTIVE, handler_type="entity_crud",
                    handler_config={"entity": "command_record", "operation": operation},
                    parameters_config=[] if method == "GET" else [{"name": "name", "location": "body", "type": "string", "required": True}]))
        self.dynamic._load_active_routes_from_database()
        flow = workflow()
        flow["nodes"][0]["child_nodes"][0]["node_id"] = "lookup_1"
        flow["nodes"][1]["config"]["api_endpoint"] = "/command-records"
        flow["nodes"][1]["child_nodes"][0]["node_id"] = "decision"
        flow["nodes"].extend([
            node("lookup_1", "api_call", ["edit_1"], config={"api_id": "read_fixture", "api_endpoint": "/command-records", "method": "GET", "ui_mode": "auto"}),
            node("decision", "condition", ["notice", "rejected"], config={"evaluation_expression": "edit_1_result.name == 'demo'"}),
            node("notice", "notification", ["finish_1"], config={"notification_type": "success", "message": "Saved ${edit_1_result.name}"}),
            node("rejected", "end"),
        ])
        flow.pop("id")
        flow.pop("status")
        created = self.workflows.create_workflow(WorkflowCreateRequest(**flow))
        self.assertTrue(created["success"], created)
        flow_id = created["data"]["workflow"]["id"]
        from app.schemas.workflow import WorkflowUpdateRequest
        self.assertTrue(self.workflows.update_workflow(flow_id, WorkflowUpdateRequest(status="active"))["success"])
        service = AIServiceSimple()
        service.workflow_executor = self.executor
        service._identify_intent_async = AsyncMock(return_value={"type": "WORKFLOW", "id": flow_id})
        # 使用真实的规则模板生成中间表单，避免模型或 Celery 服务参与测试。
        self.executor._generate_step_schema = WorkflowExecutionService._generate_step_schema.__get__(self.executor)
        if inspect.iscoroutinefunction(ai_api.async_command_service.submit):
            from app.core.command_runtime import CommandRuntime, TaskStateStore
            commands = CommandRuntime(service.process_command, TaskStateStore(None, ttl=30), timeout=10)
            self.addAsyncCleanup(commands.shutdown)
        else:
            with patch.object(type(ai_api.async_command_service), "_init_redis"):
                commands = type(ai_api.async_command_service)()
        with self.token(), patch.object(ai_api, "async_command_service", commands), \
             patch.object(command_module, "ai_service_simple", service), \
             patch.object(ai_module, "workflow_service", self.workflows), \
             patch.object(ai_module, "workflow_session_service", self.workflows.sessions), \
             patch.object(ai_amis_service, "generate_schema", AsyncMock(return_value={"success": False})):
            headers = {"Authorization": "Bearer fixture-token"}
            submitted = await self.client.post("/api/v1/command/async", json={"command": "create a fixture record", "context": {"user_token": "forged-token"}}, headers=headers)
            self.assertEqual(submitted.status_code, 202, submitted.text)
            task = submitted.json()["data"]
            poll_headers = {**headers, "X-Task-Token": task.get("poll_token", "")}
            for _ in range(100):
                polled = await self.client.get("/api/v1/command/async/" + task["task_id"], headers=poll_headers)
                self.assertEqual(polled.status_code, 200, polled.text)
                result = polled.json()["data"]
                if result["status"] in {"SUCCESS", "FAILURE"}:
                    break
                await asyncio.sleep(0)
            self.assertEqual(result["status"], "SUCCESS", result)
            self.assertTrue(result["result"]["success"], result)
            session = self.workflows.sessions.get_active_session("developer")
            self.assertIn("lookup_1", session.completed_steps)
            schema = result["result"]["amis_schema"]
            self.assertEqual(schema["instance_id"], session.id)
            self.assertEqual(schema["current_node_id"], "edit_1")
            body = {"workflow_id": flow_id, "instance_id": session.id, "node_id": "edit_1", "action": "submit", "name": "demo"}
            completed = await self.client.post("/api/v1/workflow/state", json=body, headers=headers)
            self.assertEqual(completed.json()["status"], 0, completed.text)
            self.assertEqual(completed.json()["msg"], "工作流已完成")
            duplicate = await self.client.post("/api/v1/workflow/state", json=body, headers=headers)
            self.assertEqual(duplicate.json()["status"], 1, duplicate.text)
        from sqlalchemy import text
        with database.get_db_session() as db:
            self.assertEqual(db.execute(text("SELECT COUNT(*) FROM entity_command_record")).scalar(), 1)
            self.assertEqual(db.execute(text("SELECT COUNT(*) FROM entity_notification")).scalar(), 1)
        snapshot = self.workflows.sessions.get_instance(session.id)
        self.assertEqual(snapshot.current_step, "finish_1")
        self.assertEqual(snapshot.status, "completed")
        self.assertNotIn("fixture-token", json.dumps(snapshot.to_dict()))
        self.assertNotIn("forged-token", json.dumps(snapshot.to_dict()))

    def test_required_database_initialization_failures_stop_startup(self):
        with patch.object(self.main, "init_logging"), patch.object(self.main, "init_database", return_value=True), \
             patch.object(self.main, "init_role_database", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "角色管理数据库初始化失败"):
                self.main.create_app()


class AIEntryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.service = AIServiceSimple()
        self.sessions = session_service()
        self.executor = WorkflowExecutionService()
        self.executor._session_service = self.sessions
        self.service.workflow_executor = self.executor
        self.service._generate_slot_values_for_workflow = AsyncMock(return_value={})
        self.service.schema_generator = type("Generator", (), {
            "generate_workflow_entry_form": lambda _, **kwargs: {
                "type": "page", "body": {"type": "form", "api": {
                    "url": "/api/v1/workflow/state", "data": {"action": "submit", "&": "$$"}
                }}
            }
        })()
        for item in (patch.object(ai_module, "workflow_session_service", self.sessions),):
            item.start()
            self.addCleanup(item.stop)
        self.executor._should_auto_run_api_call = lambda node, data: False

    async def generate(self, flow):
        definitions = type("Definitions", (), {
            "get_workflow_detail": lambda _, flow_id: {"success": True, "data": {"workflow": flow}}
        })()
        with patch.object(ai_module, "workflow_service", definitions):
            return await self.service._handle_workflow_intent_two_round(
                "ai_fixture_user", {"id": "regression_flow"}, {"accessible_apis": []}, "fixture command"
            )

    async def test_ai_entry_follows_graph_edges_and_binds_the_first_form(self):
        flow = workflow()
        flow["nodes"][1]["child_nodes"][0]["node_id"] = "later_input"
        flow["nodes"].insert(0, node("later_input", "user_input", ["finish_1"]))
        result = await self.generate(flow)
        self.assertTrue(result["success"], result)
        schema = result["amis_schema"]
        session = self.sessions.get_active_session("ai_fixture_user")
        self.assertEqual(session.current_step, "edit_1")
        self.assertEqual(schema["body"]["api"]["data"]["node_id"], "edit_1")
        self.assertEqual(schema["body"]["api"]["data"]["instance_id"], session.id)

    async def test_invalid_new_definition_preserves_the_existing_session(self):
        old = self.sessions.create_session("ai_fixture_user", "regression_flow", workflow())
        flow = workflow()
        flow["nodes"][0]["child_nodes"][0]["node_id"] = "missing"
        result = await self.generate(flow)
        self.assertFalse(result["success"])
        self.assertEqual(self.sessions.get_active_session("ai_fixture_user").id, old.id)

    async def test_unmatched_start_conditions_preserve_the_existing_session(self):
        old = self.sessions.create_session("ai_fixture_user", "regression_flow", workflow())
        flow = workflow()
        flow["nodes"][0]["child_nodes"][0]["condition"] = {"type": "never"}
        result = await self.generate(flow)
        self.assertFalse(result["success"])
        self.assertEqual(self.sessions.get_active_session("ai_fixture_user").id, old.id)

    async def test_mismatched_entry_nodes_preserve_the_existing_session(self):
        old = self.sessions.create_session("ai_fixture_user", "regression_flow", workflow())
        with self.assertRaisesRegex(ValueError, "入口节点"):
            await self.service._check_and_create_workflow_session(
                "ai_fixture_user", "regression_flow", workflow(), first_node_id="finish_1"
            )
        self.assertEqual(self.sessions.get_active_session("ai_fixture_user").id, old.id)

    async def test_starting_again_invalidates_the_previous_entry_form(self):
        first = await self.generate(workflow())
        second = await self.generate(workflow())
        first_id = first["amis_schema"]["instance_id"]
        second_id = second["amis_schema"]["instance_id"]
        self.assertNotEqual(first_id, second_id)
        result = await self.executor.execute_step(
            "ai_fixture_user", "regression_flow", "edit_1", {"name": "stale"},
            {"action": "submit", "instance_id": first_id}
        )
        self.assertFalse(result.success)
        self.assertEqual(self.sessions.get_active_session("ai_fixture_user").step_data, {})

    def test_legacy_user_input_forms_are_interactive(self):
        from app.services.amis_schema_generator import AmisSchemaGenerator
        current = node("legacy_input", "user_input", inputs=[
            {"name": "quantity", "type": "number", "required": True, "label": "Quantity"}
        ])
        schema = AmisSchemaGenerator().generate_workflow_step_form(workflow(), current, slot_values={})
        self.assertEqual(schema["body"]["type"], "form")
        self.assertEqual(schema["body"]["body"][0]["type"], "input-number")
        self.assertEqual(schema["body"]["api"]["data"]["action"], "submit")
        self.assertEqual(schema["body"]["api"]["data"]["&"], "$$")


if __name__ == "__main__":
    unittest.main()
