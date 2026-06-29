"""
动态响应引擎 - 支持复杂的条件响应逻辑
"""
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from fastapi import Request
from sqlalchemy.orm import Session

from app.core.database import get_db_session


class ResponseCondition:
    """响应条件类"""
    
    def __init__(self, condition_config: Dict[str, Any]):
        self.type = condition_config.get("type")  # parameter, header, user_role, time, random
        self.field = condition_config.get("field")  # 兼容旧格式
        self.field_name = condition_config.get("field_name") or condition_config.get("name")  # 新格式，支持数据库存储 + 兼容 name 字段
        self.operator = condition_config.get("operator")  # eq, ne, gt, lt, in, contains, exists
        self.value = condition_config.get("value")
        self.logic = condition_config.get("logic", "and")  # and, or

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """评估条件是否满足"""
        try:
            if self.type == "parameter":
                return self._evaluate_parameter(context)
            elif self.type == "header":
                return self._evaluate_header(context)
            elif self.type == "user_role":
                return self._evaluate_user_role(context)
            elif self.type == "time":
                return self._evaluate_time(context)
            elif self.type == "random":
                return self._evaluate_random(context)
            elif self.type == "data_count":
                return self._evaluate_data_count(context)
            else:
                return True
        except Exception as e:
            print(f"⚠️ 条件评估失败: {e}")
            return False

    def _evaluate_parameter(self, context: Dict[str, Any]) -> bool:
        """评估参数条件"""
        request_data = context.get("request_data", {})
        param_value = None
        
        # 从不同位置获取参数值
        field_name = self.field or getattr(self, 'field_name', None)
        if field_name:
            param_value = (
                request_data.get("query", {}).get(field_name) or
                request_data.get("path", {}).get(field_name) or
                request_data.get("body", {}).get(field_name) or
                request_data.get("form", {}).get(field_name)
            )
        
        return self._compare_values(param_value, self.operator, self.value)

    def _evaluate_header(self, context: Dict[str, Any]) -> bool:
        """评估头部条件"""
        headers = context.get("request_data", {}).get("header", {})
        field_name = self.field or self.field_name
        header_value = headers.get(field_name)
        return self._compare_values(header_value, self.operator, self.value)

    def _evaluate_user_role(self, context: Dict[str, Any]) -> bool:
        """评估用户角色条件"""
        user_roles = context.get("user_roles", [])
        print(f"🔍 用户角色评估: 当前角色={user_roles}, 期望值={self.value}, 操作符={self.operator}")
        
        if self.operator == "eq":
            # 等于：检查用户是否具有指定角色
            return self.value in user_roles
        elif self.operator == "ne":
            # 不等于：检查用户是否不具有指定角色
            return self.value not in user_roles
        elif self.operator == "in":
            # 包含在：检查用户角色是否在期望的角色列表中
            if isinstance(self.value, list):
                return any(role in self.value for role in user_roles)
            else:
                return self.value in user_roles
        elif self.operator == "not_in":
            if isinstance(self.value, list):
                return not any(role in self.value for role in user_roles)
            else:
                return self.value not in user_roles
        else:
            return len(user_roles) > 0

    def _evaluate_time(self, context: Dict[str, Any]) -> bool:
        """评估时间条件"""
        current_time = time.time()
        current_hour = int(time.strftime("%H"))
        
        field_name = self.field or self.field_name or "hour"
        if field_name == "hour":
            return self._compare_values(current_hour, self.operator, self.value)
        elif field_name == "timestamp":
            return self._compare_values(current_time, self.operator, self.value)
        else:
            return True

    def _evaluate_random(self, context: Dict[str, Any]) -> bool:
        """评估随机条件"""
        import random
        random_value = random.random() * 100
        return self._compare_values(random_value, self.operator, self.value)

    def _evaluate_data_count(self, context: Dict[str, Any]) -> bool:
        """评估数据数量条件"""
        data = context.get("result_data", {}).get("data", [])
        count = len(data) if isinstance(data, list) else (1 if data else 0)
        return self._compare_values(count, self.operator, self.value)

    def _compare_values(self, actual: Any, operator: str, expected: Any) -> bool:
        """比较值"""
        try:
            print(f"🔍 比较值: {actual} {operator} {expected}")
            
            if operator == "eq":
                result = str(actual) == str(expected)
            elif operator == "ne":
                result = str(actual) != str(expected)
            elif operator == "gt":
                result = float(actual) > float(expected)
            elif operator == "gte":
                result = float(actual) >= float(expected)
            elif operator == "lt":
                result = float(actual) < float(expected)
            elif operator == "lte":
                result = float(actual) <= float(expected)
            elif operator == "in":
                if isinstance(expected, list):
                    result = actual in expected
                else:
                    result = str(expected) in str(actual)
            elif operator == "not_in":
                if isinstance(expected, list):
                    result = actual not in expected
                else:
                    result = str(expected) not in str(actual)
            elif operator == "contains":
                result = str(expected) in str(actual)
            elif operator == "between":
                if isinstance(expected, (list, tuple)) and len(expected) >= 2:
                    lower = float(expected[0])
                    upper = float(expected[1])
                    result = lower <= float(actual) <= upper
                else:
                    result = False
            elif operator == "exists":
                result = actual is not None and actual != ""
            elif operator == "not_exists":
                result = actual is None or actual == ""
            else:
                result = True
            
            print(f"✅ 比较结果: {result}")
            return result
        except Exception as e:
            print(f"❌ 值比较失败: {e}")
            return False


