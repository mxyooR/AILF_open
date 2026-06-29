"""
工作流执行服务 - 单一数据源

核心职责：
- 统一处理工作流状态流转
- 管理会话数据更新
- 计算下一步骤（支持条件分支）
- 调用 AI 生成界面

设计原则：
- DRY: 消除 ai_service.py 和 workflow.py 中的重复逻辑
- 单一职责: 所有工作流执行逻辑集中在此服务
- 清晰接口: 标准化的输入输出格式
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
import json
import re

from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class WorkflowExecutionResult:
    """
    工作流执行结果
    
    标准化的返回类型，包含执行状态、下一步骤、UI Schema 和错误信息
    """
    success: bool
    next_step: Optional[str]
    amis_schema: Optional[Dict[str, Any]]
    error: Optional[str] = None
    workflow_completed: bool = False
    
    def to_api_response(self) -> Dict[str, Any]:
        """
        转换为 API 响应格式
        
        用于 workflow.py 的 workflow_state_transition 端点
        """
        if self.workflow_completed:
            return {
                "status": 0,
                "msg": "工作流已完成",
                "data": self.amis_schema or {
                    "type": "page",
                    "body": {
                        "type": "alert",
                        "level": "success",
                        "body": "工作流已成功完成！"
                    }
                }
            }
        
        if not self.success:
            return {
                "status": 1,
                "msg": self.error or "执行失败",
                "data": self.amis_schema
            }
        
        return {
            "status": 0,
            "msg": "success",
            "data": self.amis_schema
        }
    
    def to_ai_response(self) -> Dict[str, Any]:
        """
        转换为 AI 服务响应格式
        
        用于 ai_service.py 的 _handle_workflow_continue 方法
        """
        if self.workflow_completed:
            return {
                "success": True,
                "amis_schema": self.amis_schema,
                "workflow_completed": True,
                "response_text": "工作流已完成"
            }
        
        return {
            "success": self.success,
            "amis_schema": self.amis_schema,
            "error": self.error,
            "response_text": "已为您生成界面" if self.success else self.error
        }


@dataclass
class WorkflowContext:
    """
    工作流上下文
    
    封装工作流执行所需的所有上下文信息
    """
    workflow_id: str
    node_id: str
    form_data: Dict[str, Any]
    accessible_apis: List[Dict[str, Any]] = field(default_factory=list)
    auto_progress: bool = False
    
    @classmethod
    def from_request(cls, request: Dict[str, Any], context: Dict[str, Any]) -> 'WorkflowContext':
        """
        从请求和上下文构建 WorkflowContext
        
        Args:
            request: API 请求体（包含 workflow_id, node_id, 表单数据等）
            context: 上下文信息（包含 accessible_apis 等）
        
        Returns:
            WorkflowContext 实例
        """
        # 过滤控制字段，提取纯表单数据
        control_fields = {"workflow_id", "node_id", "action", "&"}
        form_data = {k: v for k, v in request.items() if k not in control_fields}
        
        return cls(
            workflow_id=request.get("workflow_id") or context.get("workflow_id", ""),
            node_id=request.get("node_id") or context.get("node_id", ""),
            form_data=form_data,
            accessible_apis=context.get("accessible_apis", []),
            auto_progress=context.get("auto_progress", False)
        )


class WorkflowExecutionService:
    """
    工作流执行服务 - 单一数据源
    
    统一处理所有工作流状态流转逻辑，消除代码重复
    """
    
    def __init__(self):
        # 延迟导入，避免循环依赖
        self._session_service = None
        self._workflow_service = None
        self._api_executor = None
    
    @property
    def session_service(self):
        """延迟加载 workflow_session_service"""
        if self._session_service is None:
            from app.services.workflow_session_service import workflow_session_service
            self._session_service = workflow_session_service
        return self._session_service
    
    @property
    def workflow_service(self):
        """延迟加载 workflow_service"""
        if self._workflow_service is None:
            from app.services.workflow_service import workflow_service
            self._workflow_service = workflow_service
        return self._workflow_service
    
    @property
    def api_executor(self):
        """延迟加载 api_executor_service"""
        if self._api_executor is None:
            from app.services.api_executor_service import api_executor_service
            self._api_executor = api_executor_service
        return self._api_executor
    
    def is_workflow_schema(self, schema: Dict[str, Any]) -> bool:
        """
        🔥 判断 AI 生成的 schema 是否是工作流界面
        
        只看顶层是否有 workflow_id（与数据集 V13 格式一致）
        
        Args:
            schema: AI 生成的 AMIS schema
        
        Returns:
            bool: 是否是工作流界面
        """
        if not schema or not isinstance(schema, dict):
            return False
        
        workflow_id = schema.get("workflow_id")
        return bool(workflow_id)
    
    def extract_workflow_info_from_schema(self, schema: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        🔥 从 schema 顶层提取工作流信息
        
        Args:
            schema: AI 生成的 AMIS schema
        
        Returns:
            (workflow_id, current_node_id) - 如果不是工作流界面则返回 (None, None)
        """
        if not schema or not isinstance(schema, dict):
            return None, None
        
        workflow_id = schema.get("workflow_id")
        current_node_id = schema.get("current_node_id")
        
        return workflow_id, current_node_id
    
    def is_workflow_request(self, context: Dict[str, Any]) -> bool:
        """
        判断是否为工作流请求
        
        基于 context 结构判断，而非关键词匹配
        
        判断逻辑：
        1. context 同时包含 workflow_id 和 node_id -> True
        2. context 包含 auto_progress=True 且有活跃会话 -> True
        3. 其他情况 -> False
        
        Args:
            context: 请求上下文
        
        Returns:
            bool: 是否为工作流请求
        """
        if not context:
            return False
        
        # 检查是否同时有 workflow_id 和 node_id
        workflow_id = context.get("workflow_id")
        node_id = context.get("node_id")
        if workflow_id and node_id:
            logger.debug(f"检测到工作流请求: workflow_id={workflow_id}, node_id={node_id}")
            return True
        
        # 检查 auto_progress 标志（需要有活跃会话）
        if context.get("auto_progress"):
            user_id = context.get("user_id")
            if user_id:
                session = self.session_service.get_active_session(user_id)
                if session:
                    logger.debug(f"检测到 auto_progress 工作流请求: user_id={user_id}")
                    return True
        
        return False
    
    async def execute_step(
        self,
        user_id: str,
        workflow_id: str,
        node_id: str,
        form_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> WorkflowExecutionResult:
        """
        执行工作流步骤 - 核心方法
        
        统一的工作流执行入口，处理：
        1. 会话管理（获取或创建）
        2. 步骤数据更新
        3. 执行当前节点的业务逻辑（api_call 节点调用实际 API）
        4. 下一步计算（支持条件分支）
        5. AI Schema 生成
        
        Args:
            user_id: 用户ID
            workflow_id: 工作流ID
            node_id: 当前节点ID
            form_data: 表单数据
            context: 上下文（包含 accessible_apis, user_token 等）
        
        Returns:
            WorkflowExecutionResult: 执行结果
        """
        try:
            logger.info(f"WorkflowExec: 执行步骤 user={user_id}, workflow={workflow_id}, node={node_id}")
            logger.debug(f"WorkflowExec: 表单数据 {json.dumps(form_data, ensure_ascii=False, default=str)}")
            
            # 1. 获取或创建工作流会话
            session = self.session_service.get_active_session(user_id)
            
            if not session or session.workflow_id != workflow_id:
                # 需要创建新会话
                session, node_id = await self._create_or_update_session(
                    user_id, workflow_id, node_id
                )
                if not session:
                    return WorkflowExecutionResult(
                        success=False,
                        next_step=None,
                        amis_schema=self._create_error_schema(f"工作流不存在: {workflow_id}"),
                        error=f"工作流不存在: {workflow_id}"
                    )
            else:
                # 已有会话，验证 node_id
                node_id = self._validate_node_id(session, node_id)
            
            # 2. 更新会话数据（累积所有表单数据）
            if form_data:
                logger.debug(f"WorkflowExec: 累积表单数据字段 {list(form_data.keys())}")
                self.session_service.update_session_step(
                    user_id=user_id,
                    workflow_id=workflow_id,
                    new_step=node_id,
                    step_data=form_data
                )
            else:
                logger.warning("WorkflowExec: 表单数据为空，仅更新步骤")
                self.session_service.update_session_step(
                    user_id=user_id,
                    workflow_id=workflow_id,
                    new_step=node_id,
                    step_data={}
                )
            
            # 重新获取会话以确保数据最新
            session = self.session_service.get_active_session(user_id)
            logger.debug(f"WorkflowExec: 会话累积数据 {json.dumps(session.step_data, ensure_ascii=False, default=str)}")
            
            # 3. 获取当前节点信息
            current_node = self._get_node_by_id(session.workflow_data, node_id)

            # 4. 通知节点执行：统一走内置 notification_service
            if current_node and current_node.get("type") == "notification":
                ok, error_msg = await self._run_notification_node_if_needed(
                    node=current_node,
                    workflow_id=workflow_id,
                    node_id=node_id,
                    user_id=user_id,
                    context=context,
                    session=session
                )
                if not ok:
                    logger.error(f"WorkflowExec: 通知节点执行失败: {error_msg}")
                    return WorkflowExecutionResult(
                        success=False,
                        next_step=None,
                        amis_schema=self._create_error_schema(f"通知发送失败: {error_msg}"),
                        error=error_msg
                    )
                session = self.session_service.get_active_session(user_id)
            
            # 5. 如果当前节点是 api_call 类型，根据 HTTP 方法和 action 决定行为
            # 🔥 核心逻辑（与数据集 amis_generator_v3.py 一致）：
            #   - GET 请求：前端 AMIS 直接调用业务 API（wizard.initApi / service.api / select.source）
            #               返回数据通过 responseData 映射到表单，然后通过 "&": "$" 提交到后端
            #               后端只需要存储这些数据，不需要调用 API
            #   - POST 请求 + action="submit"：后端转发到业务 API（用户确认提交）
            #   - POST 请求 + action="next"：用户刚进入节点，生成表单界面，等待用户填写
            if current_node and current_node.get("type") == "api_call":
                node_config = current_node.get("config", {})
                http_method = node_config.get("method", "GET").upper()
                action = context.get("action", "next")
                
                logger.info(f"WorkflowExec: api_call节点 {current_node.get('name')}, method={http_method}, action={action}")
                
                # 🔥 检查是否有实际的表单数据（排除空值和控制字段）
                actual_form_data = {k: v for k, v in form_data.items() 
                                   if k not in ["form_data", "workflow_id", "node_id", "action", "&"] 
                                   and v not in [None, "", [], {}]}
                
                # 🔥 如果 form_data 字段存在且不为空，尝试解析它
                if "form_data" in form_data and form_data["form_data"]:
                    try:
                        if isinstance(form_data["form_data"], str):
                            import json as json_module
                            parsed_form_data = json_module.loads(form_data["form_data"])
                            if isinstance(parsed_form_data, dict):
                                actual_form_data.update(parsed_form_data)
                        elif isinstance(form_data["form_data"], dict):
                            actual_form_data.update(form_data["form_data"])
                    except:
                        pass
                
                has_actual_data = bool(actual_form_data)
                logger.debug(f"WorkflowExec: 实际表单数据 {actual_form_data}, 有数据={has_actual_data}")

                auto_ran_current = False
                if action == "next":
                    merged_session_data = {**session.step_data, **actual_form_data}
                    # GET 向导第二步常把查询参数放在 api_request.params 中，
                    # 这里先扁平化，避免后续缺参误判。
                    self._merge_request_params_into_session(merged_session_data, actual_form_data)
                    if self._should_auto_run_api_call(current_node, merged_session_data):
                        logger.info("WorkflowExec: api_call 节点自动执行（无需渲染表单）")
                        for key, value in actual_form_data.items():
                            session.step_data[key] = value
                        # Fill request params (e.g., departure_date) into session for later steps.
                        self._merge_request_params_into_session(session.step_data, actual_form_data)
                        self.session_service.update_session_step(
                            user_id=user_id,
                            workflow_id=workflow_id,
                            new_step=node_id,
                            step_data=session.step_data
                        )
                        session = self.session_service.get_active_session(user_id)
                        api_result = await self._execute_api_call_node(
                            node=current_node,
                            session_data=session.step_data,
                            context=context
                        )
                        if not self._merge_api_result_into_session(session, node_id, api_result):
                            error_msg = api_result.get("error", "API调用失败")
                            logger.error(f"WorkflowExec: 自动执行 API 失败: {error_msg}")
                            return WorkflowExecutionResult(
                                success=False,
                                next_step=None,
                                amis_schema=self._create_error_schema(f"API调用失败: {error_msg}"),
                                error=error_msg
                            )
                        self.session_service.update_session_step(
                            user_id=user_id,
                            workflow_id=workflow_id,
                            new_step=node_id,
                            step_data=session.step_data
                        )
                        auto_ran_current = True
                
                # 🔥 GET 请求：使用 AMIS Wizard 的 initApi 自动获取数据
                # 前端 AMIS Wizard 通过 initApi 调用业务 API，获取数据后通过 "&": "$" 提交所有数据到后端
                # 后端只需要存储这些数据，不需要自己调用 API
                if not auto_ran_current and http_method == "GET":
                    logger.info("WorkflowExec: GET 请求，使用 AMIS Wizard initApi 自动获取数据")
                    
                    # 如果前端已通过 AMIS Wizard 的 initApi 带回数据
                    if has_actual_data:
                        logger.info("WorkflowExec: GET 已收到 AMIS Wizard initApi 数据")
                        
                        # 保存前端 initApi 回填数据
                        for key, value in actual_form_data.items():
                            session.step_data[key] = value
                        self._merge_request_params_into_session(session.step_data, actual_form_data)
                        self._derive_missing_output_values(current_node, actual_form_data, session.step_data)

                        # 如果前端回传了 API 响应结构，写入会话
                        response_data = self._extract_api_response_from_form(current_node, actual_form_data)
                        if response_data is not None:
                            session.step_data[f"{node_id}_result"] = response_data
                            session.step_data["last_api_result"] = response_data
                            if isinstance(response_data, dict):
                                for key, value in response_data.items():
                                    if key not in ["status", "msg", "message"] and key not in session.step_data:
                                        session.step_data[key] = value


                        self.session_service.update_session_step(
                            user_id=user_id,
                            workflow_id=workflow_id,
                            new_step=node_id,
                            step_data=session.step_data
                        )
                        
                        logger.info(f"WorkflowExec: GET 收到表单数据字段: {list(actual_form_data.keys())}")
                        # 无需再执行后端 API
                    else:
                        # GET 且无实际数据，继续返回当前步骤
                        # AMIS Wizard 仅展示 initApi 配置
                        logger.info("WorkflowExec: GET 未收到 initApi 数据，返回 AMIS Wizard")
                        session = self.session_service.get_active_session(user_id)
                        amis_schema = await self._generate_step_schema(
                            session=session,
                            next_step=node_id,  # 仍停留在当前节点
                            workflow_id=workflow_id,
                            context=context
                        )
                        return WorkflowExecutionResult(
                            success=True,
                            next_step=node_id,
                            amis_schema=amis_schema
                        )

                # POST 请求处理
                elif not auto_ran_current and http_method == "POST":

                    # 🔥 action="submit" 表示用户确认提交，后端需要转发到业务 API
                    if action == "submit":
                        logger.info("WorkflowExec: POST action=submit，后端转发到业务API")
                        
                        # 存储表单数据到会话
                        for key, value in actual_form_data.items():
                            session.step_data[key] = value
                        
                        self.session_service.update_session_step(
                            user_id=user_id,
                            workflow_id=workflow_id,
                            new_step=node_id,
                            step_data=session.step_data
                        )
                        
                        # 🔥 调用业务 API
                        session = self.session_service.get_active_session(user_id)
                        api_result = await self._execute_api_call_node(
                            node=current_node,
                            session_data=session.step_data,
                            context=context
                        )
                        
                        # 存储 API 调用结果
                        if api_result.get("success"):
                            if not self._merge_api_result_into_session(session, node_id, api_result):
                                error_msg = api_result.get("error", "API调用失败")
                                logger.error(f"WorkflowExec: POST API调用失败: {error_msg}")
                                return WorkflowExecutionResult(
                                    success=False,
                                    next_step=None,
                                    amis_schema=self._create_error_schema(f"API调用失败: {error_msg}"),
                                    error=error_msg
                                )

                            self.session_service.update_session_step(
                                user_id=user_id,
                                workflow_id=workflow_id,
                                new_step=node_id,
                                step_data=session.step_data
                            )
                            logger.info(f"WorkflowExec: POST API调用成功，结果已存入会话")
                        else:
                            error_msg = api_result.get("error", "API调用失败")
                            logger.error(f"WorkflowExec: POST API调用失败: {error_msg}")
                            return WorkflowExecutionResult(
                                success=False,
                                next_step=None,
                                amis_schema=self._create_error_schema(f"API调用失败: {error_msg}"),
                                error=error_msg
                            )
                        
                        # 🔥 继续推进到下一步
                    elif has_actual_data:
                        # 🔥 有表单数据但 action != submit：存储数据，继续推进
                        logger.debug("WorkflowExec: POST节点有数据，存储并推进")
                        
                        for key, value in actual_form_data.items():
                            session.step_data[key] = value
                        
                        self.session_service.update_session_step(
                            user_id=user_id,
                            workflow_id=workflow_id,
                            new_step=node_id,
                            step_data=session.step_data
                        )
                    else:
                        # 🔥 POST + action=next 且无数据：用户刚进入节点，生成表单界面
                        logger.info(f"WorkflowExec: POST action={action}，无数据，生成表单界面")
                        session = self.session_service.get_active_session(user_id)
                        amis_schema = await self._generate_step_schema(
                            session=session,
                            next_step=node_id,  # 保持在当前节点
                            workflow_id=workflow_id,
                            context=context
                        )
                        return WorkflowExecutionResult(
                            success=True,
                            next_step=node_id,
                            amis_schema=amis_schema
                        )
            
            # 5. 计算下一步（支持条件分支）
            # 🔥 只有在非 POST+next 的情况下才计算下一步
            next_step = self.session_service.get_next_step(user_id, session.step_data)
            
            if not next_step:
                logger.error("WorkflowExec: 无法确定下一步骤")
                return WorkflowExecutionResult(
                    success=False,
                    next_step=None,
                    amis_schema=self._create_error_schema("无法确定下一步骤"),
                    error="无法确定下一步骤"
                )
            
            # 6. 检查是否工作流完成
            if next_step == "end":
                logger.info("WorkflowExec: 工作流已完成")
                self.session_service.end_session(user_id, "completed")
                completion_node = self._get_node_by_id(session.workflow_data, session.current_step)
                return WorkflowExecutionResult(
                    success=True,
                    next_step=None,
                    amis_schema=self._create_completion_schema(session.step_data, completion_node),
                    workflow_completed=True
                )
            
            logger.info(f"WorkflowExec: 下一步={next_step}")
            
            # 7. 更新会话到下一步
            # 自动推进：连续执行可自动运行的 api_call 节点
            session = self.session_service.get_active_session(user_id)
            auto_guard = 0
            while next_step and next_step != "end" and auto_guard < 10:
                auto_guard += 1
                next_node = self._get_node_by_id(session.workflow_data, next_step)
                if not next_node:
                    break

                next_node_type = next_node.get("type")
                if next_node_type == "api_call":
                    if not self._should_auto_run_api_call(next_node, session.step_data):
                        break
                    logger.info(f"WorkflowExec: 自动执行后续节点 {next_node.get('name')} ({next_step})")
                    api_result = await self._execute_api_call_node(
                        node=next_node,
                        session_data=session.step_data,
                        context=context
                    )
                    if not self._merge_api_result_into_session(session, next_step, api_result):
                        error_msg = api_result.get("error", "API调用失败")
                        logger.error(f"WorkflowExec: 自动执行 API 失败: {error_msg}")
                        return WorkflowExecutionResult(
                            success=False,
                            next_step=None,
                            amis_schema=self._create_error_schema(f"API调用失败: {error_msg}"),
                            error=error_msg
                        )
                elif next_node_type == "notification":
                    if not self._should_auto_run_notification(next_node):
                        break
                    logger.info(f"WorkflowExec: 自动执行通知节点 {next_node.get('name')} ({next_step})")
                    ok, error_msg = await self._run_notification_node_if_needed(
                        node=next_node,
                        workflow_id=workflow_id,
                        node_id=next_step,
                        user_id=user_id,
                        context=context,
                        session=session
                    )
                    if not ok:
                        logger.error(f"WorkflowExec: 自动执行通知失败: {error_msg}")
                        return WorkflowExecutionResult(
                            success=False,
                            next_step=None,
                            amis_schema=self._create_error_schema(f"通知发送失败: {error_msg}"),
                            error=error_msg
                        )
                else:
                    break

                self.session_service.update_session_step(
                    user_id=user_id,
                    workflow_id=workflow_id,
                    new_step=next_step,
                    step_data=session.step_data
                )
                session = self.session_service.get_active_session(user_id)
                next_step = self.session_service.get_next_step(user_id, session.step_data)

                if not next_step:
                    logger.error("WorkflowExec: 无法确定下一步步骤")
                    return WorkflowExecutionResult(
                        success=False,
                        next_step=None,
                        amis_schema=self._create_error_schema("无法确定下一步步骤"),
                        error="无法确定下一步步骤"
                    )
                if next_step == "end":
                    logger.info("WorkflowExec: 工作流已完成")
                    self.session_service.end_session(user_id, "completed")
                    completion_node = self._get_node_by_id(session.workflow_data, session.current_step)
                    return WorkflowExecutionResult(
                        success=True,
                        next_step=None,
                        amis_schema=self._create_completion_schema(session.step_data, completion_node),
                        workflow_completed=True
                    )

            self.session_service.update_session_step(
                user_id=user_id,
                workflow_id=workflow_id,
                new_step=next_step,
                step_data=session.step_data
            )
            
            # 8. 生成下一步的 UI Schema
            # 重新获取会话以确保包含最新的 API 结果
            session = self.session_service.get_active_session(user_id)
            
            amis_schema = await self._generate_step_schema(
                session=session,
                next_step=next_step,
                workflow_id=workflow_id,
                context=context
            )
            
            return WorkflowExecutionResult(
                success=True,
                next_step=next_step,
                amis_schema=amis_schema
            )
            
        except Exception as e:
            logger.error(f"WorkflowExec: 执行失败 {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return WorkflowExecutionResult(
                success=False,
                next_step=None,
                amis_schema=self._create_error_schema(str(e)),
                error=str(e)
            )

    def _should_auto_run_api_call(
        self,
        node: Dict[str, Any],
        session_data: Dict[str, Any]
    ) -> bool:
        """Check if api_call node should auto-run (default auto unless missing params)."""
        node_config = node.get("config", {}) if isinstance(node, dict) else {}
        ui_mode = str(node_config.get("ui_mode") or "auto").lower()
        node_name = node.get("name", "unknown")
        logger.debug(f"WorkflowExec: _should_auto_run_api_call node={node_name}, ui_mode={ui_mode}, config={node_config}")
        if ui_mode == "form":
            logger.info(f"WorkflowExec: 节点 {node_name} ui_mode=form，不自动执行")
            return False
        if self._is_media_preview_node(node):
            logger.info(f"WorkflowExec: 节点 {node_name} 为媒体预览节点，不自动执行")
            return False
        has_missing = self._has_missing_required_params(node, session_data)
        logger.debug(f"WorkflowExec: 节点 {node_name} has_missing_params={has_missing}")
        return not has_missing

    def _is_media_preview_node(self, node: Dict[str, Any]) -> bool:
        if not isinstance(node, dict):
            return False
        config = node.get("config") if isinstance(node.get("config"), dict) else {}
        endpoint = str(config.get("api_endpoint") or "").lower()
        desc = str(node.get("description") or "").lower()
        name = str(node.get("name") or "").lower()
        media_suffixes = (".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp3", ".wav", ".mp4")
        if any(endpoint.endswith(suffix) for suffix in media_suffixes):
            return True
        media_keywords = ("preview", "media", "file", "附件", "文件预览")
        return any(keyword in desc or keyword in name for keyword in media_keywords)

    def _should_auto_run_notification(self, node: Dict[str, Any]) -> bool:
        """通知节点默认静默执行；仅在 ui_mode=form 时渲染页面。"""
        config = node.get("config", {}) if isinstance(node, dict) else {}
        ui_mode = str(config.get("ui_mode") or "auto").lower()
        if ui_mode == "form":
            logger.info(f"WorkflowExec: 通知节点 {node.get('name', 'unknown')} ui_mode=form，不自动执行")
            return False
        return True

    async def _run_notification_node_if_needed(
        self,
        node: Dict[str, Any],
        workflow_id: str,
        node_id: str,
        user_id: str,
        context: Dict[str, Any],
        session
    ) -> Tuple[bool, Optional[str]]:
        """执行通知节点并合并结果，自动去重。"""
        sent_flag_key = f"__notification_sent__:{node_id}"
        if session.step_data.get(sent_flag_key):
            logger.debug(f"WorkflowExec: 通知节点 {node_id} 已执行过，跳过重复发送")
            return True, None

        notification_result = await self._execute_notification_node(
            node=node,
            workflow_id=workflow_id,
            node_id=node_id,
            user_id=user_id,
            session_data=session.step_data,
            context=context,
        )
        if not notification_result.get("success"):
            return False, notification_result.get("error", "通知发送失败")

        payload = notification_result.get("data")
        session.step_data[sent_flag_key] = True
        if payload is not None:
            session.step_data[f"{node_id}_result"] = payload
            session.step_data["last_notification_result"] = payload

        self.session_service.update_session_step(
            user_id=user_id,
            workflow_id=workflow_id,
            new_step=node_id,
            step_data=session.step_data
        )
        return True, None

    def _has_missing_required_params(
        self,
        node: Dict[str, Any],
        session_data: Dict[str, Any]
    ) -> bool:
        config = node.get("config", {}) if isinstance(node, dict) else {}
        parameters = config.get("parameters", {}) or {}
        required_param_names = self._get_required_param_names(node=node)

        inputs = node.get("inputs", []) or []
        for item in inputs:
            if not isinstance(item, dict):
                continue
            if item.get("required", True) is False:
                continue
            name = item.get("name")
            if name and (name not in session_data or session_data.get(name) in (None, "", [], {})):
                return True

        resolved_params = parameters
        try:
            resolved_params = self.api_executor._resolve_template_variables(parameters, session_data)
        except Exception:
            pass

        if isinstance(resolved_params, dict) and required_param_names:
            for name in required_param_names:
                value = resolved_params.get(name, session_data.get(name))
                if value is None:
                    return True
                if isinstance(value, str):
                    if value.strip() == "":
                        return True
                    if "${" in value:
                        return True

        endpoint = config.get("api_endpoint") or ""
        if endpoint:
            path_params = {}
            if isinstance(resolved_params, dict):
                path_params.update(resolved_params)
            for key, value in session_data.items():
                if key not in path_params:
                    path_params[key] = value
            actual_endpoint = self.api_executor._substitute_path_params(endpoint, path_params)
            if "{" in actual_endpoint:
                return True
        return False

    def _get_required_param_names(self, node: Dict[str, Any]) -> set[str]:
        """获取节点运行所需的必填参数名（通用规则，不依赖具体业务字段）。"""
        required: set[str] = set()
        if not isinstance(node, dict):
            return required

        config = node.get("config", {}) if isinstance(node.get("config"), dict) else {}
        endpoint = str(config.get("api_endpoint") or "")
        method = str(config.get("method") or "GET").upper()
        api_id = config.get("api_id")

        # 路径参数天然必填
        required.update(re.findall(r"\{(\w+)\}", endpoint))

        # 优先使用 API 路由元数据中的 required 标记
        try:
            route = self.api_executor._find_api_route(
                api_id=api_id,
                endpoint=endpoint,
                method=method
            )
            route_params = route.get("parameters_config") if isinstance(route, dict) else None
            if isinstance(route_params, list):
                for param in route_params:
                    if not isinstance(param, dict):
                        continue
                    name = param.get("name")
                    if not name:
                        continue
                    if bool(param.get("required")):
                        required.add(str(name))
        except Exception:
            pass

        return required

    def _merge_api_result_into_session(
        self,
        session,
        node_id: str,
        api_result: Dict[str, Any]
    ) -> bool:
        if not api_result.get("success"):
            return False
        result_data = api_result.get("data", {})
        payload = result_data
        response_code = None
        if isinstance(result_data, dict):
            response_code = result_data.get("code")
            if isinstance(result_data.get("data"), dict):
                payload = result_data.get("data")

        # Store payload for templating/conditions
        if isinstance(payload, dict) and "payment_success" not in payload:
            if response_code is not None:
                payload["payment_success"] = (response_code == 200)
            elif node_id and "payment" in str(node_id).lower():
                payload["payment_success"] = True

        session.step_data[f"{node_id}_result"] = payload
        session.step_data["last_api_result"] = payload

        if isinstance(payload, dict):
            for key, value in payload.items():
                # API 输出应覆盖同名旧值，避免分支判断使用到历史脏数据（如 verified）。
                if key not in ["status", "msg", "message"]:
                    session.step_data[key] = value
        return True

    def _resolve_notification_message(
        self,
        node: Dict[str, Any],
        session_data: Dict[str, Any]
    ) -> str:
        """构建通知消息并替换 ${field} 变量。"""
        config = node.get("config", {}) if isinstance(node, dict) else {}
        ai_instructions = node.get("ai_instructions", {}) if isinstance(node, dict) else {}

        raw_message = (
            config.get("message")
            or config.get("message_template")
            or ai_instructions.get("action")
            or node.get("description")
            or node.get("name")
            or "系统通知"
        )

        def _replace_var(match: re.Match[str]) -> str:
            key = match.group(1)
            value = session_data.get(key)
            if value is None:
                return match.group(0)
            if isinstance(value, (dict, list)):
                try:
                    return json.dumps(value, ensure_ascii=False, default=str)
                except Exception:
                    return str(value)
            return str(value)

        return re.sub(r"\$\{(\w+)\}", _replace_var, str(raw_message))

    async def _execute_notification_node(
        self,
        node: Dict[str, Any],
        workflow_id: str,
        node_id: str,
        user_id: str,
        session_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行通知节点（固定服务调用，不依赖动态路由）。"""
        config = node.get("config", {}) if isinstance(node, dict) else {}
        notification_type = (
            config.get("notification_type")
            or config.get("type")
        )
        if not notification_type:
            # 配置缺失时基于文案语义推断通知级别（兼容旧节点数据）
            ai_instructions = node.get("ai_instructions", {}) if isinstance(node, dict) else {}
            infer_text = " ".join(
                str(x or "")
                for x in [
                    node.get("name"),
                    node.get("description"),
                    ai_instructions.get("action"),
                    ai_instructions.get("success_handling"),
                    ai_instructions.get("user_message"),
                ]
            )
            if re.search(r"成功|完成|已", infer_text):
                notification_type = "success"
            elif re.search(r"失败|错误|异常|拒绝", infer_text):
                notification_type = "error"
            elif re.search(r"警告|提醒|注意", infer_text):
                notification_type = "warning"
            else:
                notification_type = "info"
        channel = config.get("channel") or "in_app"
        title = node.get("name") or "流程通知"
        message = self._resolve_notification_message(node, session_data)
        workflow_session_id = context.get("session_id") or f"{user_id}:{workflow_id}"
        idempotency_key = f"wf:{workflow_id}:node:{node_id}:session:{workflow_session_id}"

        request_data = {
            "body": {
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "channel": channel,
                "user_id": user_id,
                "idempotency_key": idempotency_key,
            }
        }
        route_config = {"handler_config": {"persist": True}}

        from app.services.service_dispatcher import dispatch_service_call

        result = await dispatch_service_call(
            "notification_service",
            "send_notification",
            request_data=request_data,
            route_config=route_config,
        )

        code = int(result.get("code", 500))
        if 200 <= code < 300:
            logger.info(
                f"WorkflowExec: 通知节点发送成功 node={node_id}, type={notification_type}, user={user_id}"
            )
            return {"success": True, "data": result.get("data")}

        logger.error(
            f"WorkflowExec: 通知节点发送失败 node={node_id}, code={code}, message={result.get('message')}"
        )
        return {
            "success": False,
            "error": result.get("message", "通知发送失败"),
            "data": result.get("data"),
        }

    async def _execute_api_call_node(
        self,
        node: Dict[str, Any],
        session_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行 api_call 类型节点的业务 API 调用
        
        Args:
            node: 节点配置
            session_data: 会话数据
            context: 上下文
        
        Returns:
            API 调用结果
        """
        node_id = node.get("id", "unknown")
        node_name = node.get("name", "未知节点")
        node_config = node.get("config", {}) if isinstance(node, dict) else {}
        
        logger.info(f"APICall: 执行节点 {node_name} ({node_id})")
        logger.debug(f"APICall: 节点配置 {json.dumps(node_config, ensure_ascii=False, default=str)}")
        logger.debug(f"APICall: 会话数据 {json.dumps(session_data, ensure_ascii=False, default=str)}")
        
        # 🔥 优先从会话数据中获取 api_url 和 api_method（前端传递的）
        # 这样可以支持 AI 生成的动态 API 配置
        api_endpoint = session_data.get("api_url") or node_config.get("api_endpoint")
        method = session_data.get("api_method") or node_config.get("method", "GET")
        
        # 获取 API 配置
        api_id = node_config.get("api_id")
        parameters = node_config.get("parameters", {})
        
        if not api_id and not api_endpoint:
            logger.warning(f"APICall: 节点{node_id}未配置api_id或api_endpoint")
            return {"success": False, "error": "节点未配置 API", "data": None}
        
        # 🔥 构建增强的节点配置（包含从表单数据中提取的 API 信息）
        enhanced_node_config = {
            **node_config,
            "api_endpoint": api_endpoint,
            "method": method
        }
        
        logger.info(f"APICall: 使用 API 配置 endpoint={api_endpoint}, method={method}")
        
        # 获取用户 token
        user_token = context.get("user_token")
        accessible_apis = context.get("accessible_apis", [])
        
        # 调用 API 执行服务
        result = await self.api_executor.execute_api(
            node_config=enhanced_node_config,
            session_data=session_data,
            user_token=user_token,
            accessible_apis=accessible_apis
        )
        
        logger.info(f"APICall: 调用结果 success={result.get('success')}, endpoint={result.get('endpoint')}")
        
        return result
    
    async def _create_or_update_session(
        self,
        user_id: str,
        workflow_id: str,
        node_id: str
    ) -> tuple:
        """
        创建或更新工作流会话
        
        Returns:
            tuple: (session, validated_node_id)
        """
        # 获取工作流详情
        wf_result = self.workflow_service.get_workflow_detail(workflow_id)
        if not wf_result.get("success"):
            logger.error(f"WorkflowExec: 工作流不存在 {workflow_id}")
            return None, node_id
        
        workflow_data = wf_result["data"]["workflow"]
        
        # 创建会话
        session = self.session_service.create_session(user_id, workflow_id, workflow_data)
        
        # 验证 node_id
        valid_node_ids = {n.get("id") for n in workflow_data.get("nodes", [])}
        if node_id not in valid_node_ids:
            # node_id 不存在，使用第一个有效节点
            first_valid_node = None
            for n in workflow_data.get("nodes", []):
                if n.get("type") not in ("start", "end"):
                    first_valid_node = n.get("id")
                    break
            
            if first_valid_node:
                logger.warning(f"WorkflowExec: node_id '{node_id}'不存在，使用第一个有效节点 {first_valid_node}")
                node_id = first_valid_node
            else:
                logger.warning(f"WorkflowExec: node_id '{node_id}'不存在，且无法找到有效节点")
        
        # 更新 current_step
        self.session_service.update_session_step(
            user_id=user_id,
            workflow_id=workflow_id,
            new_step=node_id,
            step_data={}
        )
        
        logger.info(f"WorkflowExec: 创建新会话 workflow={workflow_id}, node={node_id}")
        return session, node_id
    
    def _validate_node_id(self, session, node_id: str) -> str:
        """
        验证 node_id 是否存在于工作流中
        
        Returns:
            str: 验证后的 node_id
        """
        workflow_data = session.workflow_data
        valid_node_ids = {n.get("id") for n in workflow_data.get("nodes", [])}
        
        if node_id not in valid_node_ids:
            logger.warning(f"WorkflowExec: node_id '{node_id}'不存在，使用当前会话步骤 {session.current_step}")
            return session.current_step
        
        return node_id
    
    async def _generate_step_schema(
        self,
        session,
        next_step: str,
        workflow_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成下一步的 UI Schema（优先 Celery AI，失败时规则降级）
        
        Args:
            session: 工作流会话
            next_step: 下一步节点 ID
            workflow_id: 工作流 ID
            context: 上下文
        
        Returns:
            AMIS Schema
        """
        try:
            # 获取下一步节点信息
            current_node = self._get_node_by_id(session.workflow_data, next_step)
            
            if not current_node:
                logger.error(f"WorkflowExec: 未找到节点 {next_step}")
                return self._create_error_schema(f"未找到节点: {next_step}")
            
            logger.info(f"WorkflowExec: 生成步骤Schema node={next_step}（优先 Celery AI）")
            
            # 准备上下文数据（扁平化）
            workflow_context_data = None
            if session.step_data:
                workflow_context_data = self._flatten_context_data(session.step_data)
                logger.debug(f"WorkflowExec: 上下文数据 {workflow_context_data}")
            
            # 构建用户指令（从节点描述或 AI 指令中提取）
            ai_instructions = current_node.get("ai_instructions", {})
            if not isinstance(ai_instructions, dict):
                ai_instructions = {}
            user_instruction = ai_instructions.get("user_message", current_node.get("description", ""))
            if not user_instruction:
                user_instruction = current_node.get("name", "请完成当前步骤")

            # 1) 优先走 AI AMIS（底层通过 pure_llm_model_service -> Celery worker 推理）
            try:
                from app.services.ai_amis_service import ai_amis_service

                accessible_apis = context.get("accessible_apis", []) if isinstance(context, dict) else []
                workflows = self.workflow_service.get_active_workflows_for_ai()
                ai_result = await ai_amis_service.generate_schema(
                    command=user_instruction,
                    accessible_apis=accessible_apis,
                    workflows=workflows,
                    current_workflow_node=current_node,
                    current_workflow_id=workflow_id,
                    context="workflow_step",
                    workflow_context_data=workflow_context_data or {}
                )
                if ai_result.get("success") and ai_result.get("amis_schema"):
                    logger.info(f"WorkflowExec: Celery AI 步骤Schema生成成功 node={next_step}")
                    return ai_result["amis_schema"]
                logger.warning(
                    "WorkflowExec: Celery AI 步骤Schema生成失败，降级规则生成。"
                    f" error={ai_result.get('error')}"
                )
            except Exception as ai_err:
                logger.warning(f"WorkflowExec: Celery AI 生成异常，降级规则生成: {ai_err}")

            # 2) 降级：规则生成器（保证可用性）
            slot_values = self._build_rule_slot_values(
                workflow=session.workflow_data,
                node=current_node,
                context_data=workflow_context_data or {}
            )
            from app.services.amis_schema_generator import amis_schema_generator
            return amis_schema_generator.generate_workflow_step_form(
                workflow=session.workflow_data,
                node=current_node,
                context_data=workflow_context_data,
                user_instruction=user_instruction,
                slot_values=slot_values
            )
                 
        except Exception as e:
            logger.error(f"WorkflowExec: 生成步骤Schema失败 {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return self._create_error_schema(str(e))

    def _build_rule_slot_values(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建规则槽位值，避免主后端触发 AI 槽填充。"""
        slot_values: Dict[str, Any] = {}

        workflow_name = workflow.get("name", "")
        node_name = node.get("name", "")
        node_desc = node.get("description", "")
        ai_instructions = node.get("ai_instructions", {})
        if not isinstance(ai_instructions, dict):
            ai_instructions = {}

        page_title = ai_instructions.get("page_title") or (node_name[:8] if node_name else workflow_name[:8] or "流程步骤")
        user_message = ai_instructions.get("user_message") or node_desc or f"请完成{node_name or '当前步骤'}"

        slot_values["page_title"] = page_title
        slot_values["user_message"] = user_message
        slot_values["submit_button_text"] = ai_instructions.get("submit_button_text") or "提交"
        slot_values["next_button_text"] = ai_instructions.get("next_button_text") or "下一步"
        slot_values["cancel_button_text"] = ai_instructions.get("cancel_button_text") or "取消"
        slot_values["reset_button_text"] = ai_instructions.get("reset_button_text") or "重置"

        config = node.get("config", {}) if isinstance(node.get("config"), dict) else {}
        api_endpoint = config.get("api_endpoint")
        api_method = config.get("method")
        if api_endpoint:
            slot_values["api_url"] = api_endpoint
        if api_method:
            slot_values["api_method"] = str(api_method).upper()

        def _humanize_field_name(field_name: str) -> str:
            base = (field_name or "").split(".")[-1].strip()
            if not base:
                return field_name or ""
            if any("\u4e00" <= ch <= "\u9fff" for ch in base):
                return base
            base = re.sub(r"[_\\-]+", " ", base).strip()
            if not base:
                return field_name or ""
            return base.title()

        def _resolve_field_label(field_name: str, label: Optional[str]) -> str:
            if not field_name:
                return ""
            candidate = (label or "").strip()
            if candidate and candidate != field_name:
                return candidate

            # 优先复用实体字段元数据（display_name / alias）
            try:
                from app.services.entity_service import entity_service
                entity_label = entity_service.get_field_label(field_name)
                if entity_label:
                    return entity_label
            except Exception:
                pass

            return _humanize_field_name(field_name)

        def _put_field_label(field_name: str, label: str) -> None:
            if not field_name:
                return
            key = f"field_label_{field_name}"
            if key not in slot_values:
                resolved = _resolve_field_label(field_name, label)
                slot_values[key] = resolved or field_name

        for field in node.get("inputs", []) or []:
            if isinstance(field, dict):
                _put_field_label(field.get("name", ""), field.get("label") or field.get("description") or field.get("name", ""))

        for field in node.get("outputs", []) or []:
            if isinstance(field, dict):
                _put_field_label(field.get("name", ""), field.get("label") or field.get("description") or field.get("name", ""))

        parameters = config.get("parameters", {})
        if isinstance(parameters, dict):
            for param_name in parameters.keys():
                _put_field_label(str(param_name), "")

        for key in (context_data or {}).keys():
            if isinstance(key, str) and key and key not in {"workflow_id", "node_id", "action"}:
                _put_field_label(key, "")

        return slot_values
    
    def _flatten_context_data(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        扁平化上下文数据，与数据集格式保持一致
        
        数据集格式是扁平的：{"ticket_id": "xxx", "amount": 100}
        运行时可能是：
        - {"parameters": {"ticket_id": "xxx"}}
        - {"ticket_id": "xxx", "last_api_result": {...}}
        - {"input": {"ticket_id": "xxx", "passenger_id": "222"}}  # 🔥 用户输入
        - 直接扁平的数据
        
        Args:
            step_data: 会话中的步骤数据
        
        Returns:
            扁平化后的上下文数据
        """
        flat_context = {}
        
        # 需要排除的控制字段和元数据字段
        exclude_keys = {
            "workflow_id",
            "node_id",
            "action",
            "&",
            "last_api_result",
            "submit_text",
            "api_request",
            "form_data",
        }

        def _unwrap_response(payload: Dict[str, Any]) -> Any:
            if not isinstance(payload, dict):
                return payload
            if "data" in payload:
                meta_keys = {"code", "message", "timestamp", "request_id", "api_info", "status", "msg", "success"}
                other_keys = set(payload.keys()) - {"data"}
                if other_keys and other_keys.issubset(meta_keys):
                    return payload.get("data")
            return payload
        
        for key, value in step_data.items():
            if key in exclude_keys:
                continue
            
            # 🔥 如果是 input 字典（用户输入），展开它
            if key == "input" and isinstance(value, dict):
                for input_key, input_value in value.items():
                    # 🔥 过滤掉字段定义（包含 name, label, required 等键的字典）
                    if isinstance(input_value, dict) and any(k in input_value for k in ["name", "label", "required", "type"]):
                        # 这是字段定义，不是实际值，跳过
                        logger.debug(f"跳过字段定义: {input_key}={input_value}")
                        continue
                    # 这是实际值，添加到上下文
                    if input_key not in exclude_keys:
                        flat_context[input_key] = input_value
                        logger.debug(f"提取用户输入: {input_key}={input_value}")
            # 如果是 parameters 字典，展开它
            elif key == "parameters" and isinstance(value, dict):
                for param_key, param_value in value.items():
                    if param_key not in exclude_keys:
                        flat_context[param_key] = param_value
            # 如果是 API 响应或 xxx_result 格式（API 返回结果），展开它
            elif key in ("api_response", "__api_response__") and isinstance(value, dict):
                payload = _unwrap_response(value)
                if isinstance(payload, dict):
                    for result_key, result_value in payload.items():
                        if result_key not in exclude_keys and result_key not in flat_context:
                            flat_context[result_key] = result_value
            elif key.endswith("_result") and isinstance(value, dict):
                payload = _unwrap_response(value)
                if isinstance(payload, dict):
                    for result_key, result_value in payload.items():
                        if result_key not in exclude_keys and result_key not in flat_context:
                            flat_context[result_key] = result_value
                else:
                    if key not in flat_context:
                        flat_context[key] = payload
            # 🔥 其他普通字段：只添加简单类型的值（字符串、数字、布尔）
            elif not isinstance(value, dict):
                flat_context[key] = value
        
        return flat_context

    def _extract_api_response_from_form(self, node: Dict[str, Any], form_data: Dict[str, Any]) -> Optional[Any]:
        """
        从表单数据中提取 API 响应结果。

        优先顺序：
        1) api_response / __api_response__ 显式字段
        2) 根据 outputs 定义提取字段
        3) 兜底：去除控制字段后的剩余数据
        """
        if not form_data:
            return None

        # 显式响应字段（优先提取 data，避免上下文过长）
        for key in ("api_response", "__api_response__"):
            if key in form_data:
                raw_response = form_data.get(key)
                if isinstance(raw_response, dict) and "data" in raw_response:
                    response_data = raw_response.get("data")
                    if isinstance(response_data, dict):
                        # 补全常见字段别名，保持上下文一致
                        request_params = None
                        api_request = form_data.get("api_request")
                        if isinstance(api_request, dict):
                            request_params = api_request.get("params") if isinstance(api_request.get("params"), dict) else None
                        if request_params:
                            for k, v in request_params.items():
                                if k not in response_data:
                                    response_data[k] = v
                    return response_data
                return raw_response

        # 根据 outputs 提取
        outputs = node.get("outputs", []) if isinstance(node, dict) else []
        if outputs:
            response = {}
            for output in outputs:
                name = output.get("name") if isinstance(output, dict) else None
                if name and name in form_data:
                    response[name] = form_data[name]
            if response:
                return response

        # 兜底：剔除控制字段
        control_fields = {
            "workflow_id",
            "node_id",
            "action",
            "&",
            "api_request",
            "api_response",
            "__api_response__",
        }
        fallback = {k: v for k, v in form_data.items() if k not in control_fields}
        return fallback or None

    def _merge_request_params_into_session(self, session_data: Dict[str, Any], form_data: Dict[str, Any]) -> None:
        """Merge api_request.params values back into session data when they are not present."""
        if not isinstance(session_data, dict) or not isinstance(form_data, dict):
            return
        api_request = form_data.get("api_request")
        if not isinstance(api_request, dict):
            return
        params = api_request.get("params")
        if not isinstance(params, dict):
            return
        for key, value in params.items():
            if key not in session_data or session_data.get(key) in (None, "", [], {}):
                session_data[key] = value

    def _derive_missing_output_values(
        self,
        node: Dict[str, Any],
        form_data: Dict[str, Any],
        session_data: Dict[str, Any]
    ) -> None:
        """
        Derive missing scalar outputs (especially numeric price/amount fields) from selected list items.
        This keeps workflow context complete even when those fields are hidden/read-only in UI.
        """
        if not isinstance(node, dict) or not isinstance(form_data, dict) or not isinstance(session_data, dict):
            return

        outputs = node.get("outputs") or []
        if not isinstance(outputs, list):
            return

        # Find candidate list payload in submitted form data.
        list_rows = None
        for value in form_data.values():
            if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
                list_rows = value
                break
        if not list_rows:
            return

        def _guess_item_field(output_name: str) -> List[str]:
            candidates: List[str] = []
            if not output_name:
                return candidates
            candidates.append(output_name)
            if output_name.startswith("selected_"):
                candidates.append(output_name[len("selected_"):])
            if output_name.endswith("_price"):
                candidates.extend(["price", "fare", "cost"])
            if output_name.endswith("_amount"):
                candidates.extend(["amount", "total_amount", "price"])
            if output_name.endswith("_count"):
                candidates.extend(["count", "quantity", "num"])
            # keep order and remove duplicates
            seen = set()
            ordered = []
            for c in candidates:
                if c and c not in seen:
                    seen.add(c)
                    ordered.append(c)
            return ordered

        selectors: List[tuple[str, Any]] = []
        for key, value in form_data.items():
            if value in (None, "", [], {}):
                continue
            if not isinstance(value, (str, int, float, bool)):
                continue
            key_lower = str(key).lower()
            if (
                key_lower.startswith("selected_")
                or key_lower.endswith(("_id", "_code", "_number", "_no", "_type", "_seat"))
            ):
                selectors.append((str(key), value))

        def _match_row(selector_key: str, selector_value: Any, row: Dict[str, Any]) -> bool:
            if selector_key in row and row.get(selector_key) == selector_value:
                return True
            if selector_key.startswith("selected_"):
                suffix = selector_key[len("selected_"):]
                if suffix in row and row.get(suffix) == selector_value:
                    return True
                if suffix == "seat" and row.get("seat_number") == selector_value:
                    return True
            return False

        for output in outputs:
            if not isinstance(output, dict):
                continue
            output_name = output.get("name")
            output_type = str(output.get("type", "string")).lower()
            if not output_name or output_type not in ("number", "integer", "float"):
                continue
            if session_data.get(output_name) not in (None, "", [], {}):
                continue
            if form_data.get(output_name) not in (None, "", [], {}):
                session_data[output_name] = form_data.get(output_name)
                continue

            candidate_fields = _guess_item_field(output_name)
            if not candidate_fields:
                continue

            matched_row = None
            for selector_key, selector_value in selectors:
                for row in list_rows:
                    if _match_row(selector_key, selector_value, row):
                        matched_row = row
                        break
                if matched_row:
                    break

            # Fallback to the first row when no explicit selector matches.
            if not matched_row and len(list_rows) == 1:
                matched_row = list_rows[0]

            if not matched_row:
                continue

            derived_value = None
            for field_name in candidate_fields:
                if field_name in matched_row:
                    derived_value = matched_row.get(field_name)
                    if derived_value not in (None, "", [], {}):
                        break
            if derived_value in (None, "", [], {}):
                continue

            session_data[output_name] = derived_value
            form_data[output_name] = derived_value
            logger.debug(f"WorkflowExec: 派生输出字段 {output_name}={derived_value}")
    
    def _get_node_by_id(self, workflow_data: Dict[str, Any], node_id: str) -> Optional[Dict[str, Any]]:
        """从工作流定义中获取节点"""
        nodes = workflow_data.get("nodes", [])
        for node in nodes:
            if node.get("id") == node_id:
                return node
        return None
    
    def _create_error_schema(self, error_message: str) -> Dict[str, Any]:
        """创建错误提示的 AMIS Schema"""
        return {
            "type": "page",
            "body": {
                "type": "alert",
                "level": "danger",
                "title": "执行失败",
                "body": error_message,
                "showIcon": True
            }
        }
    
    def _create_completion_schema(
        self,
        session_data: Optional[Dict[str, Any]] = None,
        current_node: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建工作流完成的 AMIS Schema"""
        level = "success"
        title = "操作完成"
        body = "工作流已成功完成！"
        is_failure = False

        if isinstance(session_data, dict):
            verified = session_data.get("verified")
            failure_reason = session_data.get("failure_reason")
            if verified is False:
                is_failure = True
                level = "warning"
                title = "身份验证失败"
                body = f"身份验证失败：{failure_reason or '未通过实名校验'}"
            elif failure_reason:
                is_failure = True
                level = "warning"
                title = "流程结束"
                body = f"执行未通过：{failure_reason}"

        # 支持开发者在节点 AI 指令中配置结束页文案（开发者配置 -> 工作流设计 -> 节点编辑）
        # - 失败时读取 ai_instructions.error_handling
        # - 成功时读取 ai_instructions.success_handling
        ai_instructions = (current_node or {}).get("ai_instructions") or {}
        if isinstance(ai_instructions, dict):
            template = ai_instructions.get("error_handling") if is_failure else ai_instructions.get("success_handling")
            if isinstance(template, str) and template.strip():
                body = template.strip()
                if isinstance(session_data, dict):
                    failure_reason = str(session_data.get("failure_reason") or "")
                    body = body.replace("{failure_reason}", failure_reason).replace("{{failure_reason}}", failure_reason)

        return {
            "type": "page",
            "body": [
                {
                    "type": "alert",
                    "level": level,
                    "title": title,
                    "body": body,
                    "showIcon": True
                },
                {
                    "type": "button",
                    "label": "返回首页",
                    "level": "primary",
                    "onEvent": {
                        "click": {
                            "actions": [
                                {
                                    "actionType": "custom",
                                    "script": "window.location.reload();"
                                }
                            ]
                        }
                    }
                }
            ]
        }


# 全局实例
workflow_execution_service = WorkflowExecutionService()
