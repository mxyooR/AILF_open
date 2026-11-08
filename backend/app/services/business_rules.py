"""内置示例业务共用的金额、确认值和事务失败规则。"""
from decimal import Decimal, InvalidOperation
import secrets


def business_code(prefix, digits):
    """保留已部署实体的 P/R+14 位、T+12 位格式，随机数字降低同秒并发冲突。

    数据库的唯一约束仍负责最终校验，编号不作为访问凭据。
    """
    return prefix + str(secrets.randbelow(10 ** digits)).zfill(digits)


class BusinessOperationError(Exception):
    """把业务失败带出事务边界，回滚后再转换成原有响应格式。"""
    def __init__(self, message, *, code=500, data=None):
        super().__init__(message)
        self.response = {"code": code, "message": message, "data": data}


def parse_amount(value, *, allow_zero=False):
    """金额以数据库配置的单位计算，禁止负数、布尔和 NaN/Infinity；不猜测元或分。"""
    if isinstance(value, bool):
        raise ValueError("金额必须是有效数字")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("金额必须是有效数字") from exc
    if not number.is_finite() or number < 0 or (number == 0 and not allow_zero):
        raise ValueError("金额必须为非负数" if allow_zero else "金额必须大于零")
    return number


def parse_confirmation(value):
    """HTTP 表单中的 false/0 不能用 bool(str) 转换，否则取消退票会被当成确认。"""
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.strip().lower() in {"true", "false", "1", "0", "yes", "no"}:
        return value.strip().lower() in {"true", "1", "yes"}
    raise ValueError("确认值必须是布尔值")


def require_write(result, message):
    """任何关联记录写入失败都要中止整笔业务，不能返回部分成功。"""
    if not result.get("success"):
        raise BusinessOperationError(message)
    return result.get("data", {}).get("record") or {}


def requester_id(request, fallback=None):
    """真实 HTTP 请求只能使用认证中间件的身份；内部工作流允许显式指定接收者。"""
    if request is None:
        return fallback
    state = getattr(request, "state", None)
    info = getattr(state, "user_info", None) or {}
    if info.get("user_type") == "developer":
        return fallback
    identity = info.get("user_id") or getattr(state, "user_id", None)
    if identity is None:
        raise BusinessOperationError("请先登录", code=401)
    return identity