class ResponseTemplate:
    """响应模板类"""
    
    def __init__(self, template_config: Dict[str, Any]):
        self.status_code = template_config.get("status_code", 200)
        self.headers = template_config.get("headers", {})
        self.body_template = template_config.get("body_template", {})
        self.transformations = template_config.get("transformations", [])

    def render(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """渲染响应模板"""
        try:
            # 复制模板避免修改原始配置
            response_body = self._deep_copy(self.body_template)
            
            # 应用数据变换
            for transformation in self.transformations:
                response_body = self._apply_transformation(response_body, transformation, context)
            
            # 变量替换
            response_body = self._substitute_variables(response_body, context)
            
            return {
                "status_code": self.status_code,
                "headers": self.headers,
                "body": response_body
            }
        except Exception as e:
            print(f"⚠️ 模板渲染失败: {e}")
            return {
                "status_code": 500,
                "headers": {},
                "body": {"error": f"模板渲染失败: {str(e)}"}
            }

    def _apply_transformation(self, data: Any, transformation: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """应用数据变换"""
        transform_type = transformation.get("type")
        
        if transform_type == "filter":
            return self._filter_data(data, transformation.get("condition", {}), context)
        elif transform_type == "sort":
            return self._sort_data(data, transformation.get("field"), transformation.get("order", "asc"))
        elif transform_type == "limit":
            return self._limit_data(data, transformation.get("count", 10))
        elif transform_type == "aggregate":
            return self._aggregate_data(data, transformation.get("operation"), transformation.get("field"))
        elif transform_type == "format":
            return self._format_data(data, transformation.get("format"))
        else:
            return data

    def _filter_data(self, data: Any, condition: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """过滤数据"""
        if not isinstance(data, list):
            return data
        
        filtered_data = []
        for item in data:
            # 创建临时上下文用于条件评估
            temp_context = {**context, "current_item": item}
            condition_obj = ResponseCondition(condition)
            if condition_obj.evaluate(temp_context):
                filtered_data.append(item)
        
        return filtered_data

    def _sort_data(self, data: Any, field: str, order: str = "asc") -> Any:
        """排序数据"""
        if not isinstance(data, list) or not field:
            return data
        
        reverse = order.lower() == "desc"
        try:
            return sorted(data, key=lambda x: x.get(field, 0), reverse=reverse)
        except Exception:
            return data

    def _limit_data(self, data: Any, count: int) -> Any:
        """限制数据数量"""
        if isinstance(data, list):
            return data[:count]
        return data

    def _aggregate_data(self, data: Any, operation: str, field: str) -> Any:
        """聚合数据"""
        if not isinstance(data, list):
            return data
        
        try:
            if operation == "count":
                return len(data)
            elif operation == "sum":
                return sum(item.get(field, 0) for item in data)
            elif operation == "avg":
                values = [item.get(field, 0) for item in data]
                return sum(values) / len(values) if values else 0
            elif operation == "max":
                return max(item.get(field, 0) for item in data)
            elif operation == "min":
                return min(item.get(field, 0) for item in data)
        except Exception:
            pass
        
        return data

    def _format_data(self, data: Any, format_config: Dict[str, Any]) -> Any:
        """格式化数据"""
        if format_config.get("type") == "currency":
            if isinstance(data, (int, float)):
                symbol = format_config.get("symbol", "¥")
                return f"{symbol}{data:.2f}"
        elif format_config.get("type") == "date":
            if isinstance(data, str):
                import datetime
                try:
                    dt = datetime.datetime.fromisoformat(data)
                    format_str = format_config.get("format", "%Y-%m-%d %H:%M:%S")
                    return dt.strftime(format_str)
                except Exception:
                    pass
        
        return data

    def _substitute_variables(self, data: Any, context: Dict[str, Any]) -> Any:
        """替换变量"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                result[key] = self._substitute_variables(value, context)
            return result
        elif isinstance(data, list):
            return [self._substitute_variables(item, context) for item in data]
        elif isinstance(data, str):
            # 替换变量占位符
            result = data
            
            # 获取原始数据
            original_data = context.get("result_data", {}).get("data", [])
            user_roles = context.get("user_roles", [])
            
            variables = {
                "{{timestamp}}": time.strftime('%Y-%m-%d %H:%M:%S'),
                "{{request_id}}": str(uuid.uuid4()),
                "{{user_id}}": str(context.get("user_id", "unknown")),
                "{{api_id}}": str(context.get("api_id", "unknown")),
                "{{data_count}}": str(len(original_data) if isinstance(original_data, list) else (1 if original_data else 0)),
                "{{user_role}}": str(user_roles[0] if user_roles else "guest"),
                "{{original_data}}": json.dumps(original_data, ensure_ascii=False) if original_data != "{{original_data}}" else original_data,
            }
            
            # 特殊处理 {{original_data}} - 如果整个字符串就是这个变量，直接返回数据
            if result == "{{original_data}}":
                return original_data
            
            for var, val in variables.items():
                result = result.replace(var, str(val))
            
            return result
        else:
            return data

    def _deep_copy(self, obj: Any) -> Any:
        """深拷贝对象"""
        if isinstance(obj, dict):
            return {key: self._deep_copy(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj


class DynamicResponseEngine:
    """动态响应引擎"""
    
    def __init__(self):
        self.response_rules: List[Dict[str, Any]] = []

    def configure_response_rules(self, rules_config: List[Dict[str, Any]]):
        """配置响应规则"""
        self.response_rules = rules_config

    async def generate_response_with_rules(
        self, 
        original_result: Dict[str, Any], 
        route_config: Any, 
        request: Request,
        request_data: Dict[str, Any],
        dynamic_rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """使用传入的动态规则生成响应"""
        try:
            # 构建上下文
            context = {
                "result_data": original_result,
                "request_data": request_data,
                "request": request,
                "route_config": route_config,
                "user_id": getattr(request.state, 'user_id', None),
                "user_roles": getattr(request.state, 'user_roles', []),
                "api_id": route_config.api_id if hasattr(route_config, 'api_id') else None,
            }

            print(f"🔧 开始评估 {len(dynamic_rules)} 个动态响应规则")

            # 按优先级排序并查找匹配的规则
            for rule in sorted(dynamic_rules, key=lambda x: x.get("priority", 1), reverse=True):
                if not rule.get("enabled", True):
                    continue
                print(f"🔍 评估规则: {rule.get('name', '未命名规则')}")
                
                conditions = rule.get("conditions", [])
                if self._evaluate_rule_conditions(conditions, context):
                    print(f"✅ 规则匹配成功: {rule.get('name', '未命名规则')}")
                    # 找到匹配的规则，应用响应模板
                    template_config = rule.get("template", {})
                    template = ResponseTemplate(template_config)
                    generated_response = template.render(context)
                    print(f"📤 生成的响应: {json.dumps(generated_response, ensure_ascii=False)[:200]}...")
                    return generated_response
                else:
                    print(f"❌ 规则不匹配: {rule.get('name', '未命名规则')}")

            print(f"⚠️ 没有匹配的规则，返回默认响应")
            # 如果没有匹配的规则，返回默认响应
            return self._format_default_response(original_result, context)

        except Exception as e:
            print(f"⚠️ 动态响应生成失败: {e}")
            import traceback
            traceback.print_exc()
            return original_result

    async def generate_response(
        self, 
        original_result: Dict[str, Any], 
        route_config: Any, 
        request: Request,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成动态响应"""
        try:
            # 构建上下文
            context = {
                "result_data": original_result,
                "request_data": request_data,
                "request": request,
                "route_config": route_config,
                "user_id": getattr(request.state, 'user_id', None),
                "user_roles": getattr(request.state, 'user_roles', []),
                "api_id": route_config.api_id if hasattr(route_config, 'api_id') else None,
            }

            # 获取响应规则配置
            response_rules = self._get_response_rules(route_config)
            
            # 按优先级排序并查找匹配的规则
            for rule in sorted(response_rules, key=lambda x: x.get("priority", 0), reverse=True):
                if not rule.get("enabled", True):
                    continue
                if self._evaluate_rule_conditions(rule.get("conditions", []), context):
                    # 找到匹配的规则，应用响应模板
                    template = ResponseTemplate(rule.get("response_template", {}))
                    return template.render(context)

            # 如果没有匹配的规则，返回默认响应
            return self._format_default_response(original_result, context)

        except Exception as e:
            print(f"⚠️ 动态响应生成失败: {e}")
            return original_result

    def _get_response_rules(self, route_config: Any) -> List[Dict[str, Any]]:
        """获取响应规则配置"""
        try:
            if hasattr(route_config, 'responses_config') and route_config.responses_config:
                dynamic_rules = route_config.responses_config.get("dynamic_rules", [])
                if isinstance(dynamic_rules, list):
                    return dynamic_rules
            return []
        except Exception:
            return []

    def _evaluate_rule_conditions(self, conditions: List[Dict[str, Any]], context: Dict[str, Any]) -> bool:
        """评估规则条件"""
        if not conditions:
            return True

        results = []
        for condition_config in conditions:
            condition = ResponseCondition(condition_config)
            results.append(condition.evaluate(context))

        # 处理逻辑组合
        if len(results) == 1:
            return results[0]
        
        # 默认使用AND逻辑
        logic = conditions[0].get("logic", "and") if conditions else "and"
        if logic == "or":
            return any(results)
        else:
            return all(results)

    def _format_default_response(self, original_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """格式化默认响应"""
        # 添加标准元数据
        result = original_result.copy()

        # 添加时间戳（兼容微秒格式，避免ValueError）
        now = datetime.now()
        # 格式：2025-08-11T12:34:56.123Z
        result["timestamp"] = now.strftime('%Y-%m-%dT%H:%M:%S.') + f"{int(now.microsecond/1000):03d}Z"

        # 添加请求ID
        result["request_id"] = str(uuid.uuid4())

        # 添加API信息
        if context.get("api_id"):
            result["api_info"] = {
                "api_id": context["api_id"],
                "version": "1.0"
            }
        
        return result


# 预设响应模板
PRESET_RESPONSE_TEMPLATES = {
    "success_with_data": {
        "name": "成功返回数据",
        "description": "标准成功响应，包含数据",
        "config": {
            "status_code": 200,
            "body_template": {
                "code": 200,
                "message": "操作成功",
                "data": "{{original_data}}",
                "timestamp": "{{timestamp}}",
                "request_id": "{{request_id}}"
            }
        }
    },
    "paginated_list": {
        "name": "分页列表响应",
        "description": "分页数据响应模板",
        "config": {
            "status_code": 200,
            "body_template": {
                "code": 200,
                "message": "获取成功",
                "data": {
                    "items": "{{original_data}}",
                    "total": "{{data_count}}",
                    "page": "{{request.query.page|1}}",
                    "per_page": "{{request.query.limit|10}}"
                },
                "timestamp": "{{timestamp}}"
            }
        }
    },
    "error_response": {
        "name": "错误响应",
        "description": "标准错误响应模板",
        "config": {
            "status_code": 400,
            "body_template": {
                "code": 400,
                "message": "请求失败",
                "error": "{{error_message}}",
                "timestamp": "{{timestamp}}",
                "request_id": "{{request_id}}"
            }
        }
    },
    "conditional_access": {
        "name": "条件访问响应",
        "description": "根据用户角色返回不同数据",
        "config": {
            "status_code": 200,
            "body_template": {
                "code": 200,
                "message": "获取成功",
                "data": "{{filtered_data}}",
                "access_level": "{{user_role}}",
                "timestamp": "{{timestamp}}"
            },
            "transformations": [
                {
                    "type": "filter",
                    "condition": {
                        "type": "user_role",
                        "operator": "in",
                        "value": ["admin", "manager"]
                    }
                }
            ]
        }
    }
}
