"""
动态响应管理API
提供动态响应配置的管理接口
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db_session
from app.core.auth import verify_developer_token
from app.models.api_route import APIRouteDBModel
from app.core.dynamic_response_engine import PRESET_RESPONSE_TEMPLATES
from app.core.response import UnifiedResponse


router = APIRouter(prefix="/dynamic-response", tags=["动态响应配置"])


class ResponseRuleModel(BaseModel):
    id: str
    name: str
    priority: int
    conditions: List[Dict[str, Any]]
    response_template: Dict[str, Any]
    enabled: bool


class DynamicResponseConfigModel(BaseModel):
    dynamic_rules: List[ResponseRuleModel]


@router.get("/presets")
async def get_preset_templates(
    _: str = Depends(verify_developer_token)
) -> Dict[str, Any]:
    """获取预设响应模板"""
    return UnifiedResponse.success(
        message="获取预设模板成功",
        data=PRESET_RESPONSE_TEMPLATES
    )


@router.get("/conditions/types")
async def get_condition_types(
    _: str = Depends(verify_developer_token)
) -> Dict[str, Any]:
    """获取条件类型定义"""
    condition_types = [
        {
            "value": "parameter",
            "label": "参数条件",
            "description": "基于请求参数的条件",
            "fields": ["field", "operator", "value"],
            "example": {"field": "user_id", "operator": "eq", "value": "123"}
        },
        {
            "value": "header",
            "label": "请求头条件",
            "description": "基于HTTP头部的条件",
            "fields": ["field", "operator", "value"],
            "example": {"field": "User-Agent", "operator": "contains", "value": "mobile"}
        },
        {
            "value": "user_role",
            "label": "用户角色",
            "description": "基于用户角色的条件",
            "fields": ["operator", "value"],
            "example": {"operator": "in", "value": ["admin", "manager"]}
        },
        {
            "value": "time",
            "label": "时间条件",
            "description": "基于时间的条件",
            "fields": ["field", "operator", "value"],
            "example": {"field": "hour", "operator": "between", "value": [9, 18]}
        },
        {
            "value": "random",
            "label": "随机条件",
            "description": "基于随机数的条件",
            "fields": ["operator", "value"],
            "example": {"operator": "lt", "value": 50}
        },
        {
            "value": "data_count",
            "label": "数据数量",
            "description": "基于数据数量的条件",
            "fields": ["operator", "value"],
            "example": {"operator": "gte", "value": 10}
        }
    ]
    
    return UnifiedResponse.success(
        message="获取条件类型成功",
        data=condition_types
    )


@router.get("/operators")
async def get_operators(
    _: str = Depends(verify_developer_token)
) -> Dict[str, Any]:
    """获取操作符定义"""
    operators = [
        {"value": "eq", "label": "等于 (=)", "description": "值相等"},
        {"value": "ne", "label": "不等于 (≠)", "description": "值不相等"},
        {"value": "gt", "label": "大于 (>)", "description": "数值大于"},
        {"value": "gte", "label": "大于等于 (≥)", "description": "数值大于等于"},
        {"value": "lt", "label": "小于 (<)", "description": "数值小于"},
        {"value": "lte", "label": "小于等于 (≤)", "description": "数值小于等于"},
        {"value": "between", "label": "区间 (between)", "description": "在两个值区间内"},
        {"value": "in", "label": "包含在", "description": "值在列表中"},
        {"value": "not_in", "label": "不包含在", "description": "值不在列表中"},
        {"value": "contains", "label": "包含", "description": "字符串包含"},
        {"value": "exists", "label": "存在", "description": "字段存在且不为空"},
        {"value": "not_exists", "label": "不存在", "description": "字段不存在或为空"}
    ]
    
    return UnifiedResponse.success(
        message="获取操作符成功",
        data=operators
    )


@router.post("/validate")
async def validate_dynamic_config(
    config: DynamicResponseConfigModel,
    _: str = Depends(verify_developer_token)
) -> Dict[str, Any]:
    """验证动态响应配置"""
    errors = []
    warnings = []
    
    try:
        # 验证规则配置
        for i, rule in enumerate(config.dynamic_rules):
            # 检查规则名称
            if not rule.name.strip():
                errors.append(f"规则 {i+1}: 名称不能为空")
            
            # 检查条件配置
            if not rule.conditions:
                warnings.append(f"规则 {i+1} ({rule.name}): 没有配置条件，将始终匹配")
            
            for j, condition in enumerate(rule.conditions):
                if not condition.get("type"):
                    errors.append(f"规则 {i+1} 条件 {j+1}: 条件类型不能为空")
                if not condition.get("operator"):
                    errors.append(f"规则 {i+1} 条件 {j+1}: 操作符不能为空")
                if condition.get("value") is None:
                    errors.append(f"规则 {i+1} 条件 {j+1}: 比较值不能为空")
            
            # 检查响应模板
            template = rule.response_template
            if not template:
                errors.append(f"规则 {i+1} ({rule.name}): 响应模板不能为空")
            elif not template.get("body_template"):
                warnings.append(f"规则 {i+1} ({rule.name}): 响应体模板为空")
        
        # 检查优先级冲突
        priorities = [rule.priority for rule in config.dynamic_rules]
        if len(priorities) != len(set(priorities)):
            warnings.append("存在优先级相同的规则，可能影响执行顺序")
        
        return UnifiedResponse.success(
            message="配置验证完成",
            data={
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }
        )
        
    except Exception as e:
        raise UnifiedResponse.bad_request(
            message="配置验证失败",
            error_type="validation_failed",
            details={
                "valid": False,
                "errors": [f"验证过程出错: {str(e)}"],
                "warnings": []
            }
        )


@router.post("/test")
async def test_dynamic_response(
    request_data: Dict[str, Any],
    _: str = Depends(verify_developer_token)
) -> Dict[str, Any]:
    """测试动态响应配置"""
    try:
        from app.core.dynamic_response_engine import DynamicResponseEngine, ResponseCondition, ResponseTemplate
        
        # 创建动态响应引擎
        engine = DynamicResponseEngine()
        
        # 获取测试配置
        config = request_data.get("config", {})
        test_context = request_data.get("context", {})
        
        # 配置响应规则
        rules = config.get("dynamic_rules", [])
        
        # 模拟测试每个规则
        results = []
        for rule in rules:
            try:
                # 评估条件
                conditions = rule.get("conditions", [])
                matched = True
                
                if conditions:
                    condition_results = []
                    for condition_config in conditions:
                        condition = ResponseCondition(condition_config)
                        result = condition.evaluate(test_context)
                        condition_results.append({
                            "condition": condition_config,
                            "result": result,
                            "explanation": f"条件 '{condition_config.get('type')}' 评估结果: {result}"
                        })
                    
                    # 简单的AND逻辑
                    matched = all(cr["result"] for cr in condition_results)
                else:
                    condition_results = []
                
                # 如果匹配，生成响应
                response = None
                if matched:
                    template = ResponseTemplate(rule.get("response_template", {}))
                    response = template.render(test_context)
                
                results.append({
                    "rule_name": rule.get("name"),
                    "priority": rule.get("priority", 0),
                    "matched": matched,
                    "condition_results": condition_results,
                    "response": response
                })
                
            except Exception as e:
                results.append({
                    "rule_name": rule.get("name", "未命名规则"),
                    "priority": rule.get("priority", 0),
                    "matched": False,
                    "error": str(e)
                })
        
        return UnifiedResponse.success(
            message="动态响应测试完成",
            data={
                "test_results": results,
                "context": test_context
            }
        )
        
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="测试失败",
            error_type="test_failed",
            details=str(e)
        )


@router.get("/variables")
async def get_available_variables(
    _: str = Depends(verify_developer_token)
) -> Dict[str, Any]:
    """获取可用变量列表"""
    variables = [
        {
            "name": "{{timestamp}}",
            "description": "当前时间戳",
            "example": "2024-01-01T12:00:00Z"
        },
        {
            "name": "{{request_id}}",
            "description": "请求唯一ID",
            "example": "550e8400-e29b-41d4-a716-446655440000"
        },
        {
            "name": "{{user_id}}",
            "description": "当前用户ID",
            "example": "user123"
        },
        {
            "name": "{{api_id}}",
            "description": "API路由ID",
            "example": "api_product_list"
        },
        {
            "name": "{{data_count}}",
            "description": "返回数据数量",
            "example": "25"
        },
        {
            "name": "{{original_data}}",
            "description": "原始返回数据",
            "example": "[{...}, {...}]"
        },
        {
            "name": "{{user_role}}",
            "description": "用户角色",
            "example": "admin"
        },
        {
            "name": "{{request.query.xxx}}",
            "description": "查询参数",
            "example": "{{request.query.page}}"
        },
        {
            "name": "{{request.body.xxx}}",
            "description": "请求体参数",
            "example": "{{request.body.name}}"
        }
    ]
    
    return UnifiedResponse.success(
        message="获取变量列表成功",
        data=variables
    )
