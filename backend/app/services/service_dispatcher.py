"""
服务分发器
- 为 custom_function 处理器提供 service/method 调用入口
- 默认提供 payment_service / notification_service 的示例实现
"""
from __future__ import annotations

import inspect
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.services.service_registry import get_service_registry
from app.services.entity_service import entity_service


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


def _find_entity_record(entity_name: str, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    entity_id = _get_entity_id(entity_name)
    if not entity_id:
        return None
    result = entity_service.get_entity_records(entity_id, page=1, limit=1, filters=filters)
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
    return results


class PaymentService:
    """示例支付服务（模拟实现）"""

    def _build_payment_id(self, base_dt: datetime) -> Optional[str]:
        for offset in range(10):
            candidate_dt = base_dt + timedelta(seconds=offset)
            payment_id = f"P{candidate_dt.strftime('%Y%m%d%H%M%S')}"
            if not _find_entity_record("payment", {"payment_id": payment_id}):
                return payment_id
        return None

    def refund_payment(self, *, request_data: Dict[str, Any], **_: Any) -> Dict[str, Any]:
        payment_id = _first_value(request_data, "payment_id")
        refund_amount = _first_value(request_data, "refund_amount")
        refund_reason = _first_value(request_data, "refund_reason")

        if not payment_id:
            return {"code": 400, "message": "缺少 payment_id", "data": None}
        if refund_amount is None:
            return {"code": 400, "message": "缺少 refund_amount", "data": None}

        return {
            "code": 200,
            "message": "退款请求已受理",
            "data": {
                "refund_id": f"refund_{uuid.uuid4().hex[:12]}",
                "payment_id": payment_id,
                "refund_amount": refund_amount,
                "refund_reason": refund_reason,
                "refund_status": "processing",
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
        if amount is None:
            amount = order.get("total_amount") or 0
        try:
            amount_value = float(amount)
        except Exception:
            amount_value = 0.0

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
            entity_service.update_entity_record(
                order_entity_id,
                order["id"],
                {"order_status": "已支付", "payment_time": create_time, "payment_method": payment_method},
            )

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
        status = _first_value(request_data, "status") or _first_value(request_data, "trade_status") or "paid"

        normalized = str(status).lower()
        paid_statuses = {"success", "paid", "trade_success", "支付成功", "已支付"}
        new_status = "已支付" if normalized in paid_statuses else "支付失败"

        payment = None
        if payment_id:
            payment = _find_entity_record("payment", {"payment_id": payment_id}) or _find_entity_record(
                "payment", {"id": payment_id}
            )
        if not payment and transaction_id:
            payment = _find_entity_record("payment", {"transaction_id": transaction_id})
        if not payment and order_id:
            payment = _find_entity_record("payment", {"order_id": order_id}) or _find_entity_record(
                "payment", {"order_number": order_id}
            )

        now_time = _db_time(datetime.utcnow())
        payment_entity_id = _get_entity_id("payment")
        if payment:
            record_id = payment.get("id") or payment.get("payment_id")
            updates = {"status": new_status, "transaction_id": transaction_id}
            if new_status == "已支付":
                updates["payment_time"] = now_time
            if payment_entity_id and record_id:
                entity_service.update_entity_record(payment_entity_id, record_id, updates)
        else:
            if not payment_id:
                payment_id = self._build_payment_id(datetime.utcnow()) or f"P{_digits_from_datetime(datetime.utcnow())[:14]}"
            record = {
                "payment_id": payment_id,
                "order_id": order_id,
                "order_number": payload.get("order_number") or order_id,
                "amount": payload.get("amount") or 0,
                "payment_method": payload.get("payment_method") or "支付宝",
                "transaction_id": transaction_id,
                "status": new_status,
                "payment_time": now_time if new_status == "已支付" else None,
                "expire_time": None,
                "create_time": now_time,
            }
            if payment_entity_id:
                entity_service.create_entity_record(payment_entity_id, record)

        order_entity_id = _get_entity_id("order")
        if order_entity_id and order_id:
            order = _find_entity_record("order", {"id": order_id}) or _find_entity_record(
                "order", {"order_number": order_id}
            )
            if order and order.get("id"):
                order_status = "已支付" if new_status == "已支付" else "支付失败"
                updates = {"order_status": order_status}
                if new_status == "已支付":
                    updates["payment_time"] = now_time
                entity_service.update_entity_record(order_entity_id, order["id"], updates)

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
            return True
        return uid in owner_values

    def send_notification(self, *, request_data: Dict[str, Any], route_config: Any = None, **_: Any) -> Dict[str, Any]:
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

        notification_id = f"notify_{uuid.uuid4().hex[:12]}"
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
        strict_persist = bool(handler_config.get("strict_persist", False))

        if persist_enabled:
            entity_id = _get_entity_id(entity_name)
            field_names = _get_entity_field_names(entity_name)
            if entity_id and field_names:
                idempotency_field = next(
                    (f for f in ("idempotency_key", "biz_key", "request_id") if f in field_names),
                    None
                )

                if idempotency_key and idempotency_field:
                    dedupe_filters: Dict[str, Any] = {idempotency_field: idempotency_key}
                    user_field = next((f for f in ("user_id", "receiver_id", "target_user_id") if f in field_names), None)
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
                    "发送时间": sent_at,
                    "created_at": _db_time(datetime.utcnow()),
                    "create_time": _db_time(datetime.utcnow()),
                    "is_read": False,
                    "read": False,
                    "是否已读": False,
                    "读取时间": None,
                }
                if idempotency_key and idempotency_field:
                    candidate_fields[idempotency_field] = idempotency_key

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

    def list_notifications(self, *, request_data: Dict[str, Any], route_config: Any = None, **_: Any) -> Dict[str, Any]:
        handler_config = _normalize_handler_config(route_config)
        entity_name = handler_config.get("entity") or "notification"
        entity_id = _get_entity_id(entity_name)
        if not entity_id:
            return {"code": 500, "message": f"通知实体不存在: {entity_name}", "data": None}

        user_id = (
            _first_value(request_data, "user_id")
            or _first_value(request_data, "receiver_id")
            or _first_value(request_data, "target_user_id")
        )
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
            user_field = next((f for f in ("user_id", "receiver_id", "target_user_id") if f in field_names), None)
            if user_field:
                filters[user_field] = user_id

        records_result = entity_service.get_entity_records(entity_id, page=page, limit=limit, filters=filters or None)
        if not records_result.get("success"):
            return {
                "code": 500,
                "message": "查询通知列表失败",
                "data": {"details": records_result.get("details")},
            }

        data = records_result.get("data", {})
        records = data.get("records") or []
        unread_count = 0
        for record in records:
            if not isinstance(record, dict):
                continue
            status = str(record.get("status") or "").lower()
            is_read = record.get("is_read")
            read_flag = record.get("read")
            if status in {"read", "已读"} or is_read is True or read_flag is True:
                continue
            unread_count += 1

        return {
            "code": 200,
            "message": "通知列表查询成功",
            "data": {
                "items": records,
                "total": data.get("total", len(records)),
                "page": data.get("page", page),
                "limit": data.get("limit", limit),
                "has_next": data.get("has_next", False),
                "has_prev": data.get("has_prev", False),
                "unread_count": unread_count,
            },
        }

    def mark_as_read(self, *, request_data: Dict[str, Any], route_config: Any = None, **_: Any) -> Dict[str, Any]:
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

    def delete_notification(self, *, request_data: Dict[str, Any], route_config: Any = None, **_: Any) -> Dict[str, Any]:
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

        return {
            "code": 200,
            "message": "退票政策查询成功",
            "data": {
                "can_refund": True,
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
            price_value = float(price)
        except Exception:
            return {"code": 400, "message": "price 格式错误", "data": None}

        try:
            rate_value = float(refund_rate) if refund_rate is not None else 0.0
        except Exception:
            rate_value = 0.0

        refund_fee = round(price_value * rate_value, 2)
        refund_amount = round(price_value - refund_fee, 2)
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
        return {
            "code": 200,
            "message": "退款处理完成",
            "data": {
                "ticket_id": ticket_id,
                "refund_amount": refund_amount,
                "refund_status": "completed",
                "refund_time": _now_iso(),
            },
        }


class TicketService:
    """模拟出票服务"""

    def _build_ticket_number(self, base_dt: datetime) -> Optional[str]:
        for offset in range(10):
            candidate_dt = base_dt + timedelta(seconds=offset)
            ticket_number = f"T{candidate_dt.strftime('%y%m%d%H%M%S')}"
            if not _find_entity_record("ticket", {"ticket_number": ticket_number}):
                return ticket_number
        return None

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
            if field_name not in record:
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

    method = getattr(service, method_name, None)
    if not method or not callable(method):
        return {
            "code": 501,
            "message": f"服务方法未实现: {service_name}.{method_name}",
            "data": None,
        }

    result = method(request_data=request_data, route_config=route_config, request=request)
    if inspect.isawaitable(result):
        result = await result
    return result
