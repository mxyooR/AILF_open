"""
服务分发器
- 为 custom_function 处理器提供 service/method 调用入口
- 默认提供 payment_service / notification_service 的示例实现
"""
from __future__ import annotations

import inspect
import hashlib
import json
import time
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional

from app.services.service_registry import get_service_registry
from app.services.entity_service import entity_service
from app.core.database import business_transaction, get_db_session
from app.services.business_rules import (
    BusinessOperationError, parse_amount, parse_confirmation, require_write, requester_id, business_code,
)
from app.services.workflow_context import response_error


def _first_value(request_data: Dict[str, Any], key: str) -> Optional[Any]:
    if not isinstance(request_data, dict):
        return None
    for location in ("path", "query", "body", "form"):
        bucket = request_data.get(location) or {}
        if isinstance(bucket, dict) and key in bucket:
            return bucket.get(key)
    return None


def _now_iso() -> str:
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def _isoformat(dt: datetime) -> str:
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def _digits_from_datetime(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H%M%S%f")


def _db_time(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _build_lock_id(base_dt: datetime) -> str:
    for offset in range(10):
        candidate_dt = base_dt + timedelta(seconds=offset)
        lock_id = f"L{candidate_dt.strftime('%Y%m%d%H%M%S')}"
        if not _find_entity_record("seat_lock", {"lock_id": lock_id}):
            return lock_id
    return f"L{_digits_from_datetime(base_dt)[:14]}"


def _get_entity_id(entity_name: str) -> Optional[str]:
    result = entity_service.get_entity_by_name(entity_name)
    if not result.get("success"):
        return None
    entity = result.get("data", {}).get("entity")
    return getattr(entity, "id", None) if entity else None


def _find_entity_record(entity_name: str, filters: Dict[str, Any], *, lock_for_update=True) -> Optional[Dict[str, Any]]:
    entity_id = _get_entity_id(entity_name)
    if not entity_id:
        return None
    result = entity_service.get_entity_records(entity_id, page=1, limit=1, filters=filters, lock_for_update=lock_for_update)
    if not result.get("success"):
        return None
    records = result.get("data", {}).get("records") or []
    return records[0] if records else None


def _find_entity_records(entity_name: str, filters: Dict[str, Any], limit: int = 20) -> list[Dict[str, Any]]:
    entity_id = _get_entity_id(entity_name)
    if not entity_id:
        return []
    result = entity_service.get_entity_records(entity_id, page=1, limit=limit, filters=filters)
    if not result.get("success"):
        return []
    return result.get("data", {}).get("records") or []


def _normalize_handler_config(route_config: Any) -> Dict[str, Any]:
    if not isinstance(route_config, dict):
        return {}
    handler_config = route_config.get("handler_config") or route_config.get("handlerConfig") or {}
    if isinstance(handler_config, str):
        try:
            handler_config = json.loads(handler_config)
        except json.JSONDecodeError:
            return {}
    return handler_config if isinstance(handler_config, dict) else {}


def _get_request_bucket(request_data: Dict[str, Any], location: str) -> Dict[str, Any]:
    if not isinstance(request_data, dict):
        return {}
    bucket = request_data.get(location) or {}
    return bucket if isinstance(bucket, dict) else {}


def _resolve_request_value(request_data: Dict[str, Any], key: str) -> Optional[Any]:
    if not key:
        return None
    if "." in key:
        prefix, field = key.split(".", 1)
        if prefix in {"path", "query", "body", "form"}:
            bucket = _get_request_bucket(request_data, prefix)
            return bucket.get(field)
    return _first_value(request_data, key)


def _generate_unique_code(
    entity_name: str,
    field_name: str,
    prefix: str,
    base_dt: datetime,
    fmt: str,
) -> str:
    for offset in range(10):
        candidate_dt = base_dt + timedelta(seconds=offset)
        value = f"{prefix}{candidate_dt.strftime(fmt)}"
        if not _find_entity_record(entity_name, {field_name: value}):
            return value
    return f"{prefix}{_digits_from_datetime(base_dt)[:14]}"


def _resolve_action_value(spec: Any, request_data: Dict[str, Any]) -> Any:
    if isinstance(spec, dict):
        if "lookup" in spec:
            lookup = spec.get("lookup") or {}
            entity = lookup.get("entity")
            field = lookup.get("field")
            filters = _resolve_action_mapping(lookup.get("filters") or {}, request_data)
            if entity and field and filters:
                record = _find_entity_record(entity, filters)
                if record and field in record:
                    return record.get(field)
            return lookup.get("default")
        if "value" in spec:
            return spec.get("value")
        if "from" in spec:
            return _resolve_request_value(request_data, spec.get("from"))
        if "generate" in spec:
            gen = spec.get("generate")
            now_dt = datetime.utcnow()
            if isinstance(gen, str):
                if gen == "now":
                    return _db_time(now_dt)
                if gen == "ticket_number":
                    return _generate_unique_code("ticket", "ticket_number", "T", now_dt, "%y%m%d%H%M%S")
                if gen == "lock_id":
                    return _generate_unique_code("seat_lock", "lock_id", "L", now_dt, "%Y%m%d%H%M%S")
                if gen == "payment_id":
                    return _generate_unique_code("payment", "payment_id", "P", now_dt, "%Y%m%d%H%M%S")
            if isinstance(gen, dict):
                gen_type = gen.get("type")
                if gen_type == "now_plus":
                    delta = timedelta(
                        hours=float(gen.get("hours", 0) or 0),
                        minutes=float(gen.get("minutes", 0) or 0),
                        seconds=float(gen.get("seconds", 0) or 0),
                    )
                    return _db_time(now_dt + delta)
                if gen_type == "sequence":
                    return _generate_unique_code(
                        gen.get("entity", ""),
                        gen.get("field", ""),
                        gen.get("prefix", ""),
                        now_dt,
                        gen.get("format", "%Y%m%d%H%M%S"),
                    )
        return None
    if isinstance(spec, str):
        if spec.startswith("${") and spec.endswith("}"):
            return _resolve_request_value(request_data, spec[2:-1])
        return spec
    return spec


def _resolve_action_mapping(mapping: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
    resolved: Dict[str, Any] = {}
    if not isinstance(mapping, dict):
        return resolved
    for key, spec in mapping.items():
        value = _resolve_action_value(spec, request_data)
        if value is not None:
            resolved[key] = value
    return resolved


def _get_field_options(entity_name: str, field_name: str) -> list[Any]:
    if not entity_name or not field_name:
        return []
    result = entity_service.get_entity_by_name(entity_name)
    if not result.get("success"):
        return []
    entity = result.get("data", {}).get("entity")
    fields = getattr(entity, "fields", []) or []
    for field in fields:
        if getattr(field, "name", None) == field_name:
            options = getattr(field, "options", None)
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except json.JSONDecodeError:
                    return []
            if isinstance(options, list):
                return options
            return []
    return []


def _get_entity_field_names(entity_name: str) -> set[str]:
    if not entity_name:
        return set()
    result = entity_service.get_entity_by_name(entity_name)
    if not result.get("success"):
        return set()
    entity = result.get("data", {}).get("entity")
    fields = getattr(entity, "fields", []) or []
    names: set[str] = set()
    for field in fields:
        name = getattr(field, "name", None)
        if isinstance(name, str) and name:
            names.add(name)
    return names


def _normalize_option_value(entity_name: str, field_name: str, value: Any) -> Any:
    options = _get_field_options(entity_name, field_name)
    if not options:
        return value
    if value in options:
        return value
    if isinstance(value, str):
        lower = value.strip().lower()
        alias_map = {
            "online": "支付宝",
            "alipay": "支付宝",
            "wechat": "微信支付",
            "wechatpay": "微信支付",
            "wxpay": "微信支付",
            "bank": "银行卡",
            "bank_card": "银行卡",
            "card": "银行卡",
            "cash": "现金",
        }
        mapped = alias_map.get(lower)
        if mapped in options:
            return mapped
        for option in options:
            if isinstance(option, str) and option.lower() == lower:
                return option
    return options[0]


def _execute_post_actions(post_actions: list[Dict[str, Any]], request_data: Dict[str, Any]) -> list[Dict[str, Any]]:
    results: list[Dict[str, Any]] = []
    if not post_actions:
        return results
    for action in post_actions:
        if not isinstance(action, dict):
            continue
        entity = action.get("entity")
        if not entity:
            continue
        entity_id = _get_entity_id(entity)
        if not entity_id:
            results.append({"entity": entity, "success": False, "error": "entity_not_found"})
            continue
        operation = (action.get("operation") or "create").lower()
        required = action.get("required") or []
        filters = _resolve_action_mapping(action.get("filters") or {}, request_data)
        data = _resolve_action_mapping(action.get("data") or {}, request_data)

        missing_required = False
        for key in required:
            value = _resolve_request_value(request_data, key)
            if value is None and key not in data:
                missing_required = True
                break
        if missing_required:
            results.append({"entity": entity, "success": False, "error": "missing_required"})
            continue

        if operation in {"update", "upsert"}:
            if not filters:
                results.append({"entity": entity, "success": False, "error": "missing_filters"})
                continue
            record = _find_entity_record(entity, filters)
            if record:
                record_id = record.get("id")
                update_result = entity_service.update_entity_record(entity_id, record_id, data)
                results.append({"entity": entity, "success": update_result.get("success"), "data": update_result})
                continue
            if operation == "update":
                results.append({"entity": entity, "success": False, "error": "record_not_found"})
                continue

        if operation in {"create", "upsert"}:
            create_payload = {**filters, **data} if filters else data
            create_result = entity_service.create_entity_record(entity_id, create_payload)
            results.append({"entity": entity, "success": create_result.get("success"), "data": create_result})
            continue

        results.append({"entity": entity, "success": False, "error": "unknown_operation"})
    if any(not result.get("success") for result in results):
        raise BusinessOperationError("后置业务操作失败，已撤销本次操作")
    return results


class PaymentService:
    """示例支付服务（模拟实现）"""

    def _build_payment_id(self, base_dt: datetime) -> Optional[str]:
        # 兼容模板中的 ^P\d{14}$，多个进程也不会挤占同一秒的十个时间槽。
        return business_code("P", 14)

    def refund_payment(self, *, request_data: Dict[str, Any], **_: Any) -> Dict[str, Any]:
        payment_id = _first_value(request_data, "payment_id")
        refund_amount = _first_value(request_data, "refund_amount")
        refund_reason = _first_value(request_data, "refund_reason")

        if not payment_id:
            return {"code": 400, "message": "缺少 payment_id", "data": None}
        if refund_amount is None:
            return {"code": 400, "message": "缺少 refund_amount", "data": None}
        payment = _find_entity_record("payment", {"payment_id": payment_id}, lock_for_update=False) or _find_entity_record("payment", {"id": payment_id}, lock_for_update=False)
        if not payment:
            return {"code": 404, "message": "支付记录不存在", "data": None}
        # 所有支付操作统一先锁订单、再锁支付记录，避免与支付创建交叉加锁。
        order = _find_entity_record("order", {"id": payment["order_id"]}) if payment.get("order_id") else None
        if payment.get("order_id") and not order:
            return {"code": 404, "message": "支付关联订单不存在", "data": None}
        payment = _find_entity_record("payment", {"id": payment["id"]})
        if not payment:
            return {"code": 404, "message": "支付记录不存在", "data": None}
        try:
            amount = parse_amount(refund_amount)
            if amount > parse_amount(payment.get("amount")):
                return {"code": 400, "message": "退款金额不能超过支付金额", "data": None}
            if amount != parse_amount(payment.get("amount")):
                return {"code": 400, "message": "示例支付服务仅支持整笔退款，票务手续费退款请使用退票服务", "data": None}
        except ValueError as exc:
            return {"code": 400, "message": str(exc), "data": None}
        previous = str(payment.get("status") or "").lower()
        if previous in {"已退款", "refunded"}:
            # 有退款金额字段时可核对重试；旧配置无退款账本时拒绝再次退款。
            if payment.get("refund_amount") is not None and parse_amount(payment["refund_amount"]) == amount:
                return {"code": 200, "message": "退款已处理", "data": {"payment_id": payment_id, "refund_status": "completed", "deduplicated": True}}
            return {"code": 409, "message": "该支付已退款", "data": None}
        if previous not in {"已支付", "paid", "success"}:
            return {"code": 409, "message": "只有已支付记录可以退款", "data": None}
        fields = _get_entity_field_names("payment")
        updates = {"status": "已退款"}
        if "refund_amount" in fields:
            updates["refund_amount"] = amount
        require_write(entity_service.update_entity_record(_get_entity_id("payment"), payment["id"], updates), "退款状态保存失败")
        if amount == parse_amount(payment.get("amount")) and payment.get("order_id"):
            require_write(entity_service.update_entity_record(_get_entity_id("order"), order["id"], {"order_status": "已退票"}), "订单退款状态保存失败")
        return {
            "code": 200,
            "message": "模拟退款处理完成",
            "data": {
                "refund_id": f"refund_{payment.get('payment_id') or payment['id']}",
                "payment_id": payment_id,
                "refund_amount": refund_amount,
                "refund_reason": refund_reason,
                "refund_status": "completed",
                "refund_time": _now_iso(),
            },
        }

    def create_payment(self, *, request_data: Dict[str, Any], route_config: Any = None, **_: Any) -> Dict[str, Any]:
        payload = request_data.get("body") or {}
        order_id = _first_value(request_data, "order_id") or _first_value(request_data, "order_number")
        if not order_id:
            return {"code": 400, "message": "缺少订单ID", "data": None}

        order = _find_entity_record("order", {"id": order_id}) or _find_entity_record(
            "order", {"order_number": order_id}
        )
        if not order:
            return {"code": 404, "message": "订单不存在", "data": None}

        amount = _first_value(request_data, "amount")
        try:
            # 订单金额是唯一计价依据，客户端传入金额只用于核对，不能覆盖订单价格。
            amount_value = parse_amount(order.get("total_amount"))
            if amount is not None and parse_amount(amount) != amount_value:
                return {"code": 400, "message": "支付金额与订单金额不一致", "data": None}
        except ValueError as exc:
            return {"code": 400, "message": str(exc), "data": None}

        order_status = str(order.get("order_status") or "").lower()
        if order_status in {"已取消", "已退票", "已退款", "已关闭", "cancelled", "canceled", "refunded", "closed"}:
            return {"code": 409, "message": "订单当前状态不可支付", "data": None}
        existing = _find_entity_record("payment", {"order_id": order.get("id")})
        if existing and str(existing.get("status") or "").lower() in {"已支付", "paid", "success"}:
            if parse_amount(existing.get("amount")) != amount_value:
                return {"code": 409, "message": "历史支付金额与订单不一致", "data": None}
            return {"code": 200, "message": "订单已支付", "data": {**existing, "payment_success": True, "deduplicated": True}}
        if order_status not in {"", "待支付", "未支付", "支付失败", "pending", "unpaid", "failed"}:
            return {"code": 409, "message": "订单当前状态不可重复支付", "data": None}

        payment_method = _first_value(request_data, "payment_method") or order.get("payment_method") or "支付宝"
        payment_method = _normalize_option_value("payment", "payment_method", payment_method)
        if not payment_method:
            payment_method = "支付宝"

        now_dt = datetime.utcnow()
        payment_id = self._build_payment_id(now_dt)
        if not payment_id:
            return {"code": 500, "message": "生成支付编号失败", "data": None}

        transaction_id = f"TX{uuid.uuid4().hex[:12]}"
        status = "已支付"
        expire_time = _db_time(now_dt + timedelta(minutes=15))
        create_time = _db_time(now_dt)

        record = {
            "payment_id": payment_id,
            "order_id": order.get("id") or order_id,
            "order_number": order.get("order_number") or order_id,
            "amount": amount_value,
            "payment_method": payment_method,
            "transaction_id": transaction_id,
            "status": status,
            "payment_time": create_time,
            "expire_time": expire_time,
            "create_time": create_time,
        }

        payment_entity_id = _get_entity_id("payment")
        if not payment_entity_id:
            return {"code": 500, "message": "支付实体不存在", "data": None}
        create_result = entity_service.create_entity_record(payment_entity_id, record)
        if not create_result.get("success"):
            return {
                "code": 500,
                "message": "支付记录创建失败",
                "data": {"details": create_result.get("details")},
            }

        order_entity_id = _get_entity_id("order")
        if order_entity_id and order.get("id"):
            require_write(entity_service.update_entity_record(
                order_entity_id,
                order["id"],
                {"order_status": "已支付", "payment_time": create_time, "payment_method": payment_method},
            ), "订单支付状态更新失败")

        handler_config = _normalize_handler_config(route_config)
        post_actions = handler_config.get("post_actions") or []
        if post_actions:
            _execute_post_actions(post_actions, request_data)

        data = create_result.get("data", {}).get("record") or record
        data.update(
            {
                "payment_success": True,
                "payment_url": f"/mock/pay/{payment_id}",
                "qr_code": None,
            }
        )
        return {"code": 200, "message": "支付成功", "data": data}

    def get_payment_status(self, *, request_data: Dict[str, Any], **_: Any) -> Dict[str, Any]:
        payment_id = _first_value(request_data, "payment_id")
        if not payment_id:
            return {"code": 400, "message": "缺少支付ID", "data": None}

        payment = (
            _find_entity_record("payment", {"payment_id": payment_id})
            or _find_entity_record("payment", {"id": payment_id})
            or _find_entity_record("payment", {"transaction_id": payment_id})
        )
        if not payment:
            return {"code": 404, "message": "支付记录不存在", "data": None}

        status = payment.get("status")
        success = status in ("已支付", "paid", "success")
        data = {
            "payment_id": payment.get("payment_id") or payment.get("id"),
            "order_id": payment.get("order_id"),
            "amount": payment.get("amount"),
            "payment_method": payment.get("payment_method"),
            "status": status,
            "payment_time": payment.get("payment_time"),
            "payment_success": success,
        }
        return {"code": 200, "message": "查询成功", "data": data}

    def handle_callback(self, *, request_data: Dict[str, Any], **_: Any) -> Dict[str, Any]:
        payload = request_data.get("body") or {}
        payment_id = _first_value(request_data, "payment_id")
        order_id = _first_value(request_data, "order_id") or _first_value(request_data, "order_number")
        transaction_id = _first_value(request_data, "transaction_id")
        status = _first_value(request_data, "status") or _first_value(request_data, "trade_status")

        normalized = str(status).lower()
        paid_statuses = {"success", "paid", "trade_success", "支付成功", "已支付"}
        failed_statuses = {"failed", "failure", "trade_closed", "支付失败"}
        if normalized not in paid_statuses | failed_statuses:
            return {"code": 400, "message": "缺少或不支持的支付状态", "data": None}
        new_status = "已支付" if normalized in paid_statuses else "支付失败"

        payment = None
        if payment_id:
            payment = _find_entity_record("payment", {"payment_id": payment_id}, lock_for_update=False) or _find_entity_record(
                "payment", {"id": payment_id}, lock_for_update=False
            )
        if not payment and transaction_id:
            payment = _find_entity_record("payment", {"transaction_id": transaction_id}, lock_for_update=False)
        if not payment and order_id:
            payment = _find_entity_record("payment", {"order_id": order_id}, lock_for_update=False) or _find_entity_record(
                "payment", {"order_number": order_id}, lock_for_update=False
            )

        # 回调只能更新已有支付，且订单归属以支付记录为准，不能按外部传入订单另造记录。
        if not payment:
            return {"code": 404, "message": "支付记录不存在", "data": None}
        order = _find_entity_record("order", {"id": payment["order_id"]}) if payment.get("order_id") else None
        if not order:
            return {"code": 404, "message": "支付关联订单不存在", "data": None}
        payment = _find_entity_record("payment", {"id": payment["id"]})
        if not payment:
            return {"code": 404, "message": "支付记录不存在", "data": None}
        if order_id and str(order_id) not in {str(payment.get("order_id")), str(payment.get("order_number"))}:
            return {"code": 409, "message": "回调订单与支付记录不一致", "data": None}
        try:
            if payload.get("amount") is not None and parse_amount(payload["amount"]) != parse_amount(payment.get("amount")):
                return {"code": 400, "message": "回调金额与支付记录不一致", "data": None}
        except ValueError as exc:
            return {"code": 400, "message": str(exc), "data": None}
        previous = str(payment.get("status") or "").lower()
        if previous in {"已退款", "refunded", "已取消", "cancelled", "canceled"}:
            return {"code": 409, "message": "支付已关闭，不能处理回调", "data": None}
        if previous in paid_statuses:
            # 迟到的失败通知不能把已支付状态倒退，也不能清空原交易号。
            return {"code": 200, "message": "支付回调已处理", "data": {"status": "已支付", "payment_success": True, "deduplicated": True}}
        if str(order.get("order_status") or "").lower() not in {"待支付", "未支付", "支付失败", "pending", "unpaid", "failed"}:
            return {"code": 409, "message": "订单当前状态不能接收支付回调", "data": None}
        now_time = _db_time(datetime.utcnow())
        updates = {"status": new_status}
        if transaction_id:
            updates["transaction_id"] = transaction_id
        if new_status == "已支付":
            updates["payment_time"] = now_time
        require_write(entity_service.update_entity_record(_get_entity_id("payment"), payment["id"], updates), "支付状态更新失败")
        order_updates = {"order_status": new_status}
        if new_status == "已支付":
            order_updates["payment_time"] = now_time
        require_write(entity_service.update_entity_record(_get_entity_id("order"), order["id"], order_updates), "订单状态更新失败")

        return {
            "code": 200,
            "message": "回调处理成功",
            "data": {"status": new_status, "payment_success": new_status == "已支付"},
        }


class NotificationService:
    """示例通知服务（占位实现）"""

    @staticmethod
    def _find_notification_record(entity_name: str, notification_id: Any) -> Optional[Dict[str, Any]]:
        record = _find_entity_record(entity_name, {"notification_id": notification_id})
        if record:
            return record
        return _find_entity_record(entity_name, {"id": notification_id})

    @staticmethod
    def _is_record_owned_by_user(record: Dict[str, Any], user_id: Any) -> bool:
        if user_id is None:
            return True
        uid = str(user_id)
        owner_fields = ("user_id", "recipient_id", "receiver_id", "target_user_id", "接收者ID")
        owner_values = []
        for field in owner_fields:
            value = record.get(field) if isinstance(record, dict) else None
            if value is not None and value != "":
                owner_values.append(str(value))
        if not owner_values:
            return False
        return uid in owner_values

    @staticmethod
    def _count_unread(entity_name, filters, field_names):
        """未读总数按接收者统计全部记录，翻页不会使通知角标跟着当前页变化。"""
        from sqlalchemy import text
        table = "entity_" + entity_service._safe_table_name(entity_name)
        clauses, parameters = [], {}
        for index, (field, value) in enumerate(filters.items()):
            clauses.append(f"`{entity_service._safe_column_name(field)}` = :owner_{index}")
            parameters[f"owner_{index}"] = value
        if "status" in field_names:
            clauses.append("COALESCE(`status`, '') NOT IN ('read', '已读')")
        for field in ("is_read", "read", "是否已读"):
            if field in field_names:
                clauses.append(f"COALESCE(`{field}`, 0) = 0")
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with get_db_session() as db:
            return db.execute(text(f"SELECT COUNT(*) FROM `{table}`{where}"), parameters).scalar() or 0

    def send_notification(self, *, request_data: Dict[str, Any], route_config: Any = None, request=None, **_: Any) -> Dict[str, Any]:
        handler_config = _normalize_handler_config(route_config)
        notification_type = _first_value(request_data, "notification_type") or _first_value(request_data, "type")
        template_code = _first_value(request_data, "template_code")
        message = _first_value(request_data, "message") or _first_value(request_data, "content") or _first_value(request_data, "body")
        title = _first_value(request_data, "title")
        channel = _first_value(request_data, "channel") or _first_value(request_data, "notify_channel") or "in_app"
        user_id = (
            _first_value(request_data, "user_id")
            or _first_value(request_data, "recipient_id")
            or _first_value(request_data, "receiver_id")
            or _first_value(request_data, "target_user_id")
        )
        if request is not None:
            authenticated_id = requester_id(request, user_id)
            state = getattr(request, "state", None)
            if (getattr(state, "user_info", None) or {}).get("user_type") != "developer":
                if user_id is not None and str(user_id) != str(authenticated_id):
                    return {"code": 403, "message": "普通用户不能给其他用户发送通知", "data": None}
                user_id = authenticated_id
        idempotency_key = (
            _first_value(request_data, "idempotency_key")
            or _first_value(request_data, "biz_key")
            or _first_value(request_data, "request_id")
        )

        if not notification_type:
            return {"code": 400, "message": "缺少 notification_type", "data": None}
        if not template_code:
            template_code = f"{str(notification_type).lower()}_default"
        if not message:
            message = template_code or title or "系统通知"

        notification_id = business_code("N", 14)
        sent_at = _now_iso()
        status = "sent"
        title = title or template_code or "系统通知"

        data = {
            "notification_id": notification_id,
            "notification_type": notification_type,
            "channel": channel,
            "template_code": template_code,
            "title": title,
            "message": message,
            "status": status,
            "sent_at": sent_at,
        }
        if user_id is not None:
            data["user_id"] = user_id

        entity_name = handler_config.get("entity") or "notification"
        persist_enabled = bool(handler_config.get("persist", True))
        strict_persist = bool(handler_config.get("strict_persist", persist_enabled))

        if persist_enabled:
            entity_id = _get_entity_id(entity_name)
            field_names = _get_entity_field_names(entity_name)
            if entity_id and field_names:
                idempotency_field = next(
                    (f for f in ("idempotency_key", "biz_key", "request_id") if f in field_names),
                    None
                )

                # 旧模板没有单独幂等列，使用稳定通知号复用已有唯一约束，无需修改真实配置。
                if idempotency_key and not idempotency_field and "notification_id" in field_names:
                    digest = hashlib.sha256(f"{user_id}:{idempotency_key}".encode()).hexdigest()
                    notification_id = "N" + str(int(digest, 16) % (10 ** 14)).zfill(14)
                    data["notification_id"] = notification_id
                    idempotency_field = "notification_id"
                if idempotency_key and idempotency_field:
                    dedupe_filters: Dict[str, Any] = {idempotency_field: notification_id if idempotency_field == "notification_id" else idempotency_key}
                    user_field = next((f for f in ("user_id", "recipient_id", "receiver_id", "target_user_id") if f in field_names), None)
                    if user_id is not None and user_field:
                        dedupe_filters[user_field] = user_id
                    existing = _find_entity_record(entity_name, dedupe_filters)
                    if existing:
                        existing_data = {
                            "notification_id": existing.get("notification_id") or existing.get("id") or notification_id,
                            "notification_type": existing.get("notification_type") or notification_type,
                            "channel": existing.get("channel") or channel,
                            "template_code": existing.get("template_code") or template_code,
                            "title": existing.get("title") or title,
                            "message": existing.get("message") or existing.get("content") or message,
                            "status": existing.get("status") or status,
                            "sent_at": existing.get("sent_at") or existing.get("created_at") or sent_at,
                        }
                        if user_id is not None:
                            existing_data["user_id"] = user_id
                        existing_data["deduplicated"] = True
                        return {"code": 200, "message": "通知已存在，返回历史结果", "data": existing_data}

                candidate_fields: Dict[str, Any] = {
                    "notification_id": notification_id,
                    "user_id": user_id,
                    "recipient_id": user_id,
                    "receiver_id": user_id,
                    "target_user_id": user_id,
                    "接收者ID": user_id,
                    "notification_type": notification_type,
                    "type": notification_type,
                    "通知类型": notification_type,
                    "channel": channel,
                    "template_code": template_code,
                    "模板代码": template_code,
                    "title": title,
                    "通知标题": title,
                    "message": message,
                    "content": message,
                    "body": message,
                    "通知内容": message,
                    "status": status,
                    "状态": status,
                    "sent_at": sent_at,
                    "send_time": _db_time(datetime.utcnow()),
                    "发送时间": sent_at,
                    "created_at": _db_time(datetime.utcnow()),
                    "create_time": _db_time(datetime.utcnow()),
                    "is_read": False,
                    "read": False,
                    "是否已读": False,
                    "读取时间": None,
                }
                type_options = _get_field_options(entity_name, "notification_type")
                if type_options and notification_type not in type_options:
                    # 工作流传入 success/info 是消息级别，铁路模板的类型字段保存发送渠道。
                    stored_type = {"in_app": "站内信", "email": "邮件", "sms": "短信"}.get(channel, notification_type)
                    candidate_fields["notification_type"] = _normalize_option_value(entity_name, "notification_type", stored_type)
                if "status" in field_names:
                    candidate_fields["status"] = _normalize_option_value(entity_name, "status", "未读" if channel == "in_app" else "已发送")
                    data["status"] = candidate_fields["status"]
                if idempotency_key and idempotency_field:
                    candidate_fields[idempotency_field] = notification_id if idempotency_field == "notification_id" else idempotency_key

                defaults = handler_config.get("defaults") if isinstance(handler_config.get("defaults"), dict) else {}
                for key, value in defaults.items():
                    if key not in candidate_fields:
                        candidate_fields[key] = value

                record = {
                    key: value
                    for key, value in candidate_fields.items()
                    if key in field_names and value is not None
                }

                create_result = entity_service.create_entity_record(entity_id, record)
                if create_result.get("success"):
                    persisted = create_result.get("data", {}).get("record") or record
                    data["persisted"] = True
                    if persisted.get("id"):
                        data["record_id"] = persisted.get("id")
                else:
                    data["persisted"] = False
                    data["persist_error"] = create_result.get("details") or create_result.get("message") or "落库失败"
                    if strict_persist:
                        return {
                            "code": 500,
                            "message": "通知发送成功，但落库失败",
                            "data": data
                        }
            else:
                data["persisted"] = False
                data["persist_error"] = f"通知实体不存在: {entity_name}"
                if strict_persist:
                    return {
                        "code": 500,
                        "message": data["persist_error"],
                        "data": data
                    }

        return {
            "code": 200,
            "message": "通知发送成功",
            "data": data,
        }

    def list_notifications(self, *, request_data: Dict[str, Any], route_config: Any = None, request=None, **_: Any) -> Dict[str, Any]:
        handler_config = _normalize_handler_config(route_config)
        entity_name = handler_config.get("entity") or "notification"
        entity_id = _get_entity_id(entity_name)
        if not entity_id:
            return {"code": 500, "message": f"通知实体不存在: {entity_name}", "data": None}

        user_id = (
            _first_value(request_data, "user_id")
            or _first_value(request_data, "recipient_id")
            or _first_value(request_data, "receiver_id")
            or _first_value(request_data, "target_user_id")
        )
        user_id = requester_id(request, user_id)
        page_raw = _first_value(request_data, "page") or 1
        limit_raw = _first_value(request_data, "limit") or 20
        try:
            page = max(int(page_raw), 1)
        except Exception:
            page = 1
        try:
            limit = int(limit_raw)
            limit = 20 if limit <= 0 else min(limit, 100)
        except Exception:
            limit = 20

        field_names = _get_entity_field_names(entity_name)
        filters: Dict[str, Any] = {}
        if user_id is not None:
            user_field = next((f for f in ("user_id", "recipient_id", "receiver_id", "target_user_id", "接收者ID") if f in field_names), None)
            if user_field:
                filters[user_field] = user_id
            else:
                return {"code": 403, "message": "通知实体未配置接收者字段", "data": None}

        records_result = entity_service.get_entity_records(entity_id, page=page, limit=limit, filters=filters or None)
        if not records_result.get("success"):
            return {
                "code": 500,
                "message": "查询通知列表失败",
                "data": {"details": records_result.get("details")},
            }

        data = records_result.get("data", {})
        pagination = data.get("pagination") or {}
        if hasattr(pagination, "model_dump"):
            pagination = pagination.model_dump()
        records = data.get("records") or []
        unread_count = self._count_unread(entity_name, filters, field_names)

        return {
            "code": 200,
            "message": "通知列表查询成功",
            "data": {
                "items": records,
                "total": pagination.get("total", len(records)),
                "page": pagination.get("page", page),
                "limit": pagination.get("limit", limit),
                "has_next": pagination.get("has_next", False),
                "has_prev": pagination.get("has_prev", False),
                "unread_count": unread_count,
            },
        }

    def mark_as_read(self, *, request_data: Dict[str, Any], route_config: Any = None, request=None, **_: Any) -> Dict[str, Any]:
        handler_config = _normalize_handler_config(route_config)
        entity_name = handler_config.get("entity") or "notification"
        entity_id = _get_entity_id(entity_name)
        if not entity_id:
            return {"code": 500, "message": f"通知实体不存在: {entity_name}", "data": None}

        notification_id = _first_value(request_data, "notification_id") or _first_value(request_data, "id")
        if not notification_id:
            return {"code": 400, "message": "缺少 notification_id", "data": None}

        requester_user_id = (
            _first_value(request_data, "requester_user_id")
            or _first_value(request_data, "user_id")
        )
        requester_user_id = requester_id(request, requester_user_id)

        field_names = _get_entity_field_names(entity_name)
        record = self._find_notification_record(entity_name, notification_id)
        if not record:
            return {"code": 404, "message": "通知不存在", "data": None}
        if requester_user_id is not None and not self._is_record_owned_by_user(record, requester_user_id):
            return {"code": 403, "message": "无权操作该通知", "data": None}

        record_id = record.get("id")
        if not record_id:
            return {"code": 500, "message": "通知记录缺少主键，无法更新", "data": None}

        now_time = _db_time(datetime.utcnow())
        update_fields: Dict[str, Any] = {}
        if "status" in field_names:
            update_fields["status"] = "已读" if "已读" in _get_field_options(entity_name, "status") else "read"
        if "read_time" in field_names:
            update_fields["read_time"] = now_time
        if "is_read" in field_names:
            update_fields["is_read"] = True
        if "read" in field_names:
            update_fields["read"] = True
        if not update_fields:
            update_fields = {"status": "read"}

        update_result = entity_service.update_entity_record(entity_id, record_id, update_fields)
        if not update_result.get("success"):
            return {
                "code": 500,
                "message": "通知已读更新失败",
                "data": {"details": update_result.get("details")},
            }

        updated = update_result.get("data", {}).get("record") or {**record, **update_fields}
        return {
            "code": 200,
            "message": "通知已标记为已读",
            "data": updated,
        }

    def delete_notification(self, *, request_data: Dict[str, Any], route_config: Any = None, request=None, **_: Any) -> Dict[str, Any]:
        handler_config = _normalize_handler_config(route_config)
        entity_name = handler_config.get("entity") or "notification"
        entity_id = _get_entity_id(entity_name)
        if not entity_id:
            return {"code": 500, "message": f"通知实体不存在: {entity_name}", "data": None}

        notification_id = _first_value(request_data, "notification_id") or _first_value(request_data, "id")
        if not notification_id:
            return {"code": 400, "message": "缺少 notification_id", "data": None}

        requester_user_id = (
            _first_value(request_data, "requester_user_id")
            or _first_value(request_data, "user_id")
        )
        requester_user_id = requester_id(request, requester_user_id)

        record = self._find_notification_record(entity_name, notification_id)
        if not record:
            return {"code": 404, "message": "通知不存在", "data": None}
        if requester_user_id is not None and not self._is_record_owned_by_user(record, requester_user_id):
            return {"code": 403, "message": "无权删除该通知", "data": None}

        record_id = record.get("id")
        if not record_id:
            return {"code": 500, "message": "通知记录缺少主键，无法删除", "data": None}

        delete_result = entity_service.delete_entity_record(entity_id, record_id)
        if not delete_result.get("success"):
            return {
                "code": 500,
                "message": "删除通知失败",
                "data": {"details": delete_result.get("details")},
            }

        return {
            "code": 200,
            "message": "通知删除成功",
            "data": {
                "notification_id": record.get("notification_id") or notification_id,
                "id": record_id,
                "deleted": True,
            },
        }


class RefundService:
    """内置退款服务（示例实现，可被配置台直接引用）"""

    def get_refund_policy(self, *, request_data: Dict[str, Any], **_: Any) -> Dict[str, Any]:
        ticket_id = _first_value(request_data, "ticket_id")
        if not ticket_id:
            return {"code": 400, "message": "缺少 ticket_id", "data": None}
        ticket = _find_entity_record("ticket", {"id": ticket_id}) or _find_entity_record("ticket", {"ticket_number": ticket_id})
        if not ticket:
            return {"code": 404, "message": "车票不存在", "data": None}
        can_refund = str(ticket.get("status") or "").lower() in {"已售", "已出票", "sold", "issued"}
        departure = ticket.get("departure_date")
        if not departure:
            can_refund = False
        if departure:
            try:
                # 票面时间按本地业务时间解释，不把无时区的发车时间与 UTC 当前时间混用。
                departure_dt = datetime.fromisoformat(f"{str(departure)[:10]}T{ticket.get('departure_time') or '00:00:00'}")
                can_refund = can_refund and departure_dt - datetime.now() >= timedelta(hours=2)
            except (TypeError, ValueError):
                return {"code": 400, "message": "车票发车时间无效", "data": None}
        return {
            "code": 200,
            "message": "退票政策查询成功",
            "data": {
                "can_refund": can_refund,
                "refund_rate": 0.1,
                "refund_deadline": "开车前2小时",
                "policy_description": "开车前2小时可退，收取10%手续费",
            },
        }

    def calculate_refund(self, *, request_data: Dict[str, Any], **_: Any) -> Dict[str, Any]:
        refund_rate = _first_value(request_data, "refund_rate")
        price = _first_value(request_data, "price")
        if price is None:
            return {"code": 400, "message": "缺少 price", "data": None}
        try:
            price_value = parse_amount(price)
            rate_value = parse_amount(refund_rate if refund_rate is not None else "0.1", allow_zero=True)
            if rate_value > 1:
                raise ValueError("退款手续费率必须介于 0 和 1")
        except ValueError as exc:
            return {"code": 400, "message": str(exc), "data": None}
        # 十进制计算避免 float 舍入使手续费和退款之和偏离原价。
        quantum = Decimal("0.01")
        entity_result = entity_service.get_entity_by_name("ticket")
        if entity_result.get("success"):
            price_field = next((field for field in entity_result["data"]["entity"].fields if field.name == "price"), None)
            kind = getattr(getattr(price_field, "type", None), "value", getattr(price_field, "type", None))
            if kind in {"number", "integer"}:
                # 模板中的整数票价以最小货币单位保存，手续费也必须取整。
                quantum = Decimal("1")
        if price_value != price_value.quantize(quantum):
            return {"code": 400, "message": "票价精度与实体金额字段不一致", "data": None}
        refund_fee = (price_value * rate_value).quantize(quantum, rounding=ROUND_HALF_UP)
        refund_amount = price_value - refund_fee
        return {
            "code": 200,
            "message": "退款金额计算成功",
            "data": {
                "price": price_value,
                "refund_rate": rate_value,
                "refund_fee": refund_fee,
                "refund_amount": refund_amount,
            },
        }

    def confirm_refund(self, *, request_data: Dict[str, Any], **_: Any) -> Dict[str, Any]:
        confirm = _first_value(request_data, "confirm_refund")
        refund_reason = _first_value(request_data, "refund_reason")
        if confirm is None:
            return {"code": 400, "message": "缺少 confirm_refund", "data": None}
        try:
            confirm = parse_confirmation(confirm)
        except ValueError as exc:
            return {"code": 400, "message": str(exc), "data": None}
        return {
            "code": 200,
            "message": "退票确认成功" if bool(confirm) else "退票已取消",
            "data": {
                "confirm_refund": bool(confirm),
                "refund_reason": refund_reason,
            },
        }

    def process_refund(self, *, request_data: Dict[str, Any], **_: Any) -> Dict[str, Any]:
        ticket_id = _first_value(request_data, "ticket_id")
        refund_amount = _first_value(request_data, "refund_amount")
        if not ticket_id or refund_amount is None:
            return {"code": 400, "message": "缺少 ticket_id 或 refund_amount", "data": None}
        confirm = _first_value(request_data, "confirm_refund")
        try:
            amount = parse_amount(refund_amount)
            if confirm is not None and not parse_confirmation(confirm):
                return {"code": 409, "message": "退票已取消", "data": None}
        except ValueError as exc:
            return {"code": 400, "message": str(exc), "data": None}
        ticket = _find_entity_record("ticket", {"id": ticket_id}) or _find_entity_record("ticket", {"ticket_number": ticket_id})
        if not ticket:
            return {"code": 404, "message": "车票不存在", "data": None}
        existing = _find_entity_record("refund", {"ticket_id": ticket["id"]})
        if existing:
            if str(existing.get("status") or "").lower() in {"已完成", "completed"} and parse_amount(existing.get("refund_amount")) == amount:
                return {"code": 200, "message": "退票已处理", "data": {**existing, "refund_status": "completed", "deduplicated": True}}
            return {"code": 409, "message": "该车票已有退款记录", "data": None}
        policy = self.get_refund_policy(request_data=request_data)
        if policy["code"] != 200:
            return policy
        if not policy["data"]["can_refund"]:
            return {"code": 409, "message": "车票当前状态或发车时间不满足退票条件", "data": None}
        calculation = self.calculate_refund(request_data={"body": {"price": ticket.get("price"), "refund_rate": policy["data"]["refund_rate"]}})
        if calculation["code"] != 200:
            return calculation
        values = calculation["data"]
        if amount != values["refund_amount"]:
            return {"code": 400, "message": "退款金额与退票政策不一致", "data": None}
        record = {
            "refund_id": business_code("R", 14), "ticket_id": ticket["id"],
            "ticket_number": ticket.get("ticket_number"), "passenger_name": ticket.get("passenger_name"),
            "passenger_id_card": ticket.get("passenger_id_card"), "original_amount": values["price"],
            "refund_fee": values["refund_fee"], "refund_amount": amount,
            "refund_reason": _first_value(request_data, "refund_reason"),
            "status": "已完成", "refund_time": _db_time(datetime.utcnow()), "create_time": _db_time(datetime.utcnow()),
        }
        # 未指定的可选值让实体默认值生效，不用显式 None 覆盖配置中的退款原因。
        record = {key: value for key, value in record.items() if value is not None}
        saved = require_write(entity_service.create_entity_record(_get_entity_id("refund"), record), "退款记录保存失败")
        require_write(entity_service.update_entity_record(_get_entity_id("ticket"), ticket["id"], {"status": "已退票"}), "车票退款状态保存失败")
        return {
            "code": 200,
            "message": "退款处理完成",
            "data": {
                **saved,
                "ticket_id": ticket_id,
                "refund_amount": refund_amount,
                "refund_status": "completed",
                "refund_time": _now_iso(),
            },
        }


class TicketService:
    """模拟出票服务"""

    def _build_ticket_number(self, base_dt: datetime) -> Optional[str]:
        return business_code("T", 12)

    def purchase_ticket(self, *, request_data: Dict[str, Any], route_config: Any = None, **_: Any) -> Dict[str, Any]:
        handler_config = _normalize_handler_config(route_config)
        entity_name = handler_config.get("entity") or "ticket"
        required_fields = handler_config.get("required_fields") or []
        field_aliases = handler_config.get("field_aliases") or {}
        defaults = handler_config.get("defaults") or {}

        entity_result = entity_service.get_entity_by_name(entity_name)
        if not entity_result.get("success"):
            return {"code": 500, "message": "目标实体不存在", "data": None}

        entity = entity_result.get("data", {}).get("entity")
        fields = [field.name for field in (getattr(entity, "fields", []) or [])]
        record: Dict[str, Any] = {}

        for field_name in fields:
            value = _resolve_request_value(request_data, field_name)
            if value is None and field_name in field_aliases:
                aliases = field_aliases.get(field_name) or []
                if isinstance(aliases, str):
                    aliases = [aliases]
                for alias in aliases:
                    value = _resolve_request_value(request_data, alias)
                    if value is not None:
                        break
            if value is None and "_" in field_name:
                suffix = field_name.split("_", 1)[1]
                value = _resolve_request_value(request_data, suffix)
            if value is not None:
                record[field_name] = value

        for key, value in defaults.items():
            if key not in record and value is not None:
                resolved = _resolve_action_value(value, request_data)
                if resolved is not None:
                    record[key] = resolved

        for field_name in required_fields:
            if field_name not in record or record[field_name] is None or record[field_name] == "":
                return {"code": 400, "message": f"缺少字段: {field_name}", "data": None}

        if "ticket_number" in fields and not record.get("ticket_number"):
            record["ticket_number"] = self._build_ticket_number(datetime.utcnow())
        if "purchase_time" in fields and not record.get("purchase_time"):
            record["purchase_time"] = _db_time(datetime.utcnow())
        if "status" in fields and not record.get("status"):
            record["status"] = handler_config.get("default_status") or "已售"

        ticket_entity_id = _get_entity_id(entity_name)
        if not ticket_entity_id:
            return {"code": 500, "message": "实体不可用", "data": None}
        create_result = entity_service.create_entity_record(ticket_entity_id, record)
        if not create_result.get("success"):
            return {
                "code": 500,
                "message": "创建记录失败",
                "data": {"details": create_result.get("details")},
            }

        post_actions = handler_config.get("post_actions") or []
        if post_actions:
            _execute_post_actions(post_actions, request_data)

        data = create_result.get("data", {}).get("record") or record
        return {"code": 200, "message": "操作成功", "data": data}


service_registry = get_service_registry()
service_registry.register(
    "payment_service",
    PaymentService(),
    display_name="支付服务",
    description="内置支付服务示例",
)
service_registry.register(
    "notification_service",
    NotificationService(),
    display_name="通知服务",
    description="内置通知服务示例",
)
service_registry.register(
    "refund_service",
    RefundService(),
    display_name="退款服务",
    description="内置退款服务",
)
service_registry.register(
    "ticket_service",
    TicketService(),
    display_name="出票服务",
    description="内置出票服务",
)


async def dispatch_service_call(
    service_name: str,
    method_name: str,
    *,
    request_data: Dict[str, Any],
    route_config: Any = None,
    request: Any = None,
) -> Dict[str, Any]:
    service = service_registry.get(service_name)
    if not service:
        return {"code": 501, "message": f"未注册的服务: {service_name}", "data": None}

    method = getattr(service, method_name, None) if not method_name.startswith("_") else None
    if not method or not callable(method):
        return {
            "code": 501,
            "message": f"服务方法未实现: {service_name}.{method_name}",
            "data": None,
        }

    async def invoke():
        result = method(request_data=request_data, route_config=route_config, request=request)
        return await result if inspect.isawaitable(result) else result

    # 内置业务的主记录、订单更新及后置动作必须同时成功，不能分散成多次提交。
    if isinstance(service, (PaymentService, RefundService, TicketService, NotificationService)):
        try:
            with business_transaction():
                result = await invoke()
                if response_error(result):
                    raise BusinessOperationError(result.get("message") or "业务操作失败", code=result.get("code", 500), data=result.get("data"))
                return result
        except BusinessOperationError as exc:
            return exc.response
        except Exception:
            return {"code": 500, "message": "业务提交失败，已撤销本次操作", "data": None}
    return await invoke()
