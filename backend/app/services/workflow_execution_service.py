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
from copy import deepcopy
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
        control_fields = {"workflow_id", "node_id", "action", "&", "instance_id"}
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
    
    async def execute_step(self, user_id, workflow_id, node_id, form_data, context):
        """同一用户串行提交，在任何业务调用前校验实例和当前节点，阻止旧表单重放。"""
        try:
            async with self.session_service.execution_lock(user_id):
                return await self._execute_step_locked(
                    user_id, workflow_id, node_id, form_data or {}, context or {}
                )
        except Exception as exc:
            logger.exception("工作流步骤执行失败")
            return WorkflowExecutionResult(
                success=False, next_step=None, amis_schema=self._create_error_schema(str(exc)), error=str(exc)
            )

    @staticmethod
    def _submission_data(form_data):
        """兼容嵌套 form_data 和 params，剔除控制字段以免污染业务上下文。"""
        data = dict(form_data)
        nested = data.pop("form_data", None)
        if isinstance(nested, str):
            nested = json.loads(nested)
        if nested is not None and not isinstance(nested, dict):
            raise ValueError("form_data 必须是对象")
        data = {**(nested or {}), **data}
        params = data.pop("params", None)
        if isinstance(params, dict):
            data = {**params, **data}
        control = {"workflow_id", "node_id", "action", "&", "api_url", "api_method", "instance_id",
                   "user_token", "accessible_apis"}
        return {key: value for key, value in data.items()
                if key not in control and (not key.startswith("__") or key == "__api_response__")}

    async def _execute_step_locked(self, user_id, workflow_id, node_id, form_data, context):
        """执行当前节点、保存结果，再依次推进自动节点，遇到表单时停止等待。"""
        action = context.get("action", "next")
        if action not in {"next", "submit"}:
            raise ValueError("不支持的工作流操作")
        session = self.session_service.get_active_session(user_id)
        if context.get("instance_id") and (session is None or session.id != context["instance_id"]):
            raise ValueError("表单属于已结束或已过期的工作流实例，请重新打开当前步骤")
        if session is None or session.workflow_id != workflow_id:
            session, node_id = await self._create_or_update_session(user_id, workflow_id, node_id)
            if session is None:
                raise ValueError("工作流不存在或无法执行")
        else:
            node_id = self._validate_node_id(session, node_id)
        if context.get("instance_id") and context["instance_id"] != session.id:
            raise ValueError("表单属于已结束的工作流实例，请重新打开当前步骤")
        context = {**context, "instance_id": session.id}
        data = self._submission_data(form_data)
        if not self.session_service.update_session_step(user_id, workflow_id, node_id, data):
            raise ValueError("工作流会话已过期，请重新开始")
        session = self.session_service.get_active_session(user_id)
        current = self._get_node_by_id(session.workflow_data, node_id)
        if current is None:
            raise ValueError("当前工作流节点不存在")
        if current.get("type") == "end":
            return self._finish_workflow(user_id, workflow_id, session, current)

        if current.get("type") == "api_call":
            method = str((current.get("config") or {}).get("method") or "GET").upper()
            auto = self._should_auto_run_api_call(current, session.step_data)
            response = next((data[key] for key in ("api_response", "__api_response__") if key in data), None)
            if method in {"GET", "HEAD"} and response is not None:
                from app.services.workflow_context import response_error
                error = response_error(response)
                if error:
                    raise ValueError(error)
                self._merge_request_params_into_session(session.step_data, data)
                self._derive_missing_output_values(current, data, session.step_data)
                payload = self._extract_api_response_from_form(current, data)
                self._merge_api_result_into_session(session, node_id, {"success": True, "data": payload})
            elif method in {"GET", "HEAD"} and data and not auto:
                self._merge_request_params_into_session(session.step_data, data)
                self._derive_missing_output_values(current, data, session.step_data)
                payload = self._extract_api_response_from_form(current, data)
                self._merge_api_result_into_session(session, node_id, {"success": True, "data": payload})
            elif auto or action == "submit":
                if self._has_missing_required_params(current, session.step_data):
                    raise ValueError("当前步骤缺少必填参数")
                result = await self._execute_api_call_node(current, session.step_data, context)
                if not self._merge_api_result_into_session(session, node_id, result):
                    raise ValueError(result.get("error") or "业务 API 执行失败")
            else:
                return await self._waiting_schema(session, workflow_id, node_id, context)
        elif current.get("type") == "notification":
            if not self._should_auto_run_notification(current) and action == "next" and not data:
                return await self._waiting_schema(session, workflow_id, node_id, context)
            ok, error = await self._run_notification_node_if_needed(
                current, workflow_id, node_id, user_id, context, session
            )
            if not ok:
                raise ValueError(error or "通知执行失败")
            session = self.session_service.get_active_session(user_id)
        elif current.get("type") == "user_input" and action == "next" and not data:
            return await self._waiting_schema(session, workflow_id, node_id, context)

        self.session_service.update_session_step(user_id, workflow_id, node_id, session.step_data)
        self.session_service.mark_step_completed(
            user_id, node_id, data, session.step_data.get(f"{node_id}_result")
        )
        session = self.session_service.get_active_session(user_id)
        next_step = self.session_service.get_next_step(user_id, session.step_data)
        visited = {node_id}
        for _ in range(100):
            if not next_step:
                raise ValueError("没有满足条件的后续步骤，请检查分支配置")
            node = self._get_node_by_id(session.workflow_data, next_step)
            if node is None:
                raise ValueError("后续步骤不存在")
            if node.get("type") == "end":
                return self._finish_workflow(user_id, workflow_id, session, node)
            kind = node.get("type")
            automatic = (
                kind in {"start", "condition"}
                or (kind == "api_call" and self._should_auto_run_api_call(node, session.step_data))
                or (kind == "notification" and self._should_auto_run_notification(node))
            )
            if not automatic:
                self.session_service.update_session_step(user_id, workflow_id, next_step, session.step_data)
                session = self.session_service.get_active_session(user_id)
                return await self._waiting_schema(session, workflow_id, next_step, context)
            if next_step in visited:
                raise ValueError("检测到自动执行循环，请检查工作流连线")
            visited.add(next_step)
            # 先保存真正要执行的节点，API 失败后重试才不会从前一步重复写入。
            self.session_service.update_session_step(user_id, workflow_id, next_step, session.step_data)
            session = self.session_service.get_active_session(user_id)
            if kind == "api_call":
                result = await self._execute_api_call_node(node, session.step_data, context)
                if not self._merge_api_result_into_session(session, next_step, result):
                    raise ValueError(result.get("error") or "业务 API 执行失败")
            elif kind == "notification":
                ok, error = await self._run_notification_node_if_needed(
                    node, workflow_id, next_step, user_id, context, session
                )
                if not ok:
                    raise ValueError(error or "通知执行失败")
                session = self.session_service.get_active_session(user_id)
            self.session_service.update_session_step(user_id, workflow_id, next_step, session.step_data)
            self.session_service.mark_step_completed(
                user_id, next_step, {}, session.step_data.get(f"{next_step}_result")
            )
            session = self.session_service.get_active_session(user_id)
            next_step = self.session_service.get_next_step(user_id, session.step_data)
        raise ValueError("工作流自动执行超过 100 步，请检查循环")

    async def _waiting_schema(self, session, workflow_id, node_id, context):
        """生成待提交界面，并把每个提交 API 绑定到当前实例和节点。"""
        from app.services.workflow_context import bind_workflow_schema
        schema = await self._generate_step_schema(session, node_id, workflow_id, context)
        schema = bind_workflow_schema(schema, session, node_id)
        return WorkflowExecutionResult(success=True, next_step=node_id, amis_schema=schema)

    def _finish_workflow(self, user_id, workflow_id, session, end_node):
        """记录实际结束节点，结束会话并返回完成界面。"""
        self.session_service.update_session_step(user_id, workflow_id, end_node["id"], session.step_data)
        self.session_service.mark_step_completed(user_id, end_node["id"])
        snapshot = self.session_service.get_active_session(user_id)
        self.session_service.end_session(user_id, "completed")
        return WorkflowExecutionResult(
            success=True, next_step=None, workflow_completed=True,
            amis_schema=self._create_completion_schema(snapshot.step_data, end_node),
        )

    def _should_auto_run_api_call(
        self,
        node: Dict[str, Any],
        session_data: Dict[str, Any]
    ) -> bool:
        """读接口可在参数齐全时自动执行；写接口只有显式 ui_mode=auto 才自动执行。"""
        node_config = node.get("config", {}) if isinstance(node, dict) else {}
        ui_mode = str(node_config.get("ui_mode") or "").lower()
        method = str(node_config.get("method") or "GET").upper()
        if method not in {"GET", "HEAD"} and ui_mode != "auto":
            return False
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

    def _merge_api_result_into_session(self, session, node_id, api_result):
        """业务失败不合并输出；成功时同时保存节点命名空间与兼容的扁平字段。"""
        from app.services.workflow_context import response_error, unwrap_response
        if not api_result.get("success"):
            return False
        response = api_result.get("data")
        error = response_error(response)
        if error:
            api_result["error"] = error
            return False
        payload = deepcopy(unwrap_response(response))
        if isinstance(payload, dict) and "payment" in str(node_id).lower() and "payment_success" not in payload:
            code = response.get("code") if isinstance(response, dict) else None
            if code is not None:
                payload["payment_success"] = code == 0 or 200 <= int(code) < 300
        session.step_data[f"{node_id}_result"] = payload
        session.step_data["last_api_result"] = payload
        if isinstance(payload, dict):
            for key, value in payload.items():
                if key not in {"status", "msg", "message", "api_url", "api_method"} and not key.startswith("__"):
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

        from app.services.workflow_context import resolve_templates
        resolved = resolve_templates(str(raw_message), session_data)
        return json.dumps(resolved, ensure_ascii=False, default=str) if isinstance(resolved, (dict, list)) else str(resolved)

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
        # 同一节点在一个实例内去重；重新开始会获得新实例 ID，允许再次发送通知。
        workflow_session_id = context.get("instance_id") or context.get("session_id") or f"{user_id}:{workflow_id}"
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
        
        # 业务 API 由服务端节点定义决定。
        api_endpoint = node_config.get("api_endpoint")
        method = node_config.get("method") or "GET"
        
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
    
    async def _create_or_update_session(self, user_id, workflow_id, node_id):
        """仅允许从入口创建会话，不允许直接提交到任意中间节点。"""
        result = self.workflow_service.get_workflow_detail(workflow_id)
        if not result.get("success"):
            return None, node_id
        from app.services.workflow_graph import normalize_nodes
        from app.services.workflow_service import normalize_status
        flow = result["data"]["workflow"]
        if normalize_status(flow.get("status")) != "ACTIVE":
            raise ValueError("工作流尚未启用")
        flow["nodes"] = normalize_nodes(flow["nodes"], executable=True)
        start = next(node for node in flow["nodes"] if node.get("type") == "start")
        previous = self.session_service._load_session(user_id)
        if previous is not None and previous.workflow_id == workflow_id and previous.status != "active" and node_id != start["id"]:
            raise ValueError("工作流已结束，请重新开始")
        initial_nodes = {start["id"]} | {edge["node_id"] for edge in start["child_nodes"]}
        if node_id not in initial_nodes:
            raise ValueError("请从工作流入口开始，不能跳过前置步骤")
        session = self.session_service.create_session(user_id, workflow_id, flow)
        self.session_service.update_session_step(user_id, workflow_id, node_id)
        return self.session_service.get_active_session(user_id), node_id

    def _validate_node_id(self, session, node_id):
        """只接受当前节点，拒绝旧页面和跳步提交。"""
        if node_id != session.current_step:
            raise ValueError("表单步骤已过期，请使用当前步骤")
        if not self._get_node_by_id(session.workflow_data, node_id):
            raise ValueError("工作流节点不存在")
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
