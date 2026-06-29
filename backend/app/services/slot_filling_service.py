"""
槽填充服务 (Slot-Filling Service)

核心思想：
- 规则生成器：提供 AMIS 模板骨架（100% 正确）
- AI 模型：只填充动态内容（标题、描述、字段标签等）

优势：
- 合规性：规则保证 AMIS 语法 100% 正确
- 符合意图性：AI 提供个性化文案，提升用户体验
- 性能：AI 只生成 200 tokens（vs 1500 tokens），推理时间减少 90%+
"""
import re
import json
from typing import Dict, Any, List, Optional
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SlotFillingService:
    """槽填充服务 - AI 只填充动态内容"""
    
    def __init__(self):
        self._llm_service = None
    
    @property
    def llm_service(self):
        """延迟加载 LLM 服务"""
        if self._llm_service is None:
            from app.core.ai.pure_llm_model_service import pure_llm_model_service
            self._llm_service = pure_llm_model_service
        return self._llm_service
    
    def extract_slots(self, template: str) -> List[str]:
        """
        从模板中提取所有 AI 槽位
        
        槽位格式：{{ AI_SLOT: slot_name }}
        
        Args:
            template: 带槽位的模板字符串
        
        Returns:
            槽位名称列表，如 ["page_title", "user_message", "field_label_order_id"]
        """
        pattern = r'\{\{\s*AI_SLOT:\s*(\w+)\s*\}\}'
        slots = re.findall(pattern, template)
        logger.debug(f"从模板中提取到 {len(slots)} 个槽位: {slots}")
        return slots
    
    async def fill_slots(
        self,
        template: str,
        context: Dict[str, Any],
        user_instruction: str = "",
        inference_trace_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        让 AI 填充所有槽位
        
        Args:
            template: 带槽位的模板
            context: 上下文（节点信息、API 定义等）
            user_instruction: 用户指令
        
        Returns:
            槽位值字典，如 {"page_title": "订单查询", "user_message": "请选择要查询的订单"}
        """
        slots = self.extract_slots(template)
        slots = self._merge_slots(slots, context)
        
        if not slots:
            logger.debug("模板中没有槽位，跳过 AI 填充")
            return {}
        
        logger.info(f"🎯 开始 AI 槽填充，共 {len(slots)} 个槽位")
        
        prompt = self._build_slot_filling_prompt(
            slots=slots,
            context=context,
            user_instruction=user_instruction
        )
        
        # 调用 AI（输出很短，只有槽位值）
        try:
            import asyncio
            slot_values = await asyncio.wait_for(
                self._call_ai_for_slots(
                    prompt,
                    slots,
                    user_instruction=user_instruction,
                    inference_trace_id=inference_trace_id
                ),
                timeout=60
            )
            slot_values = self._postprocess_slot_values(slot_values, context)
            logger.info(f"✅ AI 槽填充完成: {list(slot_values.keys())}")
            return slot_values
        except asyncio.TimeoutError:
            logger.warning("⚠️ AI 槽填充超时，使用默认槽位值")
            return self._get_default_slot_values(slots)
        except Exception as e:
            logger.error(f"❌ AI 槽填充失败: {str(e)}")
            return self._get_default_slot_values(slots)
    
    def _get_domain_cn(self, domain: str) -> str:
        domain_names = {
            "medical": "医疗", "finance": "财务", "ecommerce": "电商",
            "train_ticket": "火车票", "logistics": "物流", "hrm": "人力资源",
            "education": "教育", "hotel": "酒店", "banking": "银行",
            "government": "政务", "realestate": "房产", "catering": "餐饮",
            "general": "通用", "railway_ticketing": "火车票"
        }
        return domain_names.get(domain, domain)

    def _format_node_id(self, workflow_id: str, node_id: str) -> str:
        if not workflow_id or not node_id:
            return node_id
        prefix = f"{workflow_id}_node_"
        if node_id.startswith(prefix):
            return node_id
        return f"{workflow_id}_node_{node_id}"

    def _build_api_detail_for_prompt(self, context: Dict[str, Any], prompt_type: str) -> Dict[str, Any]:
        api_detail = self._extract_api_detail(context)
        if not api_detail:
            return {}
        if prompt_type == "api_only":
            detail = {}
            for key in ("path", "method", "desc"):
                if api_detail.get(key):
                    detail[key] = api_detail[key]
            request = api_detail.get("request", [])
            if request:
                detail["request"] = [
                    {"name": p.get("name", ""), "type": p.get("type", "string")} for p in request
                ]
            response_fields = context.get("response_fields") or []
            if response_fields:
                detail["response_fields"] = response_fields
            return detail
        return api_detail

    def _build_slot_filling_prompt(
        self,
        slots: List[str],
        context: Dict[str, Any],
        user_instruction: str
    ) -> str:
        """
        构建槽填充 Prompt（匹配数据集格式）
        """
        import json

        node = context.get("node", {})
        workflow = context.get("workflow", {})
        api = context.get("api", {})
        context_data = context.get("context_data", {})
        prompt_type = context.get("prompt_type", "")

        detail_blocks = []

        if prompt_type == "workflow_step":
            domain = context.get("domain") or workflow.get("domain") or workflow.get("business_scenario") or api.get("domain") or "general"
            domain_cn = self._get_domain_cn(domain)
            if domain_cn and domain != "general":
                detail_blocks.append(f"你是{domain_cn}领域的 AMIS 界面生成助手。")

            workflow_name = workflow.get("name", "")
            workflow_id = workflow.get("id", workflow.get("workflow_id", ""))
            if workflow_name or workflow_id:
                detail_blocks.append(f"当前工作流：{workflow_name}（ID: {workflow_id}）")

            node_id = node.get("id", "")
            full_node_id = self._format_node_id(workflow_id, node_id) if node_id else node_id
            node_name = node.get("name", "")
            node_type = node.get("type", "")
            ai_instructions = node.get("ai_instructions", {}) or {}
            node_prompt = ai_instructions.get("user_message", "") if isinstance(ai_instructions, dict) else ""
            if not node_prompt:
                node_prompt = node.get("description", "")

            node_lines = []
            if full_node_id:
                node_lines.append(f"当前节点：ID: {full_node_id}")
            if node_name:
                node_lines.append(f"名称: {node_name}")
            if node_type:
                node_lines.append(f"类型: {node_type}")
            if node_prompt:
                node_lines.append(f"提示: {node_prompt}")
            if node_lines:
                detail_blocks.append("\n".join(node_lines))

            api_detail = self._build_api_detail_for_prompt(context, prompt_type)
            if api_detail:
                detail_blocks.append("节点API详情：\n" + json.dumps(api_detail, ensure_ascii=False, indent=2))
            if context_data:
                # Keep context in prompt (for correctness), but avoid dumping big nested objects
                # that slow down slot filling / AMIS generation.
                compact_context = self._compact_context_data_for_prompt(context_data, node)
                if compact_context:
                    detail_blocks.append(
                        "上下文数据（前序节点输出，已压缩）：\n"
                        + json.dumps(compact_context, ensure_ascii=False, indent=2)
                    )
                else:
                    # Fallback: provide keys only so the model knows what's available without payload bloat.
                    keys_preview = sorted([k for k in context_data.keys() if isinstance(k, str)])[:80]
                    detail_blocks.append("上下文数据（前序节点输出，仅键名）：\n" + json.dumps(keys_preview, ensure_ascii=False, indent=2))

        elif prompt_type == "workflow_entry":
            workflow_id = workflow.get("id", workflow.get("workflow_id", ""))
            workflow_name = workflow.get("name", "")
            detail_info = {
                "id": workflow_id,
                "name": workflow_name,
                "desc": workflow.get("description", workflow.get("desc", ""))
            }
            if workflow.get("node_chain"):
                detail_info["node_chain"] = workflow.get("node_chain")

            first_node = {}
            if node:
                node_id = node.get("id", "")
                full_node_id = self._format_node_id(workflow_id, node_id) if node_id else node_id
                ai_instructions = node.get("ai_instructions", {}) if isinstance(node.get("ai_instructions", {}), dict) else {}
                first_node = {
                    "id": full_node_id or node_id,
                    "name": node.get("name", ""),
                    "type": node.get("type", ""),
                    "ai_instructions": ai_instructions
                }
                api_detail = self._build_api_detail_for_prompt(context, prompt_type)
                if api_detail:
                    first_node["api"] = api_detail
            if first_node:
                detail_info["first_node"] = first_node

            detail_blocks.append("工作流详情：\n" + json.dumps(detail_info, ensure_ascii=False, indent=2))
        else:
            api_detail = self._build_api_detail_for_prompt(context, prompt_type)
            if api_detail:
                detail_blocks.append("API详情：\n" + json.dumps(api_detail, ensure_ascii=False, indent=2))
            elif workflow:
                detail_info = {
                    "id": workflow.get("id", workflow.get("workflow_id", "")),
                    "name": workflow.get("name", ""),
                    "desc": workflow.get("description", workflow.get("desc", ""))
                }
                detail_blocks.append("工作流详情：\n" + json.dumps(detail_info, ensure_ascii=False, indent=2))
            else:
                detail_blocks.append("详情：无")

        slots_json = json.dumps(slots, ensure_ascii=False)
        prompt = "\n\n".join([b for b in detail_blocks if b])
        if prompt:
            prompt += "\n\n"
        prompt += f"任务：为以下槽位生成中文文案（JSON 格式）：\n{slots_json}"

        if prompt_type == "workflow_step":
            api_url_rule = "- api_url：完整的 API 路径（如果有路径参数且上下文中有值，直接使用具体值）"
        else:
            api_url_rule = "- api_url：完整的 API 路径（如果有路径参数，使用 ${param} 格式）"

        requirements = [
            "- page_title：3-6 字",
            "- user_message：10-20 字",
        ]

        if any(isinstance(s, str) and s.startswith("field_label_") for s in slots):
            requirements.append("- field_label_xxx：2-4 字")
        if any(isinstance(s, str) and s.startswith("resp_label_") for s in slots):
            requirements.append("- resp_label_xxx：返回字段中文名（2-4 字）")
        if "api_url" in slots:
            requirements.append(api_url_rule)
        if "api_method" in slots:
            requirements.append("- api_method：HTTP 方法（GET/POST/PUT/DELETE）")

        requirements.append("- 只输出 JSON，不要其他内容")

        prompt += "\n\n要求：\n" + "\n".join(requirements)

        # Prompt can be long; keep it at debug to avoid flooding logs in normal runs.
        logger.debug(f"[SlotFilling] Prompt:\n{prompt}")
        return prompt

    async def _call_ai_for_slots(
        self,
        prompt: str,
        slots: List[str],
        user_instruction: str = "",
        inference_trace_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        调用 AI 填充槽位（输出很短，速度快）
        
        Args:
            prompt: 槽填充提示
            slots: 槽位列表
        
        Returns:
            槽位值字典
        """
        # 检查模型是否加载
        if not self.llm_service.is_loaded:
            logger.warning("⚠️ LLM 模型未加载，使用默认槽位值")
            return self._get_default_slot_values(slots)
        
        messages = [{"role": "system", "content": prompt}]
        if user_instruction:
            messages.append({"role": "user", "content": user_instruction})
        
        try:
            # 使用异步方式调用
            import asyncio
            loop = asyncio.get_event_loop()
            invoke_kwargs: Dict[str, Any] = {
                "max_new_tokens": 1000,  # 槽位填充输出较长时避免截断
                "temperature": 0.2,
                "top_p": 0.8,
                "do_sample": False
            }
            if inference_trace_id:
                invoke_kwargs["__metrics_trace_id"] = inference_trace_id
            output = await loop.run_in_executor(
                None,
                lambda: self.llm_service._generate_single_turn(
                    messages,
                    **invoke_kwargs
                )
            )
            
            logger.info(f"[SlotFilling] Raw output:\n{output}")
            
            # 解析 JSON
            slot_values = self._parse_slot_values(output, slots)
            
            # 验证所有槽位都有值
            for slot in slots:
                if slot not in slot_values:
                    slot_values[slot] = self._get_default_value_for_slot(slot)
            
            return slot_values
            
        except Exception as e:
            logger.error(f"❌ AI 槽填充调用失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return self._get_default_slot_values(slots)
    
    def _parse_slot_values(self, output: str, slots: List[str]) -> Dict[str, str]:
        """
        从 AI 输出中解析槽位值
        
        Args:
            output: AI 原始输出
            slots: 期望的槽位列表
        
        Returns:
            槽位值字典
        """
        try:
            # 优先使用模型自带的容错 JSON 解析
            if hasattr(self.llm_service, "_try_parse_json"):
                parsed = self.llm_service._try_parse_json(output)
                if isinstance(parsed, dict):
                    filtered_values = {k: v for k, v in parsed.items() if k in slots}
                    logger.debug(f"解析到 {len(filtered_values)} 个槽位值")
                    return filtered_values

            # 提取 JSON 部分
            json_start = output.find('{')
            json_end = output.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning("⚠️ AI 输出中未找到 JSON")
                return {}
            
            json_str = output[json_start:json_end]
            slot_values = json.loads(json_str)
            
            # 验证类型
            if not isinstance(slot_values, dict):
                logger.warning(f"⚠️ AI 输出不是字典类型: {type(slot_values)}")
                return {}
            
            # 过滤掉不在槽位列表中的键
            filtered_values = {k: v for k, v in slot_values.items() if k in slots}
            
            logger.debug(f"解析到 {len(filtered_values)} 个槽位值")
            return filtered_values
            
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON 解析失败: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"❌ 槽位值解析异常: {str(e)}")
            return {}

    def _postprocess_slot_values(self, slot_values: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        context_data = context.get("context_data") or {}
        api_detail = self._extract_api_detail(context)
        prompt_type = context.get("prompt_type") or ""

        # For direct API forms, api_url/api_method are authoritative from API config.
        if prompt_type == "api_only":
            if api_detail.get("path"):
                slot_values["api_url"] = api_detail.get("path")
            if api_detail.get("method"):
                slot_values["api_method"] = api_detail.get("method")
        else:
            api_url = slot_values.get("api_url")
            if api_detail.get("path") and (not isinstance(api_url, str) or not api_url or api_url == "??"):
                slot_values["api_url"] = api_detail.get("path")

            api_method = slot_values.get("api_method")
            if api_detail.get("method") and (not isinstance(api_method, str) or not api_method or api_method == "??"):
                slot_values["api_method"] = api_detail.get("method")

        api_url = slot_values.get("api_url")
        if isinstance(api_url, str) and api_url:
            slot_values["api_url"] = self._normalize_api_url(api_url, context_data)
        return slot_values

    def _normalize_api_url(self, api_url: str, context_data: Dict[str, Any]) -> str:
        if not api_url:
            return api_url
        
        import re
        
        def _first_item_id(items: List[Dict[str, Any]]) -> Optional[Any]:
            for item in items:
                if isinstance(item, dict):
                    if "id" in item:
                        return item["id"]
                    for key in ("_id", "uuid"):
                        if key in item:
                            return item[key]
            return None
        
        def _find_context_value(param_name: str) -> Optional[Any]:
            if param_name in context_data:
                value = context_data[param_name]
                if isinstance(value, dict) and "id" in value:
                    return value["id"]
                return value
            
            if param_name.endswith("_id"):
                base_name = param_name[:-3]
                if base_name in context_data:
                    value = context_data[base_name]
                    if isinstance(value, dict) and "id" in value:
                        return value["id"]
                    if isinstance(value, list):
                        return _first_item_id(value)
                    return value
                
                plural_key = f"{base_name}s"
                if plural_key in context_data and isinstance(context_data[plural_key], list):
                    return _first_item_id(context_data[plural_key])
                
                list_key = f"{base_name}_list"
                if list_key in context_data and isinstance(context_data[list_key], list):
                    return _first_item_id(context_data[list_key])
            
            alt_key = f"{param_name}_id"
            if alt_key in context_data:
                return context_data[alt_key]

            if param_name == "id":
                id_keys = [k for k, v in context_data.items() if k.endswith("_id") and isinstance(v, (str, int, float, bool))]
                if len(id_keys) == 1:
                    return context_data[id_keys[0]]
            
            return None
        
        def _replace_param(match: "re.Match") -> str:
            param_name = match.group(1)
            value = _find_context_value(param_name)
            if isinstance(value, (str, int, float, bool)):
                return str(value)
            return f"${{{param_name}}}"
        
        api_url = re.sub(r'(?<!\$)\{(\w+)\}', _replace_param, api_url)
        return api_url

    def _get_default_slot_values(self, slots: List[str]) -> Dict[str, str]:
        """
        获取所有槽位的默认值
        
        Args:
            slots: 槽位列表
        
        Returns:
            默认槽位值字典
        """
        default_values = {}
        for slot in slots:
            default_values[slot] = self._get_default_value_for_slot(slot)
        return default_values
    
    def _get_default_value_for_slot(self, slot: str) -> str:
        """
        获取单个槽位的默认值
        
        Args:
            slot: 槽位名称
        
        Returns:
            默认值
        """
        # 根据槽位名称推断默认值
        if slot == "page_title":
            return "操作界面"
        elif slot == "user_message":
            return "请填写信息"
        elif slot.startswith("field_label_"):
            return ""
        elif slot == "submit_button_text":
            return "提交"
        elif slot == "cancel_button_text":
            return "取消"
        elif slot == "continue_button_text":
            return "继续"
        else:
            return "内容"
    
    def _replace_path_params(self, path: str, context_data: Dict) -> str:
        """根据上下文替换 API path 中的 {xxx}"""
        import re
        
        def replace_param(match):
            param_name = match.group(1)
            if param_name in context_data:
                return f"${{{param_name}}}"
            return match.group(0)
        
        return re.sub(r'\{(\w+)\}', replace_param, path)

    def _merge_slots(self, slots: List[str], context: Dict[str, Any]) -> List[str]:
        extra_slots = context.get("extra_slots", []) or []
        merged = list(slots)
        for slot in extra_slots:
            if slot not in merged:
                merged.append(slot)
        
        form_fields = context.get("form_fields") or []
        for field in form_fields:
            if isinstance(field, dict) and field.get("name"):
                slot = f"field_label_{field.get('name')}"
                if slot not in merged:
                    merged.append(slot)

        fields = context.get("fields") or []
        for field in fields:
            if isinstance(field, dict) and field.get("name"):
                slot = f"field_label_{field.get('name')}"
                if slot not in merged:
                    merged.append(slot)

        outputs = context.get("outputs") or []
        prompt_type = context.get("prompt_type", "")
        for output in outputs:
            if not isinstance(output, dict) or not output.get("name"):
                continue
            if prompt_type == "workflow_step" and output.get("type") == "array":
                continue
            slot = f"field_label_{output.get('name')}"
            if slot not in merged:
                merged.append(slot)

        # 上下文字段是否需要展示/生成 label，默认不生成，避免槽位数量爆炸；
        # 仅当节点配置显式提供 context_fields 白名单时才生成对应标签槽位。
        context_data = context.get("context_data") or {}
        context_fields = context.get("context_fields") or []
        if not context_fields:
            node = context.get("node") or {}
            config = node.get("config") or {}
            context_fields = config.get("context_fields") or []

        if context_data and context_fields:
            if "context_info_title" not in merged:
                merged.append("context_info_title")
            for key in context_fields:
                if key in context_data:
                    slot = f"field_label_{key}"
                    if slot not in merged:
                        merged.append(slot)

        api_detail = self._extract_api_detail(context)
        # Only ask the model for api_url/api_method when they can vary (workflow nodes).
        if prompt_type in {"workflow_entry", "workflow_step"} and api_detail:
            for slot in ("api_url", "api_method"):
                if slot not in merged:
                    merged.append(slot)
        
        return merged

    def _compact_context_data_for_prompt(self, context_data: Dict[str, Any], node: Dict[str, Any]) -> Dict[str, Any]:
        """
        将上下文数据压缩为“对当前节点有用”的短版本，避免把大对象塞进 prompt。
        - 保留标量字段（str/int/float/bool）优先
        - 对 list/dict 仅保留简要摘要（数量/键名）
        """
        if not isinstance(context_data, dict) or not context_data:
            return {}

        config = (node or {}).get("config") or {}
        context_fields = config.get("context_fields") or config.get("context_display_fields") or []

        result: Dict[str, Any] = {}

        def _compact_value(key: str, value: Any) -> Optional[Any]:
            if value is None:
                return None
            if isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, list):
                return {"_type": "list", "count": len(value)}
            if isinstance(value, dict):
                keys = list(value.keys())[:8]
                return {"_type": "object", "keys": keys}
            return None

        def _add_key(key: str, value: Any) -> None:
            if key in result:
                return
            compacted = _compact_value(key, value)
            if compacted is not None:
                result[key] = compacted

        # 1) 白名单字段（如果配置了）优先
        for key in context_fields:
            if key in context_data:
                _add_key(key, context_data.get(key))

        # 2) 基于节点配置推断“可能需要”的字段
        candidate_keys: List[str] = []

        # 从 parameters / inputs / outputs 收集字段名
        parameters = config.get("parameters") or {}
        for param_name, param_value in parameters.items():
            if param_name:
                candidate_keys.append(param_name)
            if isinstance(param_value, str):
                # 提取 ${var} 或 {{ var }} 中的变量名
                matches = re.findall(r"\$\{([^}]+)\}|\{\{\s*([^}]+)\s*\}\}", param_value)
                for m1, m2 in matches:
                    var_name = (m1 or m2 or "").strip()
                    if var_name:
                        var_name = var_name.split(".")[-1]
                        candidate_keys.append(var_name)

        for item in (node or {}).get("inputs", []) or []:
            if isinstance(item, dict) and item.get("name"):
                candidate_keys.append(item.get("name"))

        for item in (node or {}).get("outputs", []) or []:
            if isinstance(item, dict) and item.get("name"):
                candidate_keys.append(item.get("name"))

        # 去重但保留顺序
        seen = set()
        ordered_candidates = []
        for key in candidate_keys:
            if key and key not in seen:
                seen.add(key)
                ordered_candidates.append(key)

        for key in ordered_candidates:
            if key in context_data:
                _add_key(key, context_data.get(key))

        # 3) 补充少量其它标量字段
        for key, value in context_data.items():
            if key in result:
                continue
            # 只补充标量，避免大对象
            if isinstance(value, (list, dict)):
                continue
            _add_key(key, value)
            if len(result) >= 12:
                break

        return result

    def _extract_api_detail(self, context: Dict[str, Any]) -> Dict[str, Any]:
        api = context.get("api") or {}
        node = context.get("node") or {}
        config = node.get("config") or {}

        path = (
            api.get("path")
            or api.get("endpoint")
            or api.get("url")
            or config.get("api_endpoint")
            or ""
        )
        method = api.get("method") or config.get("method") or ""
        desc = api.get("desc") or api.get("description") or node.get("description") or ""

        request_params = (
            api.get("request")
            or api.get("parameters")
            or api.get("request_params")
            or config.get("parameters")
            or []
        )
        request = self._normalize_request_params(request_params)

        response_params = api.get("response") or api.get("responses") or node.get("outputs") or []
        response = self._normalize_response_fields(response_params)

        detail = {}
        if api.get("id"):
            detail["id"] = api.get("id")
        elif config.get("api_id"):
            detail["id"] = config.get("api_id")
        if path:
            detail["path"] = path
        if method:
            detail["method"] = method
        if desc:
            detail["desc"] = desc
        if request:
            detail["request"] = request
        if response:
            detail["response"] = response

        return detail
    def _normalize_request_params(self, params: Any) -> List[Dict[str, Any]]:
        if isinstance(params, dict):
            return [{"name": name, "type": "string"} for name in params.keys()]
        if isinstance(params, list):
            normalized = []
            for item in params:
                if isinstance(item, dict):
                    normalized.append({k: item.get(k) for k in ("name", "type", "label", "required") if item.get(k) is not None})
                elif isinstance(item, str):
                    normalized.append({"name": item, "type": "string"})
            return [p for p in normalized if p]
        return []

    def _normalize_response_fields(self, params: Any) -> List[Dict[str, Any]]:
        if isinstance(params, list):
            normalized = []
            for item in params:
                if isinstance(item, dict):
                    normalized.append({k: item.get(k) for k in ("name", "type", "desc", "description") if item.get(k) is not None})
                elif isinstance(item, str):
                    normalized.append({"name": item, "type": "string"})
            return [p for p in normalized if p]
        return []


# 全局实例
slot_filling_service = SlotFillingService()
