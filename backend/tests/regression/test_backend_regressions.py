import copy
import unittest
from unittest.mock import AsyncMock, patch
from _support import (
    DatabaseTestCase, APIExecutorService, WorkflowExecutionService,
    session_service, node, workflow, database,
)
from app.schemas.workflow import WorkflowCreateRequest, WorkflowUpdateRequest, WorkflowNodeCreateRequest
from app.schemas.entity import EntityCreateRequest


class WorkflowPersistenceTests(DatabaseTestCase):
    def create(self, data=None):
        payload = copy.deepcopy(data or workflow())
        payload.pop("id", None)
        payload.pop("status", None)
        result = self.workflows.create_workflow(WorkflowCreateRequest(**payload))
        self.assertTrue(result["success"], result)
        return result["data"]["workflow"]["id"]

    def test_extra_node_settings_survive_save_and_reload(self):
        data = workflow()
        data["nodes"][1]["config"]["display_type"] = "cards"
        data["nodes"][1]["config"]["message"] = "Configured message"
        data["nodes"][1]["inputs"] = [{"name": "name", "required": True}]
        flow_id = self.create(data)
        saved = self.workflows.get_workflow_detail(flow_id)["data"]["workflow"]["nodes"][1]
        self.assertEqual(saved["config"].get("display_type"), "cards")
        self.assertEqual(saved["config"].get("message"), "Configured message")
        self.assertEqual(saved.get("inputs"), [{"name": "name", "required": True}])

    def test_node_management_keeps_edges_consistent(self):
        flow_id = self.create()
        result = self.workflows.get_workflow_nodes(flow_id)
        self.assertTrue(result["success"], result)
        added = self.workflows.add_workflow_node(
            flow_id, WorkflowNodeCreateRequest(**node("note_1", "notification"))
        )
        self.assertTrue(added["success"], added)
        removed = self.workflows.delete_workflow_node(flow_id, "edit_1")
        self.assertTrue(removed["success"], removed)
        saved = self.workflows.get_workflow_detail(flow_id)["data"]["workflow"]
        self.assertEqual(saved["nodes"][0]["child_nodes"], [])
        self.assertNotIn("edit_1", saved["node_relationships"]["finish_1"]["parents"])

    def test_activation_normalizes_status_and_legacy_rows_remain_visible(self):
        flow_id = self.create()
        result = self.workflows.update_workflow(flow_id, WorkflowUpdateRequest(status="active"))
        self.assertTrue(result["success"], result)
        with database.get_db_session() as db:
            from app.models.workflow import WorkflowDBModel
            self.assertEqual(db.get(WorkflowDBModel, flow_id).status, "ACTIVE")
            db.get(WorkflowDBModel, flow_id).status = "active"
        self.assertEqual(len(self.workflows.get_active_workflows_for_ai()), 1)

    def test_long_display_names_do_not_overflow_primary_key(self):
        data = workflow()
        data["name"] = "A" * 100
        flow_id = self.create(data)
        self.assertLessEqual(len(flow_id), 50)

    def test_active_graph_rejects_dangling_edges(self):
        flow_id = self.create()
        invalid = workflow()["nodes"]
        invalid[0]["child_nodes"][0]["node_id"] = "missing_node"
        result = self.workflows.update_workflow(
            flow_id, WorkflowUpdateRequest(nodes=invalid, status="active")
        )
        self.assertFalse(result["success"])
        saved = self.workflows.get_workflow_detail(flow_id)["data"]["workflow"]
        self.assertEqual(saved["nodes"][0]["child_nodes"][0]["node_id"], "edit_1")


