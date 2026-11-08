"""实体字段的统一转换规则，供配置校验、管理接口和动态业务 API 共用。"""
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import math
import re

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, Text
from sqlalchemy.sql import literal


def field_type(field):
    """统一 Pydantic 枚举和 ORM 字符串形式的字段类型。"""
    value = getattr(field, "type", "")
    return str(getattr(value, "value", value)).lower()


def validate_identifier(name, *, max_length=64):
    if not isinstance(name, str) or len(name) > max_length or not re.fullmatch(r"[^\W\d]\w*", name, re.UNICODE):
        raise ValueError(f"名称必须以字母或下划线开头，只能包含字母、数字、中文和下划线，最长 {max_length} 字符")
    return name


def validation_rules(field):
    """把配置模型和数据库字典转换为相同的规则字典。"""
    rules = getattr(field, "validation", None)
    return rules.model_dump(exclude_none=True) if hasattr(rules, "model_dump") else (rules or {})


def normalize_field_value(field, value):
    """创建和更新共用的值转换：保留合法零值，拒绝损失精度或非法类型。"""
    if value is None:
        return None
    kind = field_type(field)
    if kind in {"json", "multiselect"}:
        if isinstance(value, str):
            value = json.loads(value)
        if not isinstance(value, (dict, list)) or (kind == "multiselect" and not isinstance(value, list)):
            raise ValueError("需要 JSON 对象或列表" if kind == "json" else "多选字段需要列表")
        options = getattr(field, "options", None)
        if kind == "multiselect" and options and any(item not in options for item in value):
            raise ValueError("多选值不在允许的选项中")
        return value
    if kind == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)) and value in (0, 1):
            return bool(value)
        if isinstance(value, str) and value.strip().lower() in {"true", "false", "1", "0", "yes", "no"}:
            return value.strip().lower() in {"true", "1", "yes"}
        raise ValueError("需要布尔值")
    if kind in {"number", "integer", "decimal", "float"}:
        if isinstance(value, bool):
            raise ValueError("数字字段不能使用布尔值")
        try:
            number = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError("需要有效数字") from exc
        if not number.is_finite():
            raise ValueError("数字必须有限")
        if kind in {"number", "integer"}:
            if number != number.to_integral_value():
                raise ValueError("整数字段不能丢弃小数部分")
            return int(number)
        if kind == "float":
            return float(number)
        precision = validation_rules(field).get("precision", 2)
        if precision is None:
            precision = 2
        if number != number.quantize(Decimal(1).scaleb(-int(precision))):
            raise ValueError(f"小数最多保留 {precision} 位")
        return number
    if kind == "date":
        if isinstance(value, (int, float)):
            value = datetime.fromtimestamp(value, timezone.utc).date()
        if isinstance(value, datetime):
            value = value.date()
        if isinstance(value, str):
            value = date.fromisoformat(value.strip().split("T")[0].split(" ")[0])
        if not isinstance(value, date):
            raise ValueError("需要有效日期")
        return value.isoformat()
    if kind in {"datetime", "timestamp"}:
        if isinstance(value, (int, float)):
            value = datetime.fromtimestamp(value, timezone.utc)
        if isinstance(value, str):
            value = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if not isinstance(value, datetime):
            raise ValueError("需要有效日期时间")
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if not isinstance(value, str):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            value = str(value)
        else:
            raise ValueError("需要文本值")
    if kind == "select" and getattr(field, "options", None) and value not in field.options:
        raise ValueError("值不在允许的选项中")
    return value


def storage_value(field, value):
    """把已校验的值转换为数据库参数，JSON 编码仅在落库前执行。"""
    value = normalize_field_value(field, value)
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, Decimal):
        return format(value, "f")
    return value


def serialize_default(value):
    """默认值不能按真假判断，False、0 和空列表都需要保存。"""
    if value is None:
        return None
    if isinstance(value, (dict, list, bool)):
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    return str(value)


def default_value(field):
    """兼容配置端 defaultValue 和 ORM default_value 两种命名。"""
    raw = getattr(field, "defaultValue", getattr(field, "default_value", None))
    return normalize_field_value(field, raw) if raw is not None else None


def decode_record(record, fields):
    """读取时恢复布尔和 JSON 类型，使管理接口与业务 API 返回一致。"""
    result = dict(record)
    for field in fields:
        key = field.name
        value = result.get(key)
        if value is None:
            continue
        kind = field_type(field)
        if kind in {"json", "multiselect"} and isinstance(value, str):
            try:
                result[key] = json.loads(value)
            except (TypeError, ValueError):
                pass  # 旧的非 JSON 文本仍返回，方便在配置界面修复历史数据。
        elif kind == "boolean":
            result[key] = normalize_field_value(field, value)
        elif isinstance(value, (date, datetime)):
            result[key] = value.isoformat()
    for key in ("created_at", "updated_at"):
        if isinstance(result.get(key), (date, datetime)):
            result[key] = result[key].isoformat()
    return result


def sql_field_type(field):
    """统一建表和改表的 SQL 类型，小数字段的 precision 表示小数位数。"""
    kind = field_type(field)
    if kind in {"number", "integer"}:
        return Integer()
    if kind in {"decimal", "float"}:
        precision = validation_rules(field).get("precision", 2)
        return Numeric(20, int(precision if precision is not None else 2))
    return {
        "boolean": Boolean(), "date": Date(), "datetime": DateTime(), "timestamp": DateTime(),
        "json": JSON(), "multiselect": JSON(), "reference": String(36),
        "select": String(100), "phone": String(20), "file": String(2048), "image": String(2048),
        "url": String(2048),
    }.get(kind, String(255))


def sql_type_signature(column_type, dialect):
    """比较保留列与新字段类型，统一 MySQL 反射返回的同义类型名称。"""
    rendered = str(column_type.compile(dialect=dialect)).upper()
    if dialect.name == "mysql":
        rendered = re.sub(r"\bNUMERIC\b", "DECIMAL", rendered)
        rendered = re.sub(r"\b(?:BOOL|BOOLEAN)\b", "TINYINT(1)", rendered)
        rendered = re.sub(r"\b(?:INTEGER|INT)(?:\(\d+\))?", "INTEGER", rendered)
    return rendered


def sql_default(field, dialect):
    """由 SQLAlchemy 转义默认值；MySQL 8 的 JSON 默认值需要表达式括号。"""
    value = default_value(field)
    if value is None:
        return None
    encoded = storage_value(field, value)
    rendered = str(literal(encoded).compile(dialect=dialect, compile_kwargs={"literal_binds": True}))
    # 这里随后会作为 text 再编译为 DDL，先撤销一次 DBAPI 百分号转义，避免默认值被翻倍。
    if dialect.paramstyle in {"format", "pyformat"}:
        rendered = rendered.replace("%%", "%")
    if field_type(field) in {"json", "multiselect"} and dialect.name == "mysql":
        rendered = f"({rendered})"
    return rendered
