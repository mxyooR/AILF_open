"""
配置状态API路由
提供配置完成状态的检查和管理接口
"""
from app.core.logging_config import get_logger
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

from app.schemas.configuration_status import (
    ConfigurationStatusResponse,
    ConfigurationCompletionCheckResponse,
    StepCompletionRequest,
    StepCompletionResponse,
    ConfigurationResetRequest,
    ConfigurationResetResponse
)
from app.services.configuration_status_service import configuration_status_service
from app.core.auth import verify_developer_token
from app.core.response import UnifiedResponse

logger = get_logger(__name__)

router = APIRouter()


@router.get("/configuration/status/check",
           response_model=ConfigurationCompletionCheckResponse,
           summary="检查配置完成状态",
           description="公开接口，检查七步配置是否完成，不需要认证")
async def check_configuration_completion(
    scenario_id: Optional[str] = Query(None, description="场景ID，默认为default")
):
    """
    检查配置完成状态（公开接口）

    这是一个公开接口，不需要认证即可访问。
    用于检查七步配置是否全部完成，以决定是否允许用户使用系统功能。
    """
    try:
        logger.debug(f"🔍 API调用: check_configuration_completion, scenario_id={scenario_id}")

        # 获取访问权限验证结果
        permission_result = configuration_status_service.validate_access_permission(scenario_id)
        logger.debug(f"🔍 permission_result: {permission_result}")

        # 获取详细配置状态
        config_status = configuration_status_service.get_configuration_status(scenario_id)
        logger.debug(f"🔍 config_status: {config_status}")

        response = ConfigurationCompletionCheckResponse(
            is_completed=permission_result["allowed"],
            allowed=permission_result["allowed"],
            message=permission_result["message"],
            status=permission_result["status"],
            incomplete_steps=permission_result.get("incomplete_steps"),
            incomplete_step_names=permission_result.get("incomplete_step_names"),
            configuration_status=ConfigurationStatusResponse(**config_status) if config_status else None
        )

        logger.debug(f"🔍 API响应: is_completed={response.is_completed}, allowed={response.allowed}")
        return response
        
    except Exception as e:
        logger.error(f"检查配置完成状态失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="检查配置状态失败",
            error_type="check_config_failed",
            details=str(e)
        )


@router.get("/configuration/status", 
           response_model=ConfigurationStatusResponse,
           summary="获取配置状态详情")
async def get_configuration_status(
    scenario_id: Optional[str] = Query(None, description="场景ID，默认为default"),
    _: dict = Depends(verify_developer_token)
):
    """
    获取配置状态详情
    
    需要开发者认证。返回详细的配置状态信息，包括各步骤的完成情况。
    """
    try:
        config_status = configuration_status_service.get_configuration_status(scenario_id)
        
        if not config_status:
            raise UnifiedResponse.not_found(
                message="配置状态不存在",
                error_type="config_status_not_found"
            )
        
        return ConfigurationStatusResponse(**config_status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置状态失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="获取配置状态失败",
            error_type="get_config_status_failed",
            details=str(e)
        )


@router.post("/configuration/status/step", 
            response_model=StepCompletionResponse,
            summary="更新步骤完成状态")
async def update_step_completion(
    request: StepCompletionRequest,
    _: dict = Depends(verify_developer_token)
):
    """
    更新步骤完成状态
    
    需要开发者认证。用于标记某个配置步骤为完成或未完成状态。
    """
    try:
        success = configuration_status_service.update_step_completion(
            step_number=request.step_number,
            completed=request.completed,
            scenario_id=request.scenario_id,
            details=request.details
        )
        
        if not success:
            raise UnifiedResponse.internal_error(
                message="更新步骤状态失败",
                error_type="update_step_failed"
            )
        
        # 获取步骤名称
        step_name = configuration_status_service.get_step_name(request.step_number)
        
        # 检查是否全部完成
        is_all_completed = configuration_status_service.is_configuration_completed(request.scenario_id)
        
        return StepCompletionResponse(
            success=True,
            message=f"步骤 {request.step_number}({step_name}) 状态已更新为: {'完成' if request.completed else '未完成'}",
            step_number=request.step_number,
            step_name=step_name,
            completed=request.completed,
            all_completed=is_all_completed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新步骤完成状态失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="更新步骤状态失败",
            error_type="update_step_failed",
            details=str(e)
        )


@router.post("/configuration/status/reset", 
            response_model=ConfigurationResetResponse,
            summary="重置配置状态")
async def reset_configuration_status(
    request: ConfigurationResetRequest,
    _: dict = Depends(verify_developer_token)
):
    """
    重置配置状态
    
    需要开发者认证。将所有配置步骤重置为未完成状态。
    """
    try:
        if not request.confirm:
            raise UnifiedResponse.bad_request(
                message="请确认重置操作",
                error_type="confirmation_required"
            )
        
        success = configuration_status_service.reset_configuration(request.scenario_id)
        
        if not success:
            raise UnifiedResponse.internal_error(
                message="重置配置状态失败",
                error_type="reset_config_failed"
            )
        
        scenario_id = request.scenario_id or "default"
        
        return ConfigurationResetResponse(
            success=True,
            message=f"配置状态已重置: {scenario_id}",
            scenario_id=scenario_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置配置状态失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="重置配置状态失败",
            error_type="reset_config_failed",
            details=str(e)
        )
