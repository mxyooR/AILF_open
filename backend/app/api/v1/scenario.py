"""
场景管理模块API路由
严格按照API文档实现场景管理的5个接口
"""
from fastapi import APIRouter, HTTPException, Header, Query, status, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from app.schemas.scenario import (
    ScenarioCreateRequest,
    ScenarioValidateRequest,
    ScenarioFromTemplateRequest,
    ScenarioResponse,
    ScenarioErrorResponse,
    ScenarioErrorData
)
from app.services.scenario_service import scenario_service
from app.core.auth import verify_developer_token
from app.core.response import UnifiedResponse

router = APIRouter(prefix="/scenario", tags=["场景管理模块"])


@router.get(
    "",
    response_model=ScenarioResponse,
    summary="获取当前活跃场景配置",
    description="获取当前系统中活跃的场景配置信息"
)
async def get_active_scenario(
    include_details: bool = Query(default=False, description="是否包含详细配置信息"),
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """
    获取当前活跃场景配置接口
    
    - **include_details**: 是否包含详细配置信息，默认false
    
    返回当前活跃的场景配置
    """
    # 调用场景服务
    result = scenario_service.get_active_scenario(include_details=include_details)
    
    if result["success"]:
        # 获取成功 - 将Scenario对象转换为字典
        data = result["data"].copy()
        if "scenario" in data and hasattr(data["scenario"], "model_dump"):
            data["scenario"] = data["scenario"].model_dump()

        return UnifiedResponse.success(
            data=data,
            message="获取场景配置成功"
        )
    else:
        # 未找到活跃场景
        raise UnifiedResponse.not_found(
            message="未找到活跃的场景配置",
            error_type=result["error"],
            details=result["details"]
        )


@router.post(
    "",
    response_model=ScenarioResponse,
    summary="创建或更新场景配置",
    description="创建新的场景配置或更新现有的场景配置"
)
async def create_or_update_scenario(
    request: ScenarioCreateRequest,
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """
    创建或更新场景配置接口
    
    - **name**: 场景名称
    - **type**: 场景类型
    - **description**: 场景描述（可选）
    - **config**: 场景配置对象
    
    返回创建或更新后的场景配置
    """
    # 调用场景服务
    result = scenario_service.create_or_update_scenario(request)
    
    if result["success"]:
        # 创建/更新成功
        is_created = result.get("created", False)
        status_code = 201 if is_created else 200
        message = "场景配置创建成功" if is_created else "场景配置更新成功"

        # 将Scenario对象转换为字典
        data = result["data"].copy()
        if "scenario" in data and hasattr(data["scenario"], "model_dump"):
            data["scenario"] = data["scenario"].model_dump()

        if is_created:
            return UnifiedResponse.created(data=data, message=message)
        else:
            return UnifiedResponse.success(data=data, message=message)
    else:
        # 创建/更新失败
        if result["error"] == "duplicate_scenario":
            raise UnifiedResponse.conflict(
                message="场景名称重复",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.bad_request(
                message="创建场景配置失败",
                error_type=result["error"],
                details=result["details"]
            )


@router.get(
    "/{scenario_id}",
    response_model=ScenarioResponse,
    summary="获取特定场景配置",
    description="根据场景ID获取特定场景的详细配置信息"
)
async def get_scenario_by_id(
    scenario_id: str,
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """
    获取特定场景配置接口
    
    - **scenario_id**: 场景唯一标识符
    
    返回指定场景的详细配置信息
    """
    # 调用场景服务
    result = scenario_service.get_scenario_by_id(scenario_id)
    
    if result["success"]:
        # 获取成功 - 将Scenario对象转换为字典
        data = result["data"].copy()
        if "scenario" in data and hasattr(data["scenario"], "model_dump"):
            data["scenario"] = data["scenario"].model_dump()

        return UnifiedResponse.success(
            data=data,
            message="获取场景配置成功"
        )
    else:
        # 场景不存在
        raise UnifiedResponse.not_found(
            message="场景配置不存在",
            error_type=result["error"],
            details=result["details"]
        )


@router.post(
    "/validate",
    summary="验证当前场景配置的有效性",
    description="验证当前场景配置的完整性和有效性，检查配置是否符合要求"
)
async def validate_scenario(
    request: ScenarioValidateRequest,
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """
    验证场景配置接口
    
    - **scenario_id**: 场景ID
    - **check_dependencies**: 是否检查依赖
    - **check_completeness**: 是否检查完整性
    
    返回验证结果
    """
    # 调用场景服务
    result = scenario_service.validate_scenario(request)
    
    if result["success"]:
        # 验证通过
        return UnifiedResponse.success(
            message="场景配置验证通过",
            data=result["data"].model_dump()
        )
    else:
        # 验证失败
        if result["error"] == "scenario_not_found":
            raise UnifiedResponse.not_found(
                message="场景配置不存在",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            # 验证失败但不抛异常,返回验证结果
            return UnifiedResponse.success(
                message="场景配置验证失败",
                data=result["data"].model_dump()
            )


@router.post(
    "/from-template",
    response_model=ScenarioResponse,
    summary="从预设模板创建场景配置",
    description="基于预设模板快速创建场景配置"
)
async def create_scenario_from_template(
    request: ScenarioFromTemplateRequest,
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """
    从模板创建场景配置接口
    
    - **template_key**: 模板标识符
    - **name**: 场景名称
    - **description**: 场景描述（可选）
    - **customizations**: 自定义配置覆盖（可选）
    
    返回基于模板创建的场景配置
    """
    # 调用场景服务
    result = scenario_service.create_from_template(request)
    
    if result["success"]:
        # 创建成功
        # 将Scenario对象转换为字典
        data = result["data"].copy()
        if "scenario" in data and hasattr(data["scenario"], "model_dump"):
            data["scenario"] = data["scenario"].model_dump()

        return UnifiedResponse.created(
            data=data,
            message="基于模板创建场景成功"
        )
    else:
        # 创建失败
        if result["error"] == "template_not_found":
            raise UnifiedResponse.not_found(
                message="模板不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] == "duplicate_scenario":
            raise UnifiedResponse.conflict(
                message="场景名称重复",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.bad_request(
                message="创建场景配置失败",
                error_type=result["error"],
                details=result["details"]
            )
