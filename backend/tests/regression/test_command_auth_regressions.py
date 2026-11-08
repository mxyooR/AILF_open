"""AI 入口的身份只能来自认证依赖，不能信任浏览器提交的上下文。"""
import copy
import unittest
from unittest.mock import AsyncMock, patch

from _support import DatabaseTestCase, database
# 避免导入私有异步调度器时访问本机 Redis，所有认证数据均来自隔离会话。
with patch("app.core.logging_config.get_logger"), patch("redis.Redis.ping", side_effect=ConnectionError("offline fixture")):
    from app.api.v1 import ai
from app.models.role import RoleDBModel
from app.models.user import User
from app.schemas.ai import CommandRequest
from fastapi.security import HTTPAuthorizationCredentials


class CommandAuthenticationTests(DatabaseTestCase, unittest.IsolatedAsyncioTestCase):
    async def test_verified_bearer_reaches_api_context_without_mutating_request(self):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fixture-verified-token")
        info = {"user_id": 7, "permissions": [], "accessible_apis": []}
        with self.factory() as db, \
             patch.object(ai, "_verify_developer_token", AsyncMock(return_value=None)), \
             patch.object(ai, "_verify_user_token", AsyncMock(return_value=info)):
            current_user = await ai.get_current_user_optional(credentials, db)
            request = CommandRequest(command="测试", context={"user_token": "forged-token", "user_id": 99, "form_data": {"count": 0}})
            original = copy.deepcopy(request.context)
            context = await ai._build_enhanced_context(request, current_user, db)
        self.assertEqual(context["user_token"], credentials.credentials)
        self.assertEqual(context["user_id"], 7)
        self.assertEqual(context["form_data"], {"count": 0})
        self.assertEqual(request.context, original)

    async def test_guest_context_cannot_supply_another_users_token(self):
        request = CommandRequest(command="测试", context={"user_token": "forged-token", "user_id": 7})
        with self.factory() as db:
            context = await ai._build_enhanced_context(request, None, db)
        self.assertIsNone(context.get("user_token"))
        self.assertIsNone(context["user_id"])

    async def test_developer_uses_the_verified_bearer_too(self):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fixture-developer-token")
        with self.factory() as db, \
             patch.object(ai, "_verify_developer_token", AsyncMock(return_value={"user_id": "developer"})):
            user = await ai.get_current_user_optional(credentials, db)
            context = await ai._build_enhanced_context(CommandRequest(command="测试"), user, db)
        self.assertEqual(context["user_token"], credentials.credentials)

    async def test_disabled_user_and_locked_role_cannot_enter_ai(self):
        with database.get_db_session() as db:
            db.add(RoleDBModel(id="fixture_role", name="Fixture", code="fixture_role", status="active"))
            db.flush()
            db.add(User(id=7, username="fixture_user", password_hash="fixture-hash", role_id="fixture_role", is_active=False))
        with self.factory() as db, patch.object(ai, "verify_token", return_value={"user_type": "user", "user_id": 7}), \
             patch.object(ai, "_build_user_info", AsyncMock(return_value={"user_id": 7})):
            self.assertIsNone(await ai._verify_user_token("fixture-token", db))
            db.get(User, 7).is_active = True
            db.get(RoleDBModel, "fixture_role").status = "locked"
            db.flush()
            self.assertIsNone(await ai._verify_user_token("fixture-token", db))
            self.assertEqual(ai.permission_service.get_user_permissions(db.get(User, 7), db), [])
            self.assertEqual(ai.permission_service.get_user_accessible_apis(db.get(User, 7), db), [])

    async def test_model_cannot_invent_api_targets_or_change_trusted_endpoints(self):
        from app.services import ai_service as module
        from app.services.ai_service import AIServiceSimple
        service = AIServiceSimple()
        service._handle_api_intent_two_round = AsyncMock(return_value={"success": True})
        allowed = {"api_id": "fixture_api", "endpoint": "/fixture-safe", "method": "GET"}
        context = {"user_id": 7, "accessible_apis": [allowed]}
        with patch.object(module.workflow_service, "get_active_workflows_for_ai", return_value=[]):
            service._identify_intent_async = AsyncMock(return_value={"type": "API", "id": "forbidden_api"})
            result = await service.process_command("fixture", context)
            self.assertFalse(result["success"], result)
            service._handle_api_intent_two_round.assert_not_awaited()
            service._identify_intent_async = AsyncMock(return_value={"type": "API", "id": "fixture_api", "matched_resource": {"endpoint": "/invented-admin-path"}})
            result = await service.process_command("fixture", context)
            self.assertTrue(result["success"], result)
        self.assertEqual(service._handle_api_intent_two_round.await_args.args[0]["matched_resource"], allowed)

    async def test_workflow_candidates_respect_the_users_api_permissions(self):
        from app.services.ai_service import AIServiceSimple
        from _support import workflow
        flow = workflow()
        self.assertEqual(AIServiceSimple._accessible_workflows([flow], [], []), [])
        self.assertEqual(AIServiceSimple._accessible_workflows([flow], [{"api_id": "regression_api"}], []), [flow])
