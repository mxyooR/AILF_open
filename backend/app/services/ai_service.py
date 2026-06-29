"""
AI 服务层 - 新架构：AI 只做意图识别，AMIS Schema 由规则生成

核心架构：
- AI 模型：只做意图识别（第一轮对话）
- 规则生成器：负责所有 AMIS Schema 生成
- BGE 召回：扩大候选资源范围
- 工作流数据从数据库获取
- API 权限从数据库获取

数据流：
    用户输入 → BGE 召回 → AI 意图识别 → 规则生成器 → AMIS Schema
    
优势：
- 稳定性：AMIS Schema 100% 正确（规则生成）
- 性能：只需要一轮 AI 推理（意图识别）
- 可维护性：逻辑清晰，容易调试和扩展
"""
from typing import Dict, Any, Optional, List
from app.core.logging_config import get_logger
from app.services.amis_schema_generator import amis_schema_generator
from app.services.ai_amis_service import ai_amis_service
from app.services.workflow_session_service import workflow_session_service
from app.services.workflow_service import workflow_service
from app.services.workflow_execution_service import workflow_execution_service
from app.core.ai.pure_llm_model_service import pure_llm_model_service
from app.services.help_schema_service import build_help_schema
from app.services.slot_filling_service import slot_filling_service

logger = get_logger(__name__)