class SessionAndTemplateTests(unittest.TestCase):
    def test_form_completed_requires_a_real_completed_step(self):
        service = session_service()
        flow = workflow()
        flow["nodes"][1]["child_nodes"][0]["condition"] = {
            "type": "form_completed", "required_fields": ["quantity", "enabled"]
        }
        service.create_session("regression_user", "regression_flow", flow)
        service.update_session_step("regression_user", "regression_flow", "edit_1", {"quantity": 0, "enabled": False})
        self.assertIsNone(service.get_next_step("regression_user", {"__form_completed__": True}))
        service.mark_step_completed("regression_user", "edit_1")
        self.assertEqual(service.get_next_step("regression_user"), "finish_1")

    def test_legacy_condition_groups_choose_the_false_branch(self):
        service = session_service()
        flow = workflow()
        flow["nodes"][1] = node("decision", "condition", ["finish_1", "rejected"], config={
            "conditions": [{"field": "enabled", "operator": "equals", "value": True}], "logic": "and"
        })
        flow["nodes"][0]["child_nodes"][0]["node_id"] = "decision"
        flow["nodes"].append(node("rejected", "end"))
        service.create_session("regression_user", "regression_flow", flow)
        service.update_session_step("regression_user", "regression_flow", "decision", {"enabled": False})
        self.assertEqual(service.get_next_step("regression_user"), "rejected")

    def test_session_starts_at_the_configured_start_node(self):
        service = session_service()
        session = service.create_session("regression_user", "regression_flow", workflow())
        self.assertEqual(session.current_step, "entry_1")
        self.assertEqual(service.get_next_step("regression_user"), "edit_1")

    def test_unknown_step_does_not_fall_back_to_an_arbitrary_node(self):
        service = session_service()
        service.create_session("regression_user", "regression_flow", workflow())
        self.assertFalse(service.update_session_step(
            "regression_user", "regression_flow", "missing_node", {}
        ))

    def test_nested_expressions_and_quoted_values(self):
        service = session_service()
        self.assertTrue(service._evaluate_expression(
            "lookup_result.items[0].count >= 2", {"lookup_result": {"items": [{"count": 2}]}}
        ))
        self.assertTrue(service._evaluate_expression('label == "true"', {"label": "true"}))
        self.assertFalse(service._evaluate_expression('label == "true"', {"label": True}))

    def test_templates_preserve_json_types(self):
        executor = APIExecutorService()
        values = {"enabled": False, "quantity": 0, "rows": [1, 2], "lookup_result": {"item": {"id": 7}}}
        actual = executor._resolve_template_variables({
            "enabled": "${enabled}", "quantity": "${quantity}", "rows": "${rows}",
            "id": "${lookup_result.item.id}", "label": "items: ${rows}",
        }, values)
        self.assertIs(actual["enabled"], False)
        self.assertEqual(actual["quantity"], 0)
        self.assertEqual(actual["rows"], [1, 2])
        self.assertEqual(actual["id"], 7)
        self.assertEqual(actual["label"], "items: [1, 2]")


class ExecutionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.executor = WorkflowExecutionService()
        self.executor._session_service = session_service()
        self.executor._api_executor = APIExecutorService()
        self.executor._api_executor._find_api_route = lambda **kwargs: {"parameters_config": []}
        self.executor._workflow_service = type("Definitions", (), {
            "get_workflow_detail": lambda _, flow_id: {"success": True, "data": {"workflow": workflow()}}
        })()
        self.executor._generate_step_schema = AsyncMock(return_value={"type": "page"})
        self.executor._execute_api_call_node = AsyncMock(return_value={
            "success": True, "data": {"code": 201, "data": {"id": "record"}}
        })

    async def test_custom_end_node_finishes_and_post_next_does_not_skip_write(self):
        service = self.executor.session_service
        service.create_session("regression_user", "regression_flow", workflow())
        service.update_session_step("regression_user", "regression_flow", "edit_1")
        result = await self.executor.execute_step(
            "regression_user", "regression_flow", "edit_1", {"name": "demo"}, {"action": "next"}
        )
        self.assertEqual(result.next_step, "edit_1")
        self.executor._execute_api_call_node.assert_not_awaited()
        result = await self.executor.execute_step(
            "regression_user", "regression_flow", "edit_1", {"name": "demo"}, {"action": "submit"}
        )
        self.assertTrue(result.workflow_completed, result)
        self.executor._execute_api_call_node.assert_awaited_once()

    async def test_stale_submissions_do_not_repeat_api_calls(self):
        data = workflow()
        data["nodes"].insert(2, node("confirm_1", "user_input", ["finish_1"], config={"form_schema": {"body": []}}))
        data["nodes"][1]["child_nodes"][0]["node_id"] = "confirm_1"
        service = self.executor.session_service
        service.create_session("regression_user", "regression_flow", data)
        service.update_session_step("regression_user", "regression_flow", "edit_1")
        first = await self.executor.execute_step(
            "regression_user", "regression_flow", "edit_1", {"name": "demo"}, {"action": "submit"}
        )
        self.assertTrue(first.success, first)
        stale = await self.executor.execute_step(
            "regression_user", "regression_flow", "edit_1", {"name": "demo"}, {"action": "submit"}
        )
        self.assertFalse(stale.success)
        self.executor._execute_api_call_node.assert_awaited_once()

    def test_business_errors_do_not_become_successful_outputs(self):
        session = self.executor.session_service.create_session("regression_user", "regression_flow", workflow())
        self.assertFalse(self.executor._merge_api_result_into_session(
            session, "edit_1", {"success": True, "data": {"code": 400, "message": "invalid", "data": None}}
        ))
        self.assertNotIn("edit_1_result", session.step_data)


