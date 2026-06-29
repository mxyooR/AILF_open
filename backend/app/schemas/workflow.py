"""
工作流相关的Pydantic模型 (AI指导版)
包括请求和响应模型，专门为AI提供业务流程指导
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    """工作流状态枚举"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class NodeType(str, Enum):
    """节点类型枚举 (AI指导版)"""
    START = "start"
    API_CALL = "api_call"
    USER_INPUT = "user_input"
    CONDITION = "condition"
    NOTIFICATION = "notification"
    END = "end"


class ConditionType(str, Enum):
    """条件类型枚举"""
    ALWAYS = "always"
    EXPRESSION = "expression"
    FORM_COMPLETED = "form_completed"


class ComplexityLevel(str, Enum):
    """复杂度级别枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InstanceStatus(str, Enum):
    """实例状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class ExecutionStatus(str, Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# 基础模型
class Position(BaseModel):
    """位置坐标"""
    x: int = Field(..., description="X坐标")
    y: int = Field(..., description="Y坐标")


class WorkflowInput(BaseModel):
    """工作流输入定义"""
    name: str = Field(..., description="输入名称")
    type: str = Field(..., description="输入类型")
    description: str = Field(..., description="输入描述")
    required: bool = Field(True, description="是否必填")
    ai_prompt: str = Field(..., description="AI提示语")


class NodeCondition(BaseModel):
    """节点转换条件"""
    type: ConditionType = Field(..., description="条件类型")
    expression: Optional[str] = Field(None, description="条件表达式")
    description: str = Field(..., description="条件描述")


class ChildNode(BaseModel):
    """子节点配置"""
    node_id: str = Field(..., description="子节点ID")
    condition: NodeCondition = Field(..., description="转换条件")


class NodeOutput(BaseModel):
    """节点输出定义"""
    name: str = Field(..., description="输出名称")
    type: str = Field(..., description="输出类型")
    description: str = Field(..., description="输出描述")


class AIInstructions(BaseModel):
    """AI执行指令"""
    purpose: Optional[str] = Field("", description="节点目的")
    action: Optional[str] = Field("", description="执行动作")
    user_message: Optional[str] = Field("", description="用户消息")
    success_handling: Optional[str] = Field("", description="成功处理")
    error_handling: Optional[str] = Field("", description="错误处理")
    true_path: Optional[str] = Field(None, description="条件为真时的路径")
    false_path: Optional[str] = Field(None, description="条件为假时的路径")
    validation: Optional[str] = Field(None, description="验证规则")


class WorkflowMetadata(BaseModel):
    """工作流元数据"""
    tags: List[str] = Field([], description="标签列表")
    complexity: ComplexityLevel = Field(ComplexityLevel.MEDIUM, description="复杂度级别")


class Progress(BaseModel):
    """进度信息"""
    completed_steps: int = Field(..., description="已完成步骤数")
    total_steps: int = Field(..., description="总步骤数")
    percentage: float = Field(..., description="进度百分比")


# 节点相关模型
class NodeConfig(BaseModel):
    """节点配置"""
    # API调用配置
    api_id: Optional[str] = Field(None, description="API标识符")
    api_endpoint: Optional[str] = Field(None, description="API端点")
    method: Optional[str] = Field(None, description="HTTP方法")
    parameters: Optional[Dict[str, Any]] = Field(None, description="API参数")
    ui_mode: Optional[str] = Field(None, description="UI模式(auto/form)")
    context_fields: Optional[List[str]] = Field(None, description="上下文展示白名单")

    # 用户输入配置
    input_type: Optional[str] = Field(None, description="输入类型")
    form_schema: Optional[Dict[str, Any]] = Field(None, description="表单结构")

    # 条件判断配置
    evaluation_expression: Optional[str] = Field(None, description="评估表达式")

    # 通知配置
    message_template: Optional[str] = Field(None, description="消息模板")
    recipients: Optional[List[str]] = Field(None, description="接收者列表")


class WorkflowNodeCreate(BaseModel):
    """创建工作流节点请求"""
    id: str = Field(..., description="节点ID")
    name: str = Field(..., description="节点名称")
    description: Optional[str] = Field(None, description="节点描述")
    type: NodeType = Field(..., description="节点类型")
    position: Optional[Position] = Field(None, description="节点位置")
    parent_nodes: List[str] = Field([], description="父节点列表")
    child_nodes: List[ChildNode] = Field([], description="子节点配置")
    config: Optional[NodeConfig] = Field(None, description="节点配置")
    outputs: List[NodeOutput] = Field([], description="节点输出")
    ai_instructions: Optional[AIInstructions] = Field(None, description="AI执行指令")


class WorkflowNode(BaseModel):
    """工作流节点"""
    id: str = Field(..., description="节点ID")
    name: str = Field(..., description="节点名称")
    description: Optional[str] = Field(None, description="节点描述")
    type: NodeType = Field(..., description="节点类型")
    position: Optional[Position] = Field(None, description="节点位置")
    parent_nodes: List[str] = Field([], description="父节点列表")
    child_nodes: List[ChildNode] = Field([], description="子节点配置")
    config: Optional[Dict[str, Any]] = Field(None, description="节点配置")
    outputs: List[NodeOutput] = Field([], description="节点输出")
    ai_instructions: Optional[Dict[str, Any]] = Field(None, description="AI执行指令")


# 工作流定义相关模型
class WorkflowCreateRequest(BaseModel):
    """创建工作流请求 (AI指导版)"""
    name: str = Field(..., min_length=1, max_length=200, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    business_scenario: str = Field(..., description="业务场景标识")
    user_intents: List[str] = Field(..., description="用户意图列表")
    trigger_keywords: List[str] = Field(..., description="触发关键词列表")
    inputs: List[WorkflowInput] = Field([], description="工作流输入定义")
    nodes: List[WorkflowNodeCreate] = Field(..., description="工作流节点列表")
    metadata: Optional[WorkflowMetadata] = Field(None, description="工作流元数据")


class WorkflowUpdateRequest(BaseModel):
    """更新工作流请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    business_scenario: Optional[str] = Field(None, description="业务场景标识")
    status: Optional[WorkflowStatus] = Field(None, description="工作流状态")
    user_intents: Optional[List[str]] = Field(None, description="用户意图列表")
    trigger_keywords: Optional[List[str]] = Field(None, description="触发关键词列表")
    inputs: Optional[List[WorkflowInput]] = Field(None, description="工作流输入定义")
    nodes: Optional[List[WorkflowNodeCreate]] = Field(None, description="工作流节点列表")
    metadata: Optional[WorkflowMetadata] = Field(None, description="工作流元数据")


class WorkflowListItem(BaseModel):
    """工作流列表项"""
    id: str = Field(..., description="工作流ID")
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    business_scenario: str = Field(..., description="业务场景标识")
    status: WorkflowStatus = Field(..., description="工作流状态")
    version: str = Field(..., description="版本号")
    node_count: int = Field(..., description="节点数量")
    instance_count: int = Field(..., description="实例数量")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class NodeRelationships(BaseModel):
    """节点关系映射"""
    children: List[str] = Field([], description="子节点列表")
    parents: List[str] = Field([], description="父节点列表")
    conditions: List[NodeCondition] = Field([], description="转换条件列表")


class Workflow(BaseModel):
    """工作流详情 (AI指导版)"""
    id: str = Field(..., description="工作流ID")
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    business_scenario: str = Field(..., description="业务场景标识")
    user_intents: List[str] = Field(..., description="用户意图列表")
    trigger_keywords: List[str] = Field(..., description="触发关键词列表")
    inputs: List[WorkflowInput] = Field([], description="工作流输入定义")
    nodes: List[WorkflowNode] = Field(..., description="工作流节点列表")
    node_relationships: Dict[str, NodeRelationships] = Field({}, description="节点关系映射")
    status: WorkflowStatus = Field(..., description="工作流状态")
    version: str = Field(..., description="版本号")
    metadata: Optional[Dict[str, Any]] = Field(None, description="工作流元数据")
    node_count: int = Field(..., description="节点数量")
    instance_count: int = Field(..., description="实例数量")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


# 工作流执行相关模型
class WorkflowExecuteRequest(BaseModel):
    """执行工作流请求"""
    input_data: Optional[Dict[str, Any]] = Field({}, description="输入数据")
    context: Optional[Dict[str, Any]] = Field({}, description="上下文数据")
    priority: Optional[str] = Field("normal", description="优先级")


class ExecutionHistory(BaseModel):
    """执行历史"""
    step_id: str = Field(..., description="步骤ID")
    step_name: str = Field(..., description="步骤名称")
    status: ExecutionStatus = Field(..., description="执行状态")
    started_at: Optional[str] = Field(None, description="开始时间")
    completed_at: Optional[str] = Field(None, description="完成时间")
    duration: Optional[int] = Field(None, description="执行时长(毫秒)")
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")
    output_data: Optional[Dict[str, Any]] = Field(None, description="输出数据")
    error_message: Optional[str] = Field(None, description="错误信息")


class WorkflowInstance(BaseModel):
    """工作流实例"""
    id: str = Field(..., description="实例ID")
    workflow_id: str = Field(..., description="工作流ID")
    workflow_name: str = Field(..., description="工作流名称")
    status: InstanceStatus = Field(..., description="实例状态")
    current_step: Optional[str] = Field(None, description="当前步骤ID")
    progress: Progress = Field(..., description="进度信息")
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文数据")
    output_data: Optional[Dict[str, Any]] = Field(None, description="输出数据")
    started_by: Optional[str] = Field(None, description="启动用户ID")
    priority: str = Field("normal", description="优先级")
    started_at: Optional[str] = Field(None, description="开始时间")
    completed_at: Optional[str] = Field(None, description="完成时间")
    estimated_completion: Optional[str] = Field(None, description="预计完成时间")
    execution_history: Optional[List[ExecutionHistory]] = Field([], description="执行历史")


class WorkflowInstanceListItem(BaseModel):
    """工作流实例列表项"""
    id: str = Field(..., description="实例ID")
    workflow_id: str = Field(..., description="工作流ID")
    workflow_name: str = Field(..., description="工作流名称")
    status: InstanceStatus = Field(..., description="实例状态")
    current_step: Optional[str] = Field(None, description="当前步骤ID")
    progress: Progress = Field(..., description="进度信息")
    started_at: Optional[str] = Field(None, description="开始时间")
    updated_at: str = Field(..., description="更新时间")
    estimated_completion: Optional[str] = Field(None, description="预计完成时间")


# 节点管理相关模型
class WorkflowNodeCreateRequest(BaseModel):
    """添加工作流节点请求"""
    id: str = Field(..., description="节点ID")
    name: str = Field(..., description="节点名称")
    description: Optional[str] = Field(None, description="节点描述")
    type: NodeType = Field(..., description="节点类型")
    position: Optional[Position] = Field(None, description="节点位置")
    parent_nodes: List[str] = Field([], description="父节点列表")
    child_nodes: List[ChildNode] = Field([], description="子节点配置")
    config: Optional[NodeConfig] = Field(None, description="节点配置")
    outputs: List[NodeOutput] = Field([], description="节点输出")
    ai_instructions: Optional[AIInstructions] = Field(None, description="AI执行指令")


class WorkflowNodeUpdateRequest(BaseModel):
    """更新工作流节点请求"""
    name: Optional[str] = Field(None, description="节点名称")
    description: Optional[str] = Field(None, description="节点描述")
    type: Optional[NodeType] = Field(None, description="节点类型")
    position: Optional[Position] = Field(None, description="节点位置")
    parent_nodes: Optional[List[str]] = Field(None, description="父节点列表")
    child_nodes: Optional[List[ChildNode]] = Field(None, description="子节点配置")
    config: Optional[NodeConfig] = Field(None, description="节点配置")
    outputs: Optional[List[NodeOutput]] = Field(None, description="节点输出")
    ai_instructions: Optional[AIInstructions] = Field(None, description="AI执行指令")


# AI工作流查询相关模型
class WorkflowQueryRequest(BaseModel):
    """AI工作流查询请求"""
    user_input: str = Field(..., description="用户输入")
    context: Optional[Dict[str, Any]] = Field({}, description="上下文信息")


class WorkflowMatch(BaseModel):
    """工作流匹配结果"""
    workflow_id: str = Field(..., description="工作流ID")
    name: str = Field(..., description="工作流名称")
    business_scenario: str = Field(..., description="业务场景")
    confidence: float = Field(..., description="匹配置信度")
    matched_intents: List[str] = Field([], description="匹配的意图")
    matched_keywords: List[str] = Field([], description="匹配的关键词")


class WorkflowQueryResponse(BaseModel):
    """AI工作流查询响应"""
    matches: List[WorkflowMatch] = Field([], description="匹配的工作流列表")
    best_match: Optional[WorkflowMatch] = Field(None, description="最佳匹配")
    suggestions: List[str] = Field([], description="建议列表")


# 分页和统计模型
class PaginationInfo(BaseModel):
    """分页信息"""
    page: int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页数量")
    total: int = Field(..., description="总数量")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class InstanceSummary(BaseModel):
    """实例统计摘要"""
    total_instances: int = Field(..., description="总实例数")
    running: int = Field(..., description="运行中实例数")
    completed: int = Field(..., description="已完成实例数")
    failed: int = Field(..., description="失败实例数")
    pending: int = Field(default=0, description="等待中实例数")
    cancelled: int = Field(default=0, description="已取消实例数")


class WorkflowContinueRequest(BaseModel):
    """继续执行工作流请求"""
    action: str = Field(..., description="操作类型")
    data: Dict[str, Any] = Field(default_factory=dict, description="操作数据")
    comment: Optional[str] = Field(None, description="操作备注")


class WorkflowExecutionContext(BaseModel):
    """工作流执行上下文"""
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    priority: Optional[str] = Field("normal", description="优先级")


class WorkflowStepHistory(BaseModel):
    """工作流步骤执行历史"""
    step_id: str = Field(..., description="步骤ID")
    step_name: str = Field(..., description="步骤名称")
    status: str = Field(..., description="执行状态")
    started_at: str = Field(..., description="开始时间")
    completed_at: Optional[str] = Field(None, description="完成时间")
    duration: Optional[int] = Field(None, description="执行时长(毫秒)")
    output: Dict[str, Any] = Field(default_factory=dict, description="输出数据")
    waiting_for: Optional[str] = Field(None, description="等待原因")
    timeout_at: Optional[str] = Field(None, description="超时时间")
