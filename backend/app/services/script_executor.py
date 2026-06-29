"""
Lightweight script executor for dynamic API routes.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from app.services.entity_service import EntityService


SAFE_BUILTINS = {
    "isinstance": isinstance,
    "len": len,
    "min": min,
    "max": max,
    "sum": sum,
    "sorted": sorted,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "dict": dict,
    "list": list,
    "set": set,
    "tuple": tuple,
    "abs": abs,
    "round": round,
}

_entity_service = EntityService()


def _get_entity_id(entity_name: str) -> Optional[str]:
    result = _entity_service.get_entity_by_name(entity_name)
    if not result.get("success"):
        return None
    entity = result.get("data", {}).get("entity")
    return getattr(entity, "id", None) if entity else None


def entity_list(
    entity_name: str,
    *,
    filters: Optional[Dict[str, Any]] = None,
    page: int = 1,
    limit: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
) -> Dict[str, Any]:
    entity_id = _get_entity_id(entity_name)
    if not entity_id:
        return {"success": False, "error": "entity_not_found", "details": f"实体 {entity_name} 不存在"}
    return _entity_service.get_entity_records(
        entity_id,
        page=page,
        limit=limit,
        filters=filters,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def entity_find_one(entity_name: str, *, filters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    result = entity_list(entity_name, filters=filters, page=1, limit=1)
    if not result.get("success"):
        return None
    records = result.get("data", {}).get("records") or []
    return records[0] if records else None


def entity_create(entity_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    entity_id = _get_entity_id(entity_name)
    if not entity_id:
        return {"success": False, "error": "entity_not_found", "details": f"实体 {entity_name} 不存在"}
    return _entity_service.create_entity_record(entity_id, data)


def entity_update(entity_name: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    entity_id = _get_entity_id(entity_name)
    if not entity_id:
        return {"success": False, "error": "entity_not_found", "details": f"实体 {entity_name} 不存在"}
    return _entity_service.update_entity_record(entity_id, record_id, data)


def execute_script(script: str, context: Dict[str, Any]) -> Dict[str, Any]:
    if not script:
        return {"code": 400, "message": "Missing script", "data": None}

    env: Dict[str, Any] = {
        "__builtins__": SAFE_BUILTINS,
        "now": lambda: datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "context": context,
        "request": context.get("request"),
        "path": context.get("path"),
        "query": context.get("query"),
        "body": context.get("body"),
        "headers": context.get("headers"),
        "entity_list": entity_list,
        "entity_find_one": entity_find_one,
        "entity_create": entity_create,
        "entity_update": entity_update,
    }
    local_vars: Dict[str, Any] = {}

    try:
        exec(script, env, local_vars)
    except Exception as exc:
        return {"code": 500, "message": "Script execution failed", "data": {"error": str(exc)}}

    result = local_vars.get("result", env.get("result"))
    response = local_vars.get("response", env.get("response"))
    if isinstance(response, dict):
        return response
    if isinstance(result, dict) and "code" in result and "message" in result:
        return result
    return {"code": 200, "message": "Script executed", "data": result}
