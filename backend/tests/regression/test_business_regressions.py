"""合成订单和通知验证业务状态、幂等与事务，不读取真实业务配置。"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from _support import DatabaseTestCase, database
from app.schemas.entity import EntityCreateRequest
from app.services import service_dispatcher as services


class BusinessFlowTests(DatabaseTestCase, unittest.IsolatedAsyncioTestCase):
    async def create_entity(self, name, fields):
        payload = [{"name": key, "displayName": key, "type": kind} for key, kind in fields]
        # 编号规则来自内置模板；使用相同约束，避免服务生成的编号在真实表单中落库失败。
        for field in payload:
            pattern = {"payment_id": r"^P\d{14}$", "ticket_number": r"^T\d{12}$", "refund_id": r"^R\d{14}$"}.get(field["name"])
            if pattern:
                field["validation"] = {"pattern": pattern}
        created = await self.entities.create_entity(EntityCreateRequest(name=name, displayName=name, fields=payload))
        self.assertTrue(created["success"], created)
        return created["data"]["entity"].id

    async def payment_fixture(self, status="待支付"):
        self.order_entity = await self.create_entity("order", [
            ("order_number", "text"), ("total_amount", "decimal"), ("order_status", "text"),
            ("payment_method", "text"), ("payment_time", "datetime"),
        ])
        self.payment_entity = await self.create_entity("payment", [
            ("payment_id", "text"), ("order_id", "text"), ("order_number", "text"),
            ("amount", "decimal"), ("status", "text"), ("payment_method", "text"), ("transaction_id", "text"),
            ("payment_time", "datetime"), ("expire_time", "datetime"), ("create_time", "datetime"), ("refund_amount", "decimal"),
        ])
        created = self.entities.create_entity_record(self.order_entity, {"order_number": "fixture-order", "total_amount": "100.00", "order_status": status})
        self.assertTrue(created["success"], created)
        self.order_id = created["data"]["record"]["id"]

    async def call(self, method, body, service="payment_service", **kwargs):
        return await services.dispatch_service_call(service, method, request_data={"body": body}, **kwargs)

    def records(self, entity):
        return self.entities.get_entity_records(entity)["data"]["records"]

    async def test_payment_rejects_underpayment_and_non_finite_or_negative_values(self):
        await self.payment_fixture()
        for amount in ("99.99", 0, -1, "NaN", "Infinity", True, "invalid"):
            with self.subTest(amount=amount):
                result = await self.call("create_payment", {"order_id": self.order_id, "amount": amount})
                self.assertEqual(result["code"], 400, result)
        self.assertEqual(self.records(self.payment_entity), [])
        self.assertEqual(self.records(self.order_entity)[0]["order_status"], "待支付")

    async def test_payment_retry_reuses_the_original_payment(self):
        await self.payment_fixture()
        first = await self.call("create_payment", {"order_id": self.order_id})
        second = await self.call("create_payment", {"order_id": self.order_id})
        self.assertEqual(first["code"], 200, first)
        self.assertEqual(second["code"], 200, second)
        self.assertTrue(second["data"]["deduplicated"])
        self.assertEqual(first["data"]["payment_id"], second["data"]["payment_id"])
        self.assertEqual(len(self.records(self.payment_entity)), 1)
        self.assertEqual(self.records(self.order_entity)[0]["order_status"], "已支付")

    async def test_cancelled_order_cannot_be_paid(self):
        await self.payment_fixture("已取消")
        result = await self.call("create_payment", {"order_id": self.order_id})
        self.assertEqual(result["code"], 409, result)
        self.assertEqual(self.records(self.payment_entity), [])

    async def test_order_write_failure_rolls_back_the_payment_and_counter(self):
        await self.payment_fixture()
        with patch.object(services.entity_service, "update_entity_record", return_value={"success": False}):
            result = await self.call("create_payment", {"order_id": self.order_id})
        self.assertEqual(result["code"], 500, result)
        self.assertEqual(self.records(self.payment_entity), [])
        from app.models.entity import EntityDBModel
        with database.get_db_session() as db:
            self.assertEqual(db.get(EntityDBModel, self.payment_entity).record_count, 0)

    async def test_failed_post_action_rolls_back_primary_and_related_records(self):
        await self.payment_fixture()
        result = await self.call("create_payment", {"order_id": self.order_id}, route_config={"handler_config": {
            "post_actions": [{"entity": "missing_fixture_entity", "operation": "create"}]
        }})
        self.assertEqual(result["code"], 500, result)
        self.assertEqual(self.records(self.payment_entity), [])
        self.assertEqual(self.records(self.order_entity)[0]["order_status"], "待支付")

    async def test_callback_never_creates_phantom_payments_or_downgrades_paid_state(self):
        await self.payment_fixture()
        missing = await self.call("handle_callback", {"payment_id": "unknown", "status": "paid"})
        self.assertEqual(missing["code"], 404, missing)
        payment = await self.call("create_payment", {"order_id": self.order_id})
        payment_id = payment["data"]["payment_id"]
        mismatch = await self.call("handle_callback", {"payment_id": payment_id, "order_id": "other-order", "status": "paid"})
        self.assertEqual(mismatch["code"], 409, mismatch)
        callback = await self.call("handle_callback", {"payment_id": payment_id, "status": "failed"})
        self.assertEqual(callback["code"], 200, callback)
        self.assertTrue(callback["data"]["payment_success"])
        self.assertEqual(self.records(self.payment_entity)[0]["status"], "已支付")
        self.assertEqual(self.records(self.order_entity)[0]["order_status"], "已支付")

    async def test_payment_refund_rejects_excess_and_persists_a_single_transition(self):
        await self.payment_fixture()
        payment = await self.call("create_payment", {"order_id": self.order_id})
        payment_id = payment["data"]["payment_id"]
        for amount in (-1, 101, "NaN"):
            result = await self.call("refund_payment", {"payment_id": payment_id, "refund_amount": amount})
            self.assertEqual(result["code"], 400, result)
        for _ in range(2):
            result = await self.call("refund_payment", {"payment_id": payment_id, "refund_amount": 100})
            self.assertEqual(result["code"], 200, result)
        self.assertEqual(self.records(self.payment_entity)[0]["status"], "已退款")
        self.assertEqual(self.records(self.order_entity)[0]["order_status"], "已退票")

    async def test_refund_confirmation_and_amount_rules_do_not_accept_invalid_values(self):
        for value in (False, "false", "0", "no", 0):
            result = await self.call("confirm_refund", {"confirm_refund": value}, service="refund_service")
            self.assertEqual(result["code"], 200, result)
            self.assertIs(result["data"]["confirm_refund"], False)
        for price, rate in ((-1, 0.1), ("NaN", 0.1), (100, -0.1), (100, 1.1), (100, "NaN"), (100, "invalid")):
            result = await self.call("calculate_refund", {"price": price, "refund_rate": rate}, service="refund_service")
            self.assertEqual(result["code"], 400, result)
        missing = await self.call("process_refund", {}, service="refund_service")
        self.assertEqual(missing["code"], 400, missing)

    async def test_unknown_filter_cannot_silently_select_the_first_record(self):
        await self.payment_fixture()
        result = self.entities.get_entity_records(self.order_entity, filters={"missing_field": "another-owner"})
        self.assertFalse(result["success"], result)

    async def ticket_refund_fixture(self):
        from datetime import datetime, timedelta
        self.ticket_entity = await self.create_entity("ticket", [
            ("ticket_number", "text"), ("price", "number"), ("status", "text"),
            ("departure_date", "date"), ("departure_time", "text"),
        ])
        self.refund_entity = await self.create_entity("refund", [
            ("refund_id", "text"), ("ticket_id", "text"), ("ticket_number", "text"),
            ("original_amount", "number"), ("refund_fee", "number"), ("refund_amount", "number"),
            ("refund_reason", "text"), ("status", "text"), ("refund_time", "datetime"), ("create_time", "datetime"),
        ])
        record = self.entities.create_entity_record(self.ticket_entity, {
            "ticket_number": "T123456789012", "price": 195, "status": "已售",
            "departure_date": (datetime.now() + timedelta(days=3)).date().isoformat(), "departure_time": "12:00:00",
        })
        self.assertTrue(record["success"], record)
        self.ticket_id = record["data"]["record"]["id"]

    async def test_ticket_refund_uses_currency_precision_and_persists_once(self):
        await self.ticket_refund_fixture()
        calculation = await self.call("calculate_refund", {"price": 195, "refund_rate": 0.1}, service="refund_service")
        self.assertEqual(calculation["data"]["refund_fee"], 20)
        self.assertEqual(calculation["data"]["refund_amount"], 175)
        for _ in range(2):
            result = await self.call("process_refund", {"ticket_id": self.ticket_id, "refund_amount": 175}, service="refund_service")
            self.assertEqual(result["code"], 200, result)
        self.assertEqual(len(self.records(self.refund_entity)), 1)
        self.assertEqual(self.records(self.ticket_entity)[0]["status"], "已退票")

    async def test_ticket_write_failure_rolls_back_refund_record(self):
        await self.ticket_refund_fixture()
        with patch.object(services.entity_service, "update_entity_record", return_value={"success": False}):
            result = await self.call("process_refund", {"ticket_id": self.ticket_id, "refund_amount": 175}, service="refund_service")
        self.assertEqual(result["code"], 500, result)
        self.assertEqual(self.records(self.refund_entity), [])
        self.assertEqual(self.records(self.ticket_entity)[0]["status"], "已售")

    async def test_notification_persistence_failure_is_not_reported_as_delivered(self):
        result = await self.call("send_notification", {"notification_type": "success", "message": "fixture"}, service="notification_service")
        self.assertEqual(result["code"], 500, result)

    async def template_entities(self, names):
        import json
        from pathlib import Path
        template = json.loads((Path(__file__).resolve().parents[2] / "app/templates/railway_ticketing.json").read_text(encoding="utf-8"))
        ids = {}
        for entity in template["entities"]:
            if entity["name"] in names:
                created = await self.entities.create_entity(EntityCreateRequest(**{**entity, "displayName": entity.get("display_name", entity["name"])}))
                self.assertTrue(created["success"], created)
                ids[entity["name"]] = created["data"]["entity"].id
        return ids

    async def test_builtin_template_accepts_payment_and_ticket_refund_records(self):
        from datetime import datetime, timedelta
        ids = await self.template_entities({"order", "payment", "ticket", "refund"})
        order = self.entities.create_entity_record(ids["order"], {
            "order_number": "O12345678901234", "passenger_name": "Fixture Rider", "passenger_phone": "00000000000",
            "total_amount": 195, "create_time": "2030-01-01 10:00:00",
        })
        self.assertTrue(order["success"], order)
        payment = await self.call("create_payment", {"order_id": order["data"]["record"]["id"]})
        self.assertEqual(payment["code"], 200, payment)
        ticket = self.entities.create_entity_record(ids["ticket"], {
            "ticket_number": "T123456789012", "train_number": "G123", "passenger_name": "Fixture Rider",
            "passenger_id_card": "fixture-document", "departure_station": "Fixture A", "arrival_station": "Fixture B",
            "departure_date": (datetime.now() + timedelta(days=3)).date().isoformat(), "departure_time": "12:00",
            "seat_type": "二等座", "price": 195, "status": "已售", "purchase_time": "2030-01-01 10:00:00",
        })
        self.assertTrue(ticket["success"], ticket)
        result = await self.call("process_refund", {"ticket_id": ticket["data"]["record"]["id"], "refund_amount": 175}, service="refund_service")
        self.assertEqual(result["code"], 200, result)
        self.assertEqual(self.records(ids["refund"])[0]["refund_reason"], "行程变更")

    async def test_builtin_notification_template_persists_and_deduplicates_workflow_messages(self):
        ids = await self.template_entities({"notification"})
        body = {"user_id": "7", "notification_type": "success", "message": "Fixture result", "channel": "in_app", "idempotency_key": "fixture-instance:step"}
        first = await self.call("send_notification", body, service="notification_service")
        second = await self.call("send_notification", body, service="notification_service")
        self.assertEqual(first["code"], 200, first)
        self.assertEqual(second["code"], 200, second)
        self.assertTrue(second["data"]["deduplicated"])
        records = self.records(ids["notification"])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["notification_type"], "站内信")
        self.assertEqual(records[0]["status"], "未读")
        self.assertEqual(records[0]["recipient_id"], "7")
        self.assertIsNotNone(records[0]["send_time"])

    async def test_mysql_concurrent_payment_requests_share_one_order_transition(self):
        if self.engine.dialect.name != "mysql":
            self.skipTest("requires the isolated MySQL integration database")
        import asyncio
        await self.payment_fixture()
        def pay():
            return asyncio.run(self.call("create_payment", {"order_id": self.order_id}))
        results = await asyncio.gather(asyncio.to_thread(pay), asyncio.to_thread(pay))
        self.assertEqual([result["code"] for result in results], [200, 200], results)
        self.assertEqual(len(self.records(self.payment_entity)), 1)

    async def test_notification_uses_authenticated_owner_and_real_pagination(self):
        entity = await self.create_entity("notification", [
            ("notification_id", "text"), ("recipient_id", "text"), ("status", "text"), ("is_read", "boolean"),
        ])
        for notification_id, owner in (("mine-1", "7"), ("mine-2", "7"), ("other", "9")):
            self.assertTrue(self.entities.create_entity_record(entity, {"notification_id": notification_id, "recipient_id": owner, "status": "sent", "is_read": False})["success"])
        request = SimpleNamespace(state=SimpleNamespace(user_info={"user_id": 7, "user_type": "user"}))
        listing = await self.call("list_notifications", {"user_id": 9, "limit": 1}, service="notification_service", request=request)
        self.assertEqual(listing["code"], 200, listing)
        self.assertEqual(listing["data"]["total"], 2)
        self.assertEqual(listing["data"]["unread_count"], 2)
        self.assertTrue(listing["data"]["has_next"])
        self.assertEqual(listing["data"]["items"][0]["recipient_id"], "7")
        for method in ("mark_as_read", "delete_notification"):
            result = await self.call(method, {"notification_id": "other", "requester_user_id": 9}, service="notification_service", request=request)
            self.assertEqual(result["code"], 403, result)
        self.assertEqual(len(self.records(entity)), 3)
