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
