"""
配置状态相关的Schema定义
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class StepStatus(BaseModel):
    """单个步骤状态"""
    completed: bool = Field(..., description="是否完成")
    completed_at: Optional[str] = Field(None, description="完成时间")


class ConfigurationStatusResponse(BaseModel):
    """配置状态响应"""
    scenario_id: str = Field(..., description="场景ID")
    steps: Dict[str, StepStatus] = Field(..., description="各步骤状态")
    all_completed: bool = Field(..., description="是否全部完成")
    all_completed_at: Optional[str] = Field(None, description="全部完成时间")
    completed_count: int = Field(..., description="已完成步骤数")
    total_steps: int = Field(7, description="总步骤数")
    completion_percentage: float = Field(..., description="完成百分比")


class ConfigurationCompletionCheckResponse(BaseModel):
    """配置完成检查响应"""
    is_completed: bool = Field(..., description="是否完成配置")
    allowed: bool = Field(..., description="是否允许访问")
    message: str = Field(..., description="状态消息")
    status: str = Field(..., description="状态：completed/incomplete")
    incomplete_steps: Optional[List[int]] = Field(None, description="未完成的步骤编号")
    incomplete_step_names: Optional[List[str]] = Field(None, description="未完成的步骤名称")
    configuration_status: Optional[ConfigurationStatusResponse] = Field(None, description="详细配置状态")


class StepCompletionRequest(BaseModel):
    """步骤完成请求"""
    step_number: int = Field(..., ge=1, le=7, description="步骤编号(1-7)")
    completed: bool = Field(True, description="是否完成")
    scenario_id: Optional[str] = Field(None, description="场景ID")
    details: Optional[Dict[str, Any]] = Field(None, description="完成详情")


class StepCompletionResponse(BaseModel):
    """步骤完成响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    step_number: int = Field(..., description="步骤编号")
    step_name: str = Field(..., description="步骤名称")
    completed: bool = Field(..., description="完成状态")
    all_completed: bool = Field(..., description="是否全部完成")


class ConfigurationResetRequest(BaseModel):
    """配置重置请求"""
    scenario_id: Optional[str] = Field(None, description="场景ID")
    confirm: bool = Field(..., description="确认重置")


class ConfigurationResetResponse(BaseModel):
    """配置重置响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    scenario_id: str = Field(..., description="场景ID")