class EntityPersistenceTests(DatabaseTestCase):
    def test_fast_field_creation_cannot_collide_with_timestamp_random_ids(self):
        import asyncio
        # CI 曾在同一毫秒内生成两个相同的四位随机后缀；固定旧随机源可稳定重现。
        with patch("app.core.utils.time.time", return_value=1_800_000_000), \
             patch("app.core.utils.random.randint", return_value=1234):
            result = asyncio.run(self.entities.create_entity(self.request()))
        self.assertTrue(result["success"], result)
        field_ids = [field.id for field in result["data"]["entity"].fields]
        self.assertEqual(len(field_ids), len(set(field_ids)))

    def request(self):
        return EntityCreateRequest(
            name="regression_entity", displayName="Regression entity", fields=[
                {"name": "name", "displayName": "Name", "type": "text", "required": True},
                {"name": "enabled", "displayName": "Enabled", "type": "boolean", "defaultValue": False},
                {"name": "quantity", "displayName": "Quantity", "type": "number", "defaultValue": 0},
                {"name": "tags", "displayName": "Tags", "type": "multiselect", "defaultValue": []},
                {"name": "seen_at", "displayName": "Seen at", "type": "datetime"},
            ]
        )

    def test_create_and_update_records_share_type_normalization(self):
        import asyncio
        result = asyncio.run(self.entities.create_entity(self.request()))
        self.assertTrue(result["success"], result)
        entity_id = result["data"]["entity"].id
        created = self.entities.create_entity_record(entity_id, {
            "name": "demo", "tags": ["alpha", "beta"], "seen_at": "2026-11-08T10:30:00+08:00"
        })
        self.assertTrue(created["success"], created)
        record = created["data"]["record"]
        self.assertFalse(record["enabled"])
        self.assertEqual(record["quantity"], 0)
        self.assertEqual(record["tags"], ["alpha", "beta"])
        updated = self.entities.update_entity_record(entity_id, record["id"], {
            "tags": ["gamma"], "seen_at": "2026-11-08T02:30:00Z"
        })
        self.assertTrue(updated["success"], updated)
        self.assertEqual(updated["data"]["record"]["tags"], ["gamma"])
        self.assertEqual(str(updated["data"]["record"]["seen_at"]), str(record["seen_at"]))

    def test_failed_physical_table_creation_rolls_back_metadata(self):
        import asyncio
        with patch.object(self.entities, "_create_entity_database_table", side_effect=RuntimeError("DDL failed")):
            result = asyncio.run(self.entities.create_entity(self.request()))
        self.assertFalse(result["success"])
        with database.get_db_session() as db:
            from app.models.entity import EntityDBModel
            self.assertEqual(db.query(EntityDBModel).count(), 0)


if __name__ == "__main__":
    unittest.main()
