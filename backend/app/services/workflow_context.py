"""工作流共享的上下文寻址、模板替换和业务响应解析；不执行用户表达式。"""
import json
import re
from typing import Any, Dict


def bind_workflow_schema(schema, session, node_id):
    """入口和后续表单都绑定实例，旧页面提交时不能混入重新开始后的流程。"""
    from copy import deepcopy
    if not isinstance(schema, dict):
        raise ValueError("工作流界面必须是对象")
    schema = deepcopy(schema)
    controls = {"workflow_id": session.workflow_id, "node_id": node_id, "instance_id": session.id}
    schema.update({"workflow_id": session.workflow_id, "current_node_id": node_id, "instance_id": session.id})

    def attach(value):
        if isinstance(value, dict):
            api = value.get("api")
            if isinstance(api, str) and "/workflow/state" in api:
                method, separator, url = api.partition(":")
                api = {"method": method, "url": url} if separator and method.lower() in {
                    "get", "post", "put", "patch", "delete"
                } else {"method": "post", "url": api}
                value["api"] = api
            if isinstance(api, dict) and "/workflow/state" in str(api.get("url", "")):
                data = api.get("data")
                if not isinstance(data, dict):
                    # AMIS 的 & 表示展开原始数据，兼容字符串表达式而不丢表单字段。
                    data = {"&": data if isinstance(data, str) and data else "$"}
                api["data"] = {**data, **controls}
                api["data"].setdefault("action", "submit" if value.get("type") == "form" else "next")
            for child in value.values():
                attach(child)
        elif isinstance(value, list):
            for child in value:
                attach(child)
    attach(schema)
    return schema

MISSING = object()


def _read_path(data: Any, path: str):
    """支持 result.items[0].id，也保留历史数据中带点号的完整字段名。"""
    if isinstance(data, dict) and path in data:
        return data[path]
    tokens = re.sub(r"\[(\d+)\]", r".\1", path).split(".")
    value = data
    for token in tokens:
        if isinstance(value, dict) and token in value:
            value = value[token]
        elif isinstance(value, (list, tuple)) and token.isdigit() and int(token) < len(value):
            value = value[int(token)]
        else:
            return MISSING
    return value


def resolve_context_value(path: str, data: Dict[str, Any], default=None):
    """先查精确路径，再兼容 input 和旧节点名_result 命名空间。"""
    value = _read_path(data, path)
    if value is not MISSING:
        return value
    if path.startswith("input.") and "input" not in data:
        value = _read_path(data, path[6:])
    elif "." in path:
        namespace, field = path.split(".", 1)
        # 命名空间存在时不借用其他节点的数据，空值或缺失字段也必须保持原意。
        if namespace in data:
            return default
        for candidate in (f"{namespace}_result", f"n_{namespace}_result"):
            value = _read_path(data.get(candidate), field)
            if value is not MISSING:
                return value
        for key, payload in data.items():
            if key.endswith(f"{namespace}_result"):
                value = _read_path(payload, field)
                if value is not MISSING:
                    return value
        value = _read_path(data, field)
        if value is MISSING and "_" in field:
            value = _read_path(data, field.split("_", 1)[1])
    else:
        for payload in (data.get("api_response"), data.get("last_api_result")):
            if isinstance(payload, dict):
                value = _read_path(payload.get("data", payload), path)
                if value is not MISSING:
                    return value
    return default if value is MISSING else value


def resolve_templates(value: Any, data: Dict[str, Any]) -> Any:
    """纯变量保留布尔、数字、列表等原类型；字符串中的变量按文本替换。"""
    if isinstance(value, dict):
        return {key: resolve_templates(item, data) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_templates(item, data) for item in value]
    if not isinstance(value, str):
        return value
    exact = re.fullmatch(r"\$\{([^}]+)\}", value)
    if exact:
        return resolve_context_value(exact.group(1), data)

    def replace(match):
        resolved = resolve_context_value(match.group(1), data, MISSING)
        if resolved is MISSING:
            return match.group(0)
        if isinstance(resolved, (dict, list, bool)) or resolved is None:
            return json.dumps(resolved, ensure_ascii=False, default=str)
        return str(resolved)

    return re.sub(r"\$\{([^}]+)\}", replace, value)

def response_error(payload):
    """同时识别统一响应和 AMIS 的失败包裹，避免 HTTP 200 被误当成业务成功。"""
    if not isinstance(payload, dict):
        return None
    if payload.get("success") is False:
        return str(payload.get("message") or payload.get("msg") or "业务操作失败")
    code = payload.get("code")
    if code is not None:
        try:
            code = int(code)
        except (TypeError, ValueError):
            return "业务 API 返回了无效状态码"
        if code != 0 and not 200 <= code < 300:
            return str(payload.get("message") or payload.get("msg") or f"业务 API 返回错误 {code}")
    if isinstance(payload.get("status"), (int, float)) and not isinstance(payload["status"], bool) and "msg" in payload:
        if payload["status"] != 0:
            return str(payload.get("msg") or "业务操作失败")
    return None


def unwrap_response(payload):
    """只拆已知响应包裹的 data，普通业务对象中的 data 字段仍保留。"""
    if isinstance(payload, dict) and "data" in payload and (
        "code" in payload or "msg" in payload or "success" in payload
    ):
        return payload["data"]
    return payload