class AIServiceSimple:
    """
    AI 服务 - 新架构：AI 只做意图识别
    
    职责：
    1. 调用 BGE 召回候选资源
    2. 调用 AI 模型进行意图识别
    3. 根据意图类型，用规则生成器生成 AMIS Schema
    4. 管理工作流会话和步骤推进
    """
    
    def __init__(self):
        self.schema_generator = amis_schema_generator  # 规则生成器
        self.llm_service = pure_llm_model_service  # AI 模型服务
        self.workflow_executor = workflow_execution_service  # 工作流执行服务
        self.ai_amis_service = ai_amis_service  # AMIS Schema 生成服务（包含登录界面等）
    
    def _detect_domain(self, apis: List[Dict[str, Any]], workflows: List[Dict[str, Any]]) -> str:
        if apis:
            for api in apis:
                domain = api.get('domain', api.get('business_scenario', ''))
                if domain and domain != 'common':
                    return domain

        if workflows:
            for wf in workflows:
                domain = wf.get('business_scenario', wf.get('domain', ''))
                if domain and domain != 'common':
                    return domain

        return "general"

    def _is_workflow_continue_command(self, command: str, context: Dict[str, Any]) -> bool:
        """
        检测是否是工作流推进命令
        
        优先使用 WorkflowExecutionService.is_workflow_request 进行基于上下文的检测，
        关键词匹配仅作为有活跃会话时的备用方案。
        """
        if not context:
            return False
        
        # 优先：使用 WorkflowExecutionService 的上下文检测
        if self.workflow_executor.is_workflow_request(context):
            return True
        
        # 备用：有活跃会话时检查关键词（保持向后兼容）
        user_id = context.get("user_id")
        if user_id:
            session = workflow_session_service.get_active_session(user_id)
            if session:
                continue_keywords = ["继续下一步", "下一步", "继续工作流", "推进工作流"]
                if any(keyword in command for keyword in continue_keywords):
                    return True
        
        return False

    async def process_command(
        self,
        command: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理用户命令 - 两轮对话架构

        流程：
        1. BGE 召回候选资源
        2. AI 意图识别（第一轮对话）- 选择 API/Workflow
        3. AI 槽填充（第二轮对话）- 填充文案槽位
        4. 规则生成器合并生成最终 AMIS Schema

        Args:
            command: 用户命令
            context: 上下文信息（包含 user_id, accessible_apis 等）

        Returns:
            包含 AMIS schema 的结果
        """
        try:
            # 记录用户输入
            user_id = context.get("user_id") if context else None
            inference_trace_id = (context or {}).get("_inference_trace_id")
            logger.info(f"👤 用户输入: {command}")
            
            # 1. 检查用户是否登录
            if not user_id:
                return await self._handle_unauthenticated_user(command)

            # 2. 检查是否是工作流推进命令
            if self._is_workflow_continue_command(command, context):
                logger.info(f"检测到工作流推进命令")
                return await self._handle_workflow_continue(user_id, command, context)

            # 3. 获取候选资源
            accessible_apis = context.get("accessible_apis", [])
            workflows = workflow_service.get_active_workflows_for_ai()
            domain = self._detect_domain(accessible_apis, workflows)
            logger.info(f"获取到 {len(accessible_apis)} 个可访问 API，{len(workflows)} 个活跃工作流")
            
            # 4. AI 意图识别（第一轮对话）
            logger.info("🤖 第一轮：AI 意图识别...")
            intent_result = await self._identify_intent_async(
                command=command,
                accessible_apis=accessible_apis,
                workflows=workflows,
                domain=domain,
                inference_trace_id=inference_trace_id
            )
            
            logger.info(f"✅ 意图识别结果: {intent_result['type']} - {intent_result.get('target')}")
            
            # 5. 根据意图类型处理
            if intent_result["type"] == "HELP":
                return await self._handle_help_intent(command, context, intent_result)
            if intent_result["type"] == "WORKFLOW":
                return await self._handle_workflow_intent_two_round(
                    user_id,
                    intent_result,
                    context,
                    command,
                    inference_trace_id=inference_trace_id
                )
            elif intent_result["type"] == "API":
                return await self._handle_api_intent_two_round(
                    intent_result,
                    command,
                    inference_trace_id=inference_trace_id
                )
            else:  # REJECT
                return await self._handle_reject_intent(
                    command,
                    intent_result,
                    inference_trace_id=inference_trace_id
                )
            
        except Exception as e:
            logger.error(f"❌ 命令处理失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return self._create_error_response(f"命令处理失败：{str(e)}")
    
    async def _identify_intent_async(
        self,
        command: str,
        accessible_apis: List[Dict],
        workflows: List[Dict],
        domain: str,
        inference_trace_id: Optional[str] = None
    ) -> Dict:
        """识别意图（异步调用 LLM）"""
        import asyncio
        loop = asyncio.get_event_loop()
        invoke_kwargs = {
            "user_instruction": command,
            "candidate_apis": accessible_apis,
            "candidate_workflows": workflows,
            "domain": domain
        }
        if inference_trace_id:
            invoke_kwargs["__metrics_trace_id"] = inference_trace_id

        return await loop.run_in_executor(
            None,
            lambda: self.llm_service.identify_intent(**invoke_kwargs)
        )

    async def _handle_workflow_intent_two_round(
        self,
        user_id: str,
        intent_result: Dict,
        context: Dict,
        user_instruction: str,
        inference_trace_id: Optional[str] = None
    ) -> Dict:
        """处理工作流意图（两轮对话架构）"""
        workflow_id = intent_result.get("id")
        if not workflow_id:
            return self._create_error_response("未找到匹配的工作流")
        
        # 获取工作流详情
        wf_result = workflow_service.get_workflow_detail(workflow_id)
        if not wf_result.get("success"):
            return self._create_error_response(f"获取工作流详情失败: {workflow_id}")
        
        workflow_data = wf_result["data"]["workflow"]
        nodes = workflow_data.get("nodes", [])
        
        # 找到第一个业务节点（跳过 start 节点）
        first_node = None
        for node in nodes:
            if node.get("type") not in ("start", "end"):
                first_node = node
                break
        
        if not first_node:
            return self._create_error_response("工作流没有有效的业务节点")
        
        logger.info(f"🤖 第二轮：AI 槽填充...")
        
        # 🔥 调用 AI 进行第二轮槽填充
        slot_values = await self._generate_slot_values_for_workflow(
            workflow=workflow_data,
            first_node=first_node,
            user_instruction=user_instruction,
            accessible_apis=context.get("accessible_apis", []),
            inference_trace_id=inference_trace_id
        )
        
        logger.info(f"✅ AI 槽填充完成: {list(slot_values.keys()) if slot_values else '无'}")
        
        # 用规则生成器生成 Schema（传入 AI 槽位值）
        schema = self.schema_generator.generate_workflow_entry_form(
            workflow=workflow_data,
            first_node=first_node,
            context_data={},
            user_instruction=user_instruction,
            slot_values=slot_values  # 🔥 传递 AI 槽位值
        )
        
        # 创建工作流会话
        await self._check_and_create_workflow_session(
            user_id=user_id,
            workflow_id=workflow_id,
            workflow_data=workflow_data,
            first_node_id=first_node.get("id")
        )
        
        return {
            "success": True,
            "amis_schema": schema,
            "intent": intent_result
        }
    
    async def _handle_api_intent_two_round(
        self,
        intent_result: Dict,
        user_instruction: str,
        inference_trace_id: Optional[str] = None
    ) -> Dict:
        """处理 API 意图（两轮对话架构）"""
        api = intent_result.get("matched_resource")
        if not api:
            return self._create_error_response("未找到匹配的 API")
        
        logger.info(f"🤖 第二轮：AI 槽填充 + 规则生成器合并")

        # 第二轮：为 direct API form 生成槽位值（标题/提示语/字段中文标签等）
        try:
            template_str = self.schema_generator.template_loader.get_template_content("api_form.json.j2")
        except Exception:
            # Template read failure should not block schema generation.
            template_str = ""

        request_fields = api.get("request", api.get("parameters", [])) or []

        # Normalize request_fields into a list-of-dicts so SlotFilling can derive field_label_{name} slots.
        normalized_form_fields: List[Dict[str, Any]] = []
        if isinstance(request_fields, dict):
            normalized_form_fields = [{"name": k, "type": "string"} for k in request_fields.keys()]
        elif isinstance(request_fields, list):
            for item in request_fields:
                if isinstance(item, dict) and item.get("name"):
                    normalized_form_fields.append(item)
                elif isinstance(item, str) and item:
                    normalized_form_fields.append({"name": item, "type": "string"})

        # Build response field list for user-facing labels.
        response_fields: List[str] = []
        try:
            response_fields = self._extract_response_fields(api)
        except Exception:
            response_fields = []

        # Prefer entity metadata for labels; only ask AI to label missing fields.
        missing_response_fields: List[str] = response_fields
        existing_map: Dict[str, str] = {}
        handler_cfg: Any = {}
        try:
            import json
            handler_cfg = api.get("handler_config") or api.get("handlerConfig") or {}
            if not handler_cfg and isinstance(api.get("handler"), dict):
                handler_cfg = api.get("handler", {}).get("config") or {}
            if isinstance(handler_cfg, str):
                try:
                    handler_cfg = json.loads(handler_cfg)
                except Exception:
                    handler_cfg = {}
            entity_name = None
            if isinstance(handler_cfg, dict):
                entity_name = (
                    handler_cfg.get("entity")
                    or handler_cfg.get("entity_name")
                    or handler_cfg.get("entityName")
                )
            if not entity_name:
                entity_name = api.get("entity") or api.get("entity_name")
            if entity_name:
                from app.services.entity_service import entity_service
                existing_map = entity_service.get_field_label_map(entity_name=entity_name) or {}
                if existing_map:
                    def _has_cn(value: Any) -> bool:
                        if not isinstance(value, str) or not value:
                            return False
                        return any("\u4e00" <= ch <= "\u9fff" for ch in value)

                    missing_response_fields = [
                        f for f in response_fields
                        if (f not in existing_map) or (not _has_cn(existing_map.get(f)))
                    ]
        except Exception:
            pass

        # 补充：从处理器配置中抽取列表字段，确保列表列名也能生成中文
        allowed_fields = None
        if isinstance(handler_cfg, dict):
            allowed_fields = (
                handler_cfg.get("allowed_fields")
                or handler_cfg.get("fields")
                or handler_cfg.get("select_fields")
            )
        if isinstance(allowed_fields, list):
            # 如果字段已有中文标签则不重复生成
            def _has_cn(value: Any) -> bool:
                if not isinstance(value, str) or not value:
                    return False
                return any("\u4e00" <= ch <= "\u9fff" for ch in value)

            for field_name in allowed_fields:
                if not isinstance(field_name, str) or not field_name:
                    continue
                label = existing_map.get(field_name) if existing_map else None
                if label and _has_cn(label):
                    continue
                if field_name not in missing_response_fields:
                    missing_response_fields.append(field_name)

        # Limit to keep slot filling fast.
        missing_response_fields = missing_response_fields[:20]

        slot_context = {
            "prompt_type": "api_only",
            "api": api,
            # Use request fields to derive field_label_{name} slots.
            "form_fields": normalized_form_fields,
            "extra_slots": (
                ["page_title", "user_message", "submit_button_text"]
                + [f"resp_label_{name}" for name in missing_response_fields]
            ),
            "response_fields": response_fields,
        }

        slot_values = await slot_filling_service.fill_slots(
            template=template_str,
            context=slot_context,
            user_instruction=user_instruction,
            inference_trace_id=inference_trace_id,
        )

        schema = self.schema_generator.generate_direct_api_form(api, slot_values=slot_values)
        
        return {
            "success": True,
            "amis_schema": schema,
            "intent": intent_result
        }

    async def _handle_help_intent(
        self,
        command: str,
        context: Dict[str, Any],
        intent_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理帮助类意图，返回固定模板的场景功能说明"""
        schema = build_help_schema(command, context)
        return {
            "success": True,
            "amis_schema": schema,
            "intent": intent_result,
            "response_text": "已为你展示当前用户的权限范围"
        }
    
    async def _handle_workflow_intent(
        self,
        user_id: str,
        intent_result: Dict,
        context: Dict
    ) -> Dict:
        """处理工作流意图（旧方法，保留兼容）"""
        return await self._handle_workflow_intent_two_round(user_id, intent_result, context, "", inference_trace_id=None)
    
    async def _handle_api_intent(self, intent_result: Dict) -> Dict:
        """处理 API 意图（旧方法，保留兼容）"""
        return await self._handle_api_intent_two_round(intent_result, "", inference_trace_id=None)

    def _extract_response_fields(self, api: Dict[str, Any]) -> List[str]:
        """Extract response field names from API response schema for label generation."""
        if not isinstance(api, dict):
            return []

        schema = api.get("schema")
        if not schema:
            responses = api.get("responses_config") or api.get("responses") or {}
            response_200 = responses.get("200") or responses.get(200) or {}
            if isinstance(response_200, dict):
                schema = response_200.get("schema") or response_200.get("response_schema")

        def _collect(s: Any) -> List[str]:
            if not isinstance(s, dict):
                return []
            s_type = s.get("type")
            props = s.get("properties")
            if s_type == "object" and isinstance(props, dict):
                # Dive into data when present
                if "data" in props:
                    return _collect(props.get("data"))
                fields: List[str] = []
                for key, val in props.items():
                    if key == "items" and isinstance(val, dict):
                        fields.extend(_collect(val))
                    else:
                        fields.append(key)
                return fields
            if s_type == "array":
                return _collect(s.get("items"))
            return []

        fields = _collect(schema)
        # De-dup while preserving order
        seen = set()
        ordered: List[str] = []
        for f in fields:
            if f and f not in seen:
                seen.add(f)
                ordered.append(f)
        return ordered
    
    async def _handle_reject_intent(
        self,
        command: str,
        intent_result: Dict,
        inference_trace_id: Optional[str] = None
    ) -> Dict:
        """
        处理拒绝意图（两轮对话架构）
        
        第二轮：AI 生成拒绝提示的槽位值
        """
        import json
        logger.info(f"🤖 第二轮：AI 生成拒绝提示槽位")
        
        available_actions = intent_result.get("available_actions", [])
        
        # 构建第二轮 Prompt（匹配数据集格式）
        system_prompt_round2 = f"""用户指令无法匹配到任何资源。

可用操作：
{json.dumps(available_actions[:6], ensure_ascii=False)}

任务：为拒绝提示生成槽位值（JSON 格式）：
- reject_title：拒绝标题（4-6 字）
- reject_message：拒绝提示信息（20-40 字，包含可用操作建议）"""
        
        # 调用 AI 生成槽位
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            # 使用槽填充服务
            slot_values = await loop.run_in_executor(
                None,
                lambda: self._generate_reject_slots_sync(
                    system_prompt_round2,
                    available_actions,
                    inference_trace_id=inference_trace_id
                )
            )
            
            reject_title = slot_values.get("reject_title", "无法处理")
            reject_message = slot_values.get("reject_message", f"抱歉，我无法理解您的指令：{command}")
            
        except Exception as e:
            logger.error(f"❌ AI 生成拒绝槽位失败: {str(e)}")
            # 降级到默认值
            reject_title = "无法处理"
            reject_message = f"抱歉，我无法理解您的指令：{command}"
            if available_actions:
                reject_message += f"\n\n您可以尝试以下操作：\n" + "\n".join([f"- {action}" for action in available_actions[:5]])
        
        # 用规则生成器生成拒绝 Schema
        schema = {
            "type": "page",
            "title": reject_title,
            "body": {
                "type": "alert",
                "level": "warning",
                "body": reject_message,
                "showIcon": True
            }
        }
        
        return {
            "success": True,
            "amis_schema": schema,
            "intent": intent_result
        }
    
    def _generate_reject_slots_sync(
        self,
        system_prompt: str,
        available_actions: List[str],
        inference_trace_id: Optional[str] = None
    ) -> Dict[str, str]:
        """同步生成拒绝槽位"""
        if not self.llm_service.is_loaded:
            logger.warning("⚠️ LLM 模型未加载，使用默认拒绝槽位")
            return {
                "reject_title": "无法处理",
                "reject_message": f"抱歉，我无法理解您的指令。您可以尝试：{', '.join(available_actions[:3])}"
            }
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": ""}  # 等待生成
        ]
        
        try:
            invoke_kwargs = {
                "max_new_tokens": 200,
                "temperature": 0.2,
                "top_p": 0.8,
                "do_sample": False
            }
            if inference_trace_id:
                invoke_kwargs["__metrics_trace_id"] = inference_trace_id
            output = self.llm_service._generate_single_turn(
                messages[:-1],  # 不包含空的 assistant
                **invoke_kwargs
            )
            
            # 解析 JSON
            import json
            if hasattr(self.llm_service, "_try_parse_json"):
                parsed = self.llm_service._try_parse_json(output)
                if isinstance(parsed, dict):
                    return parsed
            json_start = output.find('{')
            json_end = output.rfind('}') + 1
            if json_start != -1 and json_end > 0:
                json_str = output[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"解析拒绝槽位失败: {str(e)}")
        
        # 降级
        return {
            "reject_title": "无法处理",
            "reject_message": f"抱歉，我无法理解您的指令。您可以尝试：{', '.join(available_actions[:3])}"
        }
    
    async def _check_and_create_workflow_session(
        self,
        user_id: str,
        workflow_id: str,
        workflow_data: Dict,
        first_node_id: str
    ):
        """创建工作流会话。

        规则：当用户通过自然语言再次命中某个工作流时，视为“重新开始该流程”。
        因此若存在活跃会话，先结束旧会话再创建新会话，避免历史 step_data 污染。
        """
        try:
            # 新命中工作流时强制重建会话，避免复用旧会话导致跳步/脏数据
            existing_session = workflow_session_service.get_active_session(user_id)
            if existing_session:
                logger.info(
                    f"♻️ 检测到用户{user_id}已有活跃会话({existing_session.workflow_id})，"
                    f"将重建为新会话({workflow_id})"
                )
                workflow_session_service.end_session(user_id, "cancelled")
            
            # 创建工作流会话
            logger.info(f"为用户{user_id}创建工作流会话: {workflow_data.get('name')}")
            session = workflow_session_service.create_session(
                user_id=user_id,
                workflow_id=workflow_id,
                workflow_data=workflow_data
            )
            
            # 设置当前步骤为第一个节点
            if first_node_id:
                workflow_session_service.update_session_step(
                    user_id=user_id,
                    workflow_id=workflow_id,
                    new_step=first_node_id,
                    step_data={}
                )
            
            logger.info(f"✅ 工作流会话创建成功: {session.workflow_id}, current_step={session.current_step}")
                
        except Exception as e:
            logger.warning(f"⚠️ 创建工作流会话失败: {str(e)}")
            import traceback
            logger.warning(traceback.format_exc())

    async def _generate_slot_values_for_workflow(
        self,
        workflow: Dict,
        first_node: Dict,
        user_instruction: str,
        accessible_apis: List[Dict],
        inference_trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        调用 AI 生成工作流的槽位值（第二轮对话）
        
        参考 inference_v10.py 的实现
        """
        try:
            # 1. 构建工作流详情 JSON
            workflow_detail = self._build_workflow_detail_for_slot_filling(workflow, first_node, accessible_apis)
            
            # 2. 构建槽位列表
            slots = self._build_slots_for_workflow(first_node, accessible_apis)
            
            # 3. 构建第二轮 system prompt
            system_prompt = self._build_slot_prompt("工作流详情", workflow_detail, slots)
            logger.info(f"[SlotFilling] Slots: {slots}")
            logger.info(f"[SlotFilling] Prompt:\n{system_prompt}")
            
            # 4. 调用 AI 生成槽位 JSON
            invoke_kwargs: Dict[str, Any] = {}
            if inference_trace_id:
                invoke_kwargs["__metrics_trace_id"] = inference_trace_id
            slot_output = await self.llm_service.generate_slot_values(system_prompt, **invoke_kwargs)
            logger.info(f"[SlotFilling] Raw output:\n{slot_output}")
            
            # 5. 解析 JSON
            import json
            try:
                if hasattr(self.llm_service, "_try_parse_json"):
                    parsed = self.llm_service._try_parse_json(slot_output)
                    if isinstance(parsed, dict):
                        slot_values = parsed
                        logger.info("✅ 槽位 JSON 解析成功")
                    else:
                        slot_values = json.loads(slot_output)
                        logger.info(f"✅ 槽位 JSON 解析成功")
                else:
                    slot_values = json.loads(slot_output)
                    logger.info(f"✅ 槽位 JSON 解析成功")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ 槽位 JSON 解析失败: {str(e)}，尝试容错解析")
                logger.warning(f"原始输出: {slot_output}")
                slot_values = {}

                json_start = slot_output.find("{")
                json_end = slot_output.rfind("}")
                if json_start != -1 and json_end != -1 and json_end > json_start:
                    try:
                        slot_values = json.loads(slot_output[json_start:json_end + 1])
                        logger.info("✅ 槽位 JSON 截取解析成功")
                    except Exception:
                        slot_values = {}

                if not slot_values:
                    slot_values = self._parse_slot_kv_lines(slot_output)
                    if slot_values:
                        logger.info("✅ 槽位 KV 解析成功")

                if not slot_values:
                    logger.error("❌ 槽位解析失败，返回空结果")
                    return {}
            
            # 🔥 后处理：规范化 API URL（将 {param} 转换为 ${param}）
            if 'api_url' in slot_values:
                original_url = slot_values['api_url']
                normalized_url = self._normalize_api_url(original_url)
                if original_url != normalized_url:
                    slot_values['api_url'] = normalized_url
                    logger.info(f"🔧 URL 规范化: {original_url} -> {normalized_url}")
            
            return slot_values
                
        except Exception as e:
            logger.error(f"❌ 生成槽位值失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    
    def _build_workflow_detail_for_slot_filling(
        self,
        workflow: Dict,
        first_node: Dict,
        accessible_apis: List[Dict]
    ) -> str:
        """构建工作流详情 JSON（用于槽填充）"""
        import json
        
        # 获取第一个节点的 API 详情（如果是 api_call 节点）
        first_node_api = None
        if first_node.get("type") == "api_call":
            config = first_node.get("config", {})
            api_endpoint = config.get("api_endpoint", "")
            
            # 从 accessible_apis 中查找匹配的 API
            for api in accessible_apis:
                if api.get("path") == api_endpoint or api.get("endpoint") == api_endpoint:
                    first_node_api = api
                    break
        
        detail = {
            "id": workflow.get("id"),
            "name": workflow.get("name"),
            "desc": workflow.get("desc", ""),
            "first_node": {
                "id": first_node.get("id"),
                "name": first_node.get("name"),
                "type": first_node.get("type")
            }
        }
        
        # 如果有 API，添加 API 详情
        if first_node_api:
            detail["first_node"]["api"] = {
                "path": first_node_api.get("path", first_node_api.get("endpoint", "")),
                "method": first_node_api.get("method", "POST"),
                "request": first_node_api.get("request", first_node_api.get("parameters", []))[:5]
            }
        
        return json.dumps(detail, ensure_ascii=False, indent=2)
    
    def _build_slots_for_workflow(self, first_node: Dict, accessible_apis: List[Dict]) -> List[str]:
        """构建工作流的槽位列表"""
        slots = ["page_title", "user_message", "submit_button_text", "reset_button_text"]
        
        # 如果第一个节点是 api_call，添加 API 相关槽位
        if first_node.get("type") == "api_call":
            config = first_node.get("config", {})
            api_endpoint = config.get("api_endpoint", "")
            node_params = config.get("parameters", {}) or {}
            
            # 查找对应的 API
            for api in accessible_apis:
                if api.get("path") == api_endpoint or api.get("endpoint") == api_endpoint:
                    slots.extend(["api_url", "api_method"])
                    
                    # 添加字段标签槽位
                    request_fields = api.get("request", api.get("parameters", []))[:5]
                    for field in request_fields:
                        field_name = field.get("name")
                        if field_name:
                            slots.append(f"field_label_{field_name}")
                    break
            # 补充：使用工作流节点参数（可能包含额外字段）
            if isinstance(node_params, dict):
                for field_name in node_params.keys():
                    if field_name:
                        slots.append(f"field_label_{field_name}")
        
        # 去重且保持顺序
        seen = set()
        deduped = []
        for slot in slots:
            if slot not in seen:
                seen.add(slot)
                deduped.append(slot)
        return deduped
    
    def _build_slot_prompt(self, detail_label: str, detail_json: str, slots: List[str]) -> str:
        """构建槽填充的 system prompt"""
        import json
        
        requirements = [
            "- page_title：3-6 字",
            "- user_message：10-20 字",
            "- field_label_xxx：2-4 字"
        ]
        
        if "api_url" in slots:
            requirements.append("- api_url：完整的 API 路径（如果有路径参数，使用 ${param} 格式）")
        if "api_method" in slots:
            requirements.append("- api_method：HTTP 方法（GET/POST/PUT/DELETE）")
        
        requirements.append("- 只输出 JSON，不要其他内容")
        
        slots_text = json.dumps(slots, ensure_ascii=False)
        requirements_text = "\n".join(requirements)
        
        return f"""{detail_label}：
{detail_json}

任务：为以下槽位生成中文文案（JSON 格式）：
{slots_text}

要求：
{requirements_text}"""

    def _parse_slot_kv_lines(self, slot_output: str) -> Dict[str, Any]:
        """解析 'KEY: VALUE' 形式的槽位输出"""
        if not slot_output:
            return {}

        import re
        slot_values: Dict[str, Any] = {}
        direct_map = {
            "PAGE TITLE": "page_title",
            "USER MESSAGE": "user_message",
            "SUBMIT BUTTON TEXT": "submit_button_text",
            "RESET BUTTON TEXT": "reset_button_text",
            "API URL": "api_url",
            "API METHOD": "api_method",
        }

        for raw_line in slot_output.splitlines():
            if ":" not in raw_line:
                continue
            key, value = raw_line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if not key or not value:
                continue

            key_upper = key.upper()
            if key_upper in direct_map:
                slot_values[direct_map[key_upper]] = value
                continue

            if key_upper.startswith("FIELD LABEL "):
                field_key = key[len("FIELD LABEL "):].strip()
                field_key = re.sub(r"[^\w]+", "_", field_key.lower())
                field_key = re.sub(r"_+", "_", field_key).strip("_")
                if field_key:
                    slot_values[f"field_label_{field_key}"] = value

        return slot_values
    
    def _normalize_api_url(self, api_url: str) -> str:
        """
        将 {param} 转换为 ${param}（AMIS 变量语法）
        
        例如：
        - /api/v1/tickets/{ticket_id} -> /api/v1/tickets/${ticket_id}
        - /api/v1/orders/{order_id}/items -> /api/v1/orders/${order_id}/items
        
        Args:
            api_url: 原始 API URL
        
        Returns:
            规范化后的 URL
        """
        import re
        # 匹配 {xxx} 但不匹配 ${xxx}（使用负向后查找）
        return re.sub(r'(?<!\$)\{(\w+)\}', r'${\1}', api_url)


    async def _handle_workflow_continue(self, user_id: str, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理工作流推进命令 - 委托给 WorkflowExecutionService
        
        这个方法现在只负责：
        1. 提取参数
        2. 委托给 WorkflowExecutionService.execute_step
        3. 转换响应格式
        
        所有核心逻辑都在 WorkflowExecutionService 中，确保 DRY 原则。
        """
        try:
            logger.info(f"处理用户{user_id}的工作流推进(委托给WorkflowExecutionService)")
            
            # 1. 提取工作流参数
            workflow_id = context.get("workflow_id")
            node_id = context.get("node_id")
            form_data = context.get("data", {})
            
            # 2. 如果没有 workflow_id/node_id，尝试从活跃会话获取
            if not workflow_id or not node_id:
                session = workflow_session_service.get_active_session(user_id)
                if session:
                    workflow_id = workflow_id or session.workflow_id
                    node_id = node_id or session.current_step
                    logger.info(f"📋 从活跃会话获取: workflow_id={workflow_id}, node_id={node_id}")
                else:
                    # 没有活跃会话，按正常命令处理
                    logger.info("用户没有活跃的工作流会话，转为正常命令处理")
                    accessible_apis = context.get("accessible_apis", [])
                    workflows = workflow_service.get_active_workflows_for_ai()
                    return await self.amis_service.generate_schema(
                        command=command,
                        accessible_apis=accessible_apis,
                        workflows=workflows
                    )
            
            # 3. 委托给 WorkflowExecutionService 执行
            result = await self.workflow_executor.execute_step(
                user_id=user_id,
                workflow_id=workflow_id,
                node_id=node_id,
                form_data=form_data,
                context=context
            )
            
            # 4. 转换为 AI 服务响应格式
            return result.to_ai_response()
            
        except Exception as e:
            logger.error(f"❌ 处理工作流推进失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return self.amis_service.create_error_response(
                f"工作流推进失败: {str(e)}",
                "工作流错误"
            )
    
    async def _generate_step_schema(self, session, step_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据工作流步骤生成对应的界面（使用数据集格式）
        
        数据集格式：
        - Workflow_Input: 收集用户输入
        - Workflow_Execute: 执行 API 调用
        """
        try:
            # 获取步骤节点信息
            workflow_data = session.workflow_data
            workflow_id = session.workflow_id
            workflow_name = workflow_data.get("name", "工作流")
            step_data = session.step_data
            nodes = workflow_data.get("nodes", [])
            
            # 查找目标节点
            target_node = None
            for node in nodes:
                if node.get("id") == step_id:
                    target_node = node
                    break
            
            if not target_node:
                # 节点未预定义，创建虚拟节点让 AI 动态生成（符合数据集格式）
                logger.info(f"节点{step_id}未预定义，使用AI动态生成")
                target_node = {
                    "id": step_id,
                    "name": step_id,
                    "type": "dynamic"
                }
            
            logger.debug(f"生成步骤界面:")
            logger.debug(f"   节点ID: {target_node.get('id')}")
            logger.debug(f"   节点名称: {target_node.get('name', '未知')}")
            logger.debug(f"   节点类型: {target_node.get('type', 'unknown')}")
            
            # 构建完整的上下文，包含会话数据
            enhanced_context = {
                **context,
                "session": session.to_dict(),
                "current_node": target_node,
                "workflow_data": workflow_data,
                "step_data": session.step_data
            }
            
            # 让AI模型根据节点定义生成界面
            return await self._ai_generate_node_interface(target_node, enhanced_context)
                
        except Exception as e:
            logger.error(f"❌ 生成步骤界面失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return self.amis_service.create_error_response(
                f"生成界面失败: {str(e)}",
                "界面生成错误"
            )
    
    async def _ai_generate_node_interface(self, node: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI模型根据工作流节点定义生成界面"""
        try:
            logger.info(f"🤖 让AI模型生成节点界面: {node.get('name')}")
            
            # 获取会话信息
            session_info = context.get("session", {})
            workflow_id = session_info.get("workflow_id", "")
            
            # 构建AI提示，使用数据集格式
            ai_prompt = self._build_node_interface_prompt(node, context)
            
            logger.debug(f"AI提示内容:")
            logger.debug(f"   长度: {len(ai_prompt)}字符")
            logger.debug(f"   内容: {ai_prompt}")
            
            # 调用AI模型生成界面，传递当前工作流节点
            accessible_apis = context.get("accessible_apis", [])
            workflows = workflow_service.get_active_workflows_for_ai()
            result = await self.amis_service.generate_schema(
                command=ai_prompt,
                context="workflow",  # 标识这是工作流上下文
                accessible_apis=accessible_apis,
                workflows=workflows,
                current_workflow_node=node,
                current_workflow_id=workflow_id
            )
            
            if result.get("success"):
                logger.info("✅ AI成功生成节点界面")
                # 在响应中添加工作流信息
                result["workflow_node"] = {
                    "id": node.get("id"),
                    "name": node.get("name"),
                    "type": node.get("type")
                }
            else:
                logger.error(f"❌ AI生成节点界面失败: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ AI生成节点界面异常: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return self.amis_service.create_error_response(
                f"AI生成界面失败: {str(e)}",
                "AI生成错误"
            )
    
    def _build_node_interface_prompt(self, node: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        构建AI生成界面的提示 - 使用数据集 V10 格式
        
        🔥 数据集 V10 格式（已移除 Workflow_Input，统一使用 Workflow_Execute）：
        - Workflow_Execute: "指令：xxx\n当前状态：Workflow_Execute\n当前节点ID：{full_node_id}\n工作流ID：{workflow_id}\n上下文数据：{...}"
        """
        try:
            # 获取节点信息
            node_id = node.get("id", "unknown")
            node_name = node.get("name", "步骤")
            node_type = node.get("type", "unknown")
            
            # 获取会话信息
            session_info = context.get("session", {})
            workflow_id = session_info.get("workflow_id", "unknown")
            workflow_name = session_info.get("workflow_data", {}).get("name", "工作流")
            step_data = session_info.get("step_data", {})
            
            # 🔥 统一使用 Workflow_Execute 状态（与数据集 V10 一致）
            state = "Workflow_Execute"
            
            # 获取节点的 ai_instructions 作为指令
            ai_instructions = node.get("ai_instructions", {})
            instruction = ai_instructions.get("user_message", f"{workflow_name} - {node_name}")
            
            # 使用数据集格式构建输入
            return self._build_dataset_format_input(
                command=instruction,
                state=state,
                context=context,
                workflow_id=workflow_id,
                node_id=node_id,
                step_data=step_data
            )
            
        except Exception as e:
            logger.error(f"❌ 构建节点界面提示失败: {str(e)}")
            return f"指令：生成 {node.get('name', '步骤')} 界面\n当前状态：Workflow_Execute"
    
    def _find_form_in_schema(self, schema: Any) -> Optional[Dict[str, Any]]:
        """在 schema 中查找表单组件"""
        if not isinstance(schema, dict):
            return None
        
        # 直接是表单
        if schema.get("type") == "form":
            return schema
        
        # 在 body 中查找
        if "body" in schema:
            body = schema["body"]
            if isinstance(body, dict):
                result = self._find_form_in_schema(body)
                if result:
                    return result
            elif isinstance(body, list):
                for item in body:
                    result = self._find_form_in_schema(item)
                    if result:
                        return result
        
        # 在其他字段中查找
        for key, value in schema.items():
            if isinstance(value, (dict, list)):
                result = self._find_form_in_schema(value)
                if result:
                    return result
        
        return None
    
    async def _find_matching_workflows(self, command: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查找匹配的工作流"""
        try:
            # 这里应该查询数据库中的工作流定义
            from app.services.workflow_service import workflow_service
            
            workflows_result = workflow_service.get_workflows_list(
                page=1, limit=100, status="ACTIVE"
            )
            
            if not workflows_result.get("success"):
                return []
            
            workflows = workflows_result.get("data", {}).get("workflows", [])
            matching_workflows = []
            
            command_lower = command.lower()
            for workflow_data in workflows:
                # 检查触发关键词
                trigger_keywords = workflow_data.get("trigger_keywords", [])
                user_intents = workflow_data.get("user_intents", [])
                
                # 简单匹配逻辑
                if any(keyword in command_lower for keyword in trigger_keywords):
                    matching_workflows.append(workflow_data)
                elif any(intent in command_lower for intent in user_intents):
                    matching_workflows.append(workflow_data)
            
            logger.info(f"找到{len(matching_workflows)}个匹配的工作流")
            return matching_workflows
            
        except Exception as e:
            logger.error(f"❌ 查找匹配工作流失败: {str(e)}")
            return []

    
    def _build_dataset_format_input(
        self, 
        command: str, 
        state: str = "Global_Routing",
        context: Dict[str, Any] = None,
        workflow_id: str = None,
        node_id: str = None,
        step_data: Dict[str, Any] = None
    ) -> str:
        """
        构建符合数据集格式的用户输入
        
        🔥 数据集 V10 格式：
        - Global_Routing: "指令：xxx\n当前状态：Global_Routing"
        - Workflow_Execute: "指令：xxx\n当前状态：Workflow_Execute\n当前节点ID：{workflow_id}_node_{node_id}\n工作流ID：{workflow_id}\n上下文数据：{...}"
        
        Args:
            command: 用户原始命令
            state: 状态机状态 (Global_Routing, Workflow_Execute)
            context: 上下文信息
            workflow_id: 工作流 ID
            node_id: 当前节点 ID
            step_data: 上下文数据（之前步骤收集的数据）
        
        Returns:
            格式化的用户输入字符串
        """
        import json
        
        parts = [f"指令：{command}", f"当前状态：{state}"]
        
        if state == "Workflow_Execute":
            # 🔥 使用完整的节点 ID 格式（与数据集一致）
            if workflow_id and node_id:
                full_node_id = f"{workflow_id}_node_{node_id}"
                parts.append(f"当前节点ID：{full_node_id}")
                parts.append(f"工作流ID：{workflow_id}")
            elif node_id:
                parts.append(f"当前节点ID：{node_id}")
            
            # 🔥 只有当有上下文数据时才添加
            if step_data:
                parts.append(f"上下文数据：{json.dumps(step_data, ensure_ascii=False)}")
        
        result = "\n".join(parts)
        logger.debug(f"构建数据集格式输入: {result[:200]}...")
        return result

    
    def _create_error_response(self, error_message: str) -> Dict:
        """创建错误响应"""
        return {
            "success": False,
            "error": error_message,
            "amis_schema": {
                "type": "page",
                "title": "错误",
                "body": {
                    "type": "alert",
                    "level": "danger",
                    "body": error_message,
                    "showIcon": True
                }
            }
        }
    
    async def _handle_unauthenticated_user(self, command: str) -> Dict[str, Any]:
        """处理未认证用户的请求"""
        try:
            logger.info(f"🔐 处理未认证用户请求: {command}")
            # 调用 ai_amis_service 生成登录界面
            login_response = await self.ai_amis_service.generate_login_schema(command)
            logger.info(f"✅ 已生成登录界面")
            return login_response
        except Exception as e:
            logger.error(f"❌ 生成登录界面失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return self._create_error_response(f"无法生成登录界面：{str(e)}")


# 全局实例
ai_service_simple = AIServiceSimple()

