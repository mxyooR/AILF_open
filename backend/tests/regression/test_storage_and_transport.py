"""API 参数传输和 MySQL DDL 规划回归；默认不连接 MySQL 或 Redis。"""
import asyncio
from decimal import Decimal
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

import httpx
from _support import DatabaseTestCase, database, APIExecutorService
from app.schemas.entity import EntityFieldCreateRequest, EntityCreateRequest, EntityUpdateRequest
from app.schemas.workflow import WorkflowNodeCreate


class APITransportTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.requests = []

        def handle(request):
            self.requests.append(request)
            if request.method in {"HEAD", "OPTIONS"}:
                return httpx.Response(204, headers={"Content-Type": "application/json"})
            return httpx.Response(200, json={"code": 200, "data": {"ok": True}})
        self.client = httpx.AsyncClient(transport=httpx.MockTransport(handle), base_url="http://fixture")
        self.executor = APIExecutorService()
        self.executor._http_client = self.client

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_path_query_body_and_headers_keep_their_declared_locations(self):
        self.executor._find_api_route = lambda **kwargs: {
            "endpoint": "/records/{record_id}", "method": "PATCH", "status": "active",
            "parameters_config": [
                {"name": "record_id", "location": "path"},
                {"name": "dry_run", "location": "query"},
                {"name": "X-Request-ID", "location": "header"},
                {"name": "enabled", "location": "body"},
                {"name": "quantity", "location": "body"},
                {"name": "tags", "location": "body"},
            ]
        }
        result = await self.executor.execute_api(
            {"api_id": "fixture_api", "parameters": {}},
            {"record_id": "value/with space", "dry_run": False, "X-Request-ID": "fixture-request",
             "enabled": False, "quantity": 0, "tags": [], "unrelated": "private-context"},
            user_token="fixture-token"
        )
        self.assertTrue(result["success"], result)
        request = self.requests[0]
        self.assertIn(b"value%2Fwith%20space", request.url.raw_path)
        self.assertEqual(request.url.params["dry_run"], "false")
        self.assertEqual(request.headers["X-Request-ID"], "fixture-request")
        self.assertEqual(request.headers["Authorization"], "Bearer fixture-token")
        import json
        self.assertEqual(json.loads(request.content), {"enabled": False, "quantity": 0, "tags": []})

    async def test_delete_can_send_declared_body_fields(self):
        self.executor._find_api_route = lambda **kwargs: {
            "endpoint": "/records/{record_id}", "method": "DELETE", "status": "active",
            "parameters_config": [
                {"name": "record_id", "location": "path"},
                {"name": "reason", "location": "body"},
                {"name": "dry_run", "location": "query"},
            ]
        }
        result = await self.executor.execute_api(
            {"api_id": "fixture_api", "parameters": {}},
            {"record_id": "record", "reason": "fixture", "dry_run": True}
        )
        self.assertTrue(result["success"], result)
        import json
        self.assertEqual(json.loads(self.requests[0].content), {"reason": "fixture"})
        self.assertEqual(self.requests[0].url.params["dry_run"], "true")

    async def test_empty_head_and_options_responses_are_successful(self):
        for method in ("HEAD", "OPTIONS"):
            self.executor._find_api_route = lambda **kwargs: {
                "endpoint": "/records", "method": method, "status": "active", "parameters_config": []
            }
            result = await self.executor.execute_api({"api_id": "fixture_api"}, {})
            self.assertTrue(result["success"], (method, result))

    async def test_absolute_urls_and_inactive_routes_do_not_send_requests(self):
        for route in [
            {"endpoint": "https://external.invalid/records", "method": "POST", "status": "active"},
            {"endpoint": "//external.invalid/records", "method": "POST", "status": "active"},
            {"endpoint": "/records", "method": "POST", "status": "inactive"},
        ]:
            self.executor._find_api_route = lambda **kwargs: route
            result = await self.executor.execute_api({"api_id": "fixture_api"}, {})
            self.assertFalse(result["success"])
        self.assertEqual(self.requests, [])


class DDLPlanningTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        from sqlalchemy.dialects.mysql import dialect
        from app.services.entity_service import EntityService
        self.service = EntityService()
        self.db = MagicMock()
        self.db.bind.dialect = dialect()
        self.db.execute.return_value.scalar.return_value = 0
        self.inspector = MagicMock()
        self.inspector.get_indexes.return_value = []
        self.inspector.get_unique_constraints.return_value = []
        self.definition = SimpleNamespace(fields=[])
        self.db.query.return_value.filter.return_value.first.return_value = self.definition

    async def plan(self, fields, old):
        self.definition.fields = old
        self.inspector.get_columns.return_value = [
            {"name": item.name, "nullable": not item.required} for item in old
        ]
        with patch.object(self.service, "_table_exists", return_value=True), \
             patch("app.services.entity_service.inspect", return_value=self.inspector):
            await self.service._alter_entity_database_table("fixture", fields, self.db)
        return [str(call.args[0]) for call in self.db.execute.call_args_list]

    def previous(self, kind="text", unique=False, required=False, precision=2):
        return SimpleNamespace(name="value", type=kind, unique_field=unique, required=required,
                               default_value=None, validation={"precision": precision}, options=None)

    async def test_repeated_unique_index_metadata_is_dropped_once(self):
        self.inspector.get_indexes.return_value = [{"name": "uq_fixture", "column_names": ["value"], "unique": True}]
        self.inspector.get_unique_constraints.return_value = [{"name": "uq_fixture", "column_names": ["value"]}]
        field = EntityFieldCreateRequest(name="value", displayName="Value", type="text", unique=False)
        statements = await self.plan([field], [self.previous(unique=True)])
        alter = next(value for value in statements if value.startswith("ALTER TABLE"))
        self.assertEqual(alter.count("DROP INDEX `uq_fixture`"), 1)

    async def test_decimal_precision_changes_the_physical_column(self):
        field = EntityFieldCreateRequest(name="value", displayName="Value", type="decimal", validation={"precision": 4})
        statements = await self.plan([field], [self.previous(kind="decimal")])
        self.assertTrue(any("MODIFY COLUMN" in sql and "NUMERIC(20, 4)" in sql for sql in statements), statements)

    async def test_removed_required_fields_keep_data_but_allow_new_records(self):
        statements = await self.plan([], [self.previous(required=True)])
        self.assertTrue(any("MODIFY COLUMN" in sql and "value" in sql for sql in statements), statements)
        self.assertFalse(any("DROP COLUMN" in sql for sql in statements))
        self.assertFalse(any("NOT NULL" in sql for sql in statements if sql.startswith("ALTER TABLE")))

    async def test_readding_a_retained_column_rejects_type_changes_with_data(self):
        from sqlalchemy import String
        self.db.execute.return_value.scalar.return_value = 1
        self.inspector.get_columns.return_value = [{"name": "value", "type": String(255), "nullable": True}]
        field = EntityFieldCreateRequest(name="value", displayName="Value", type="number")
        with patch.object(self.service, "_table_exists", return_value=True), \
             patch("app.services.entity_service.inspect", return_value=self.inspector):
            with self.assertRaisesRegex(ValueError, "已有数据"):
                await self.service._alter_entity_database_table("fixture", [field], self.db)
        self.assertFalse(any("ALTER TABLE" in str(call.args[0]) for call in self.db.execute.call_args_list))

    async def test_readding_a_retained_column_applies_its_new_definition(self):
        from sqlalchemy import String
        self.inspector.get_columns.return_value = [{"name": "value", "type": String(255), "nullable": True}]
        field = EntityFieldCreateRequest(name="value", displayName="Value", type="text", required=True, defaultValue="restored")
        with patch.object(self.service, "_table_exists", return_value=True), \
             patch("app.services.entity_service.inspect", return_value=self.inspector):
            await self.service._alter_entity_database_table("fixture", [field], self.db)
        alters = [str(call.args[0]) for call in self.db.execute.call_args_list if "ALTER TABLE" in str(call.args[0])]
        self.assertEqual(len(alters), 1)
        self.assertIn("MODIFY COLUMN", alters[0])
        self.assertIn("NOT NULL", alters[0])
        self.assertIn("restored", alters[0])

    def test_all_models_compile_for_mysql_without_untyped_columns(self):
        from sqlalchemy.dialects.mysql import dialect
        from sqlalchemy.schema import CreateTable
        for table in database.Base.metadata.sorted_tables:
            str(CreateTable(table).compile(dialect=dialect()))


class EntityEvolutionTests(DatabaseTestCase):
    def test_adding_a_required_field_without_a_default_does_not_modify_metadata(self):
        result = asyncio.run(self.entities.create_entity(EntityCreateRequest(
            name="evolution_regression", displayName="Evolution", fields=[
                {"name": "name", "displayName": "Name", "type": "text", "required": True},
            ]
        )))
        self.assertTrue(result["success"], result)
        entity_id = result["data"]["entity"].id
        created = self.entities.create_entity_record(entity_id, {"name": "demo"})
        self.assertTrue(created["success"], created)
        update = asyncio.run(self.entities.update_entity(entity_id, EntityUpdateRequest(fields=[
            {"name": "name", "displayName": "Name", "type": "text", "required": True},
            {"name": "required_new", "displayName": "New", "type": "text", "required": True},
        ])))
        self.assertFalse(update["success"])
        from app.models.entity import EntityDBModel
        with database.get_db_session() as db:
            self.assertEqual([field.name for field in db.get(EntityDBModel, entity_id).fields], ["name"])

    def test_field_ids_survive_edits_and_false_defaults_are_preserved(self):
        request = EntityCreateRequest(name="evolution_regression", displayName="Evolution", fields=[
            {"name": "enabled", "displayName": "Enabled", "type": "boolean", "defaultValue": False}
        ])
        result = asyncio.run(self.entities.create_entity(request))
        self.assertTrue(result["success"], result)
        entity_id = result["data"]["entity"].id
        field_id = result["data"]["entity"].fields[0].id
        update = asyncio.run(self.entities.update_entity(entity_id, EntityUpdateRequest(
            fields=[{"name": "enabled", "displayName": "Renamed", "type": "boolean", "defaultValue": False}]
        )))
        self.assertTrue(update["success"], update)
        self.assertEqual(update["data"]["entity"].fields[0].id, field_id)
        self.assertIs(update["data"]["entity"].fields[0].defaultValue, False)


class LegacyGraphSchemaTests(unittest.TestCase):
    def test_legacy_edges_are_imported_only_when_the_new_field_is_absent(self):
        legacy = WorkflowNodeCreate(id="start", name="Start", type="start", nextSteps=["business"])
        self.assertEqual([edge.node_id for edge in legacy.child_nodes], ["business"])
        cleared = WorkflowNodeCreate(id="start", name="Start", type="start", child_nodes=[], nextSteps=["business"])
        self.assertEqual(cleared.child_nodes, [])


if __name__ == "__main__":
    unittest.main()
