"""
AI交互相关的Pydantic Schema
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class CommandRequest(BaseModel):
    """用户命令请求"""
    command: str = Field(..., description="用户输入的自然语言命令")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    options: Optional[Dict[str, Any]] = Field(None, description="选项配置")


class IntentAnalysis(BaseModel):
    """意图分析结果"""
    intent_type: str = Field(..., description="意图类型")
    entity: Optional[str] = Field(None, description="涉及的业务实体")
    action: Optional[str] = Field(None, description="具体操作")
    parameters: Optional[Dict[str, Any]] = Field(None, description="提取的参数")
    confidence: float = Field(..., description="置信度")


class AIResponse(BaseModel):
    """AI响应"""
    intent: Optional[IntentAnalysis] = Field(None, description="意图分析结果")
    amis_schema: Optional[Dict[str, Any]] = Field(None, description="生成的amis schema", alias="schema")
    response_text: str = Field(..., description="响应文本")
    timestamp: str = Field(..., description="时间戳")


class CommandResponse(BaseModel):
    """命令处理响应"""
    success: bool = Field(..., description="是否成功")
    data: Optional[AIResponse] = Field(None, description="响应数据")
    error: Optional[str] = Field(None, description="错误信息")





class EntitySuggestionRequest(BaseModel):
    """实体推荐请求"""
    business_description: str = Field(..., description="业务描述")


class WorkflowSuggestionRequest(BaseModel):
    """工作流推荐请求"""
    entities: List[str] = Field(..., description="业务实体列表")
    business_scenario: str = Field(..., description="业务场景描述")


class APISuggestionRequest(BaseModel):
    """API推荐请求"""
    entities: List[str] = Field(..., description="业务实体列表")
    operations: List[str] = Field(..., description="操作类型列表")
    api_style: Optional[str] = Field("RESTful", description="API风格")


class SuggestionResponse(BaseModel):
    """推荐响应"""
    success: bool = Field(..., description="是否成功")
    suggestions: Optional[Dict[str, Any]] = Field(None, description="推荐结果")
    raw_response: Optional[str] = Field(None, description="原始响应")
    error: Optional[str] = Field(None, description="错误信息")


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    success: bool = Field(..., description="是否成功")
    ai_client: Dict[str, Any] = Field(..., description="AI客户端状态")
    error: Optional[str] = Field(None, description="错误信息")
