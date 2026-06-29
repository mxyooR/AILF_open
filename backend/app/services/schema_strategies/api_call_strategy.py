"""
API Call 节点策略 - Slot-Filling 架构

处理 GET 和 POST 类型的 API 调用节点

支持多种展示类型：
1. Table - 表格展示（列表数据）
2. Cards - 卡片展示（商品、用户等）
3. Service - 服务容器（自定义展示）
4. Form - 表单提交（POST）
5. Chart - 图表展示（统计数据，由 ChartStrategy 处理）

展示类型推断规则：
- 优先使用节点配置中的 display_type
- 根据 API 响应结构自动推断
- 降级到默认展示

Slot-Filling 集成：
- 规则生成器：提供 AMIS 模板骨架
- AI 填充：页面标题、用户提示、字段标签等动态文案
"""
from typing import Dict, Any, Optional, List
import re
import asyncio
import json
from .base import NodeStrategy
from app.core.logging_config import get_logger
from app.core.database import get_db_session
from app.models.api_route import APIRouteDBModel

logger = get_logger(__name__)

class ApiCallStrategy(NodeStrategy):
    """API Call 节点策略 - Slot-Filling 架构"""
    
    def __init__(self, template_loader):
        super().__init__(template_loader)
        self._slot_filling_service = None
    
    @property
    def slot_filling_service(self):
        """延迟加载槽填充服务"""
        if self._slot_filling_service is None:
            from app.services.slot_filling_service import slot_filling_service
            self._slot_filling_service = slot_filling_service
        return self._slot_filling_service
    
    def can_handle(self, node: Dict[str, Any]) -> bool:
        """判断是否为 api_call 节点"""
        return node.get("type") == "api_call"
    
    def generate_schema(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None,
        user_instruction: str = "",
        slot_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成 API Call 节点界面（Slot-Filling 架构）
        
        根据 HTTP Method 和 display_type 选择不同的生成策略
        """
        config = node.get("config", {})
        method = config.get("method", "GET").upper()
        logger.info(f"生成 API Call 节点 Schema: method={method}")
        
        if method == "GET":
            return self._generate_get_schema(workflow, node, context_data, user_instruction, slot_values)
        else:
            return self._generate_post_schema(workflow, node, context_data, user_instruction, slot_values)

    def _run_async(self, coro):
        """Run an async coroutine safely from sync context."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        import concurrent.futures

        def _runner():
            return asyncio.run(coro)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(_runner).result()

    def _resolve_workflow_id(self, workflow: Dict[str, Any]) -> str:
        """兼容 workflow.id 与 workflow.workflow_id 两种结构。"""
        return workflow.get("id") or workflow.get("workflow_id") or ""

    def _normalize_workflow_for_template(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """保证模板能读取 workflow.id。"""
        workflow_id = self._resolve_workflow_id(workflow)
        if workflow.get("id") or not workflow_id:
            return workflow
        normalized = dict(workflow)
        normalized["id"] = workflow_id
        return normalized
    
    def _generate_get_schema(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None,
        user_instruction: str = "",
        slot_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成 GET 请求的界面 - 使用 AMIS Wizard
        
        所有 GET 节点都使用 Wizard 的 initApi 自动获取数据
        """
        logger.info("生成 GET 节点 Wizard Schema")
        
        # 使用 Wizard 模板
        return self._generate_wizard_get_with_slots(workflow, node, context_data, user_instruction, slot_values)
    
    def _infer_display_type(self, node: Dict[str, Any]) -> str:
        """
        自动推断展示类型
        
        推断规则：
        1. 检查节点描述关键词
        2. 检查输出字段结构
        3. 默认 service
        """
        desc = node.get("description", "").lower()
        outputs = node.get("outputs", [])
        
        # 关键词匹配
        if any(kw in desc for kw in ["列表", "查询", "搜索", "list", "search"]):
            return "table"
        elif any(kw in desc for kw in ["卡片", "商品", "用户", "card", "product"]):
            return "cards"
        
        # 检查输出结构
        has_array = any(o.get("type") == "array" for o in outputs)
        if has_array:
            # 有数组输出，默认表格
            return "table"
        
        # 默认 service
        return "service"
    
    def _generate_table_display_with_slots(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None,
        user_instruction: str = ""
    ) -> Dict[str, Any]:
        """
        生成表格展示界面（Slot-Filling 架构）
        
        使用 AMIS Table 组件 + AI 填充文案
        """
        config = node.get("config", {})
        api_endpoint = config.get("api_endpoint", "")
        outputs = node.get("outputs", [])
        
        context_data = context_data or {}
        
        # 找到数组类型的输出
        array_output = next((o for o in outputs if o.get("type") == "array"), None)
        if not array_output:
            logger.warning("未找到数组输出，降级为 service 展示")
            # 没有数组输出，降级到 service
            return self._generate_service_display_with_slots(workflow, node, context_data, user_instruction)
        
        table_source = array_output.get("name", "items")
        
        # 构建表格列（从 array 的 items 定义中提取）
        fields = self._extract_table_fields(array_output)
        
        # 获取模板内容
        template_content = self.template_loader.get_template_content("api_call_table.json.j2")
        
        api_detail = self._build_api_detail_from_node(node)
        ai_instructions = node.get("ai_instructions") or {}
        default_instruction = ""
        if isinstance(ai_instructions, dict):
            default_instruction = ai_instructions.get("user_message", "") or node.get("description", "")
        else:
            default_instruction = node.get("description", "")
        # AI 填充槽位
        slot_values = self._run_async(
            self.slot_filling_service.fill_slots(
                template=template_content,
                context={
                    "workflow": workflow,
                    "node": node,
                    "fields": fields,
                    "context_data": context_data,
                    "api": api_detail,
                    "prompt_type": "workflow_step"
                },
                user_instruction=user_instruction or default_instruction
            )
        )
        
        # 合并规则值和槽位值
        template_values = {
            "workflow_id": self._resolve_workflow_id(workflow),
            "node_id": node.get("id", ""),
            "api_endpoint": api_endpoint,
            "table_source": table_source,
            "fields": fields,
            "outputs": outputs,
            "slot_values": slot_values,
            **slot_values
        }
        
        # 渲染最终 Schema
        schema = self.template_loader.render("api_call_table.json.j2", **template_values)
        
        return schema
    
    def _generate_wizard_get_with_slots(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None,
        user_instruction: str = "",
        slot_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate Wizard GET node schema using initApi."""
        config = node.get("config", {})
        route_cfg = self._resolve_route_config(config)
        api_endpoint = route_cfg.get("endpoint") or config.get("api_endpoint", "")
        api_method = (route_cfg.get("method") or config.get("method", "GET")).upper()
        parameters = config.get("parameters", {}) or {}
        outputs = node.get("outputs", [])
        inputs = node.get("inputs", [])

        context_data = context_data or {}
        workflow_id = self._resolve_workflow_id(workflow)
        workflow_for_template = self._normalize_workflow_for_template(workflow)

        # Build display fields from outputs
        display_fields = []
        for output in outputs:
            display_fields.append({
                "name": output.get("name", ""),
                "label": output.get("label") or output.get("description") or output.get("name", ""),
                "type": output.get("type", "string")
            })

        # Detect primary list field (first array output or explicit config)
        array_outputs = [
            output for output in outputs
            if output.get("type") == "array" and output.get("name")
        ]
        list_field = config.get("list_field") or config.get("array_field")
        if not list_field and array_outputs:
            list_field = array_outputs[0].get("name")

        # Prefer configured api_endpoint; only accept AI api_url if it matches
        api_url = api_endpoint
        if slot_values and slot_values.get("api_url"):
            candidate_url = slot_values.get("api_url")
            normalized_endpoint = self._normalize_api_url(api_endpoint) if api_endpoint else None
            normalized_candidate = self._normalize_api_url(candidate_url) if candidate_url else None
            if normalized_endpoint and normalized_candidate and normalized_endpoint != normalized_candidate:
                logger.warning(
                    f"忽略 AI api_url（与配置不一致）: {normalized_candidate} != {normalized_endpoint}"
                )
            else:
                api_url = candidate_url
        api_url = self._normalize_api_url(api_url)

        import re

        def _extract_var(value: str) -> Optional[str]:
            if not isinstance(value, str):
                return None
            value = value.strip()
            m = re.match(r"^\$\{([^}]+)\}$", value)
            if not m:
                m = re.match(r"^\{\{\s*([^}]+)\s*\}\}$", value)
            if not m:
                return None
            var_name = m.group(1).strip()
            if var_name.startswith("inputs."):
                var_name = var_name[7:]
            if var_name.startswith("input."):
                var_name = var_name[6:]
            # 处理命名空间变量（如 train_query.train_number）
            # 如果包含点号，尝试提取最后一部分作为字段名
            if "." in var_name:
                # 检查上下文中是否有完整的命名空间对象
                namespace = var_name.split(".")[0]
                field = var_name.split(".", 1)[1]
                # 如果上下文中没有命名空间对象，但有字段本身，使用字段名
                if namespace not in context_data and field in context_data:
                    var_name = field
            return var_name

        # Build request params mapping for initApi
        request_params = {}
        for param_name, param_value in parameters.items():
            var_name = _extract_var(param_value)
            if var_name:
                request_params[param_name] = f"${{{var_name}}}"
            else:
                request_params[param_name] = param_value

        # Extract placeholders from URL
        placeholders = re.findall(r"\$\{([^}]+)\}", api_url or "")

        # Build input fields
        form_fields = []
        seen_fields = set()

        def _add_field(field_name: str) -> None:
            if not field_name or field_name in seen_fields:
                return
            seen_fields.add(field_name)
            if field_name in context_data:
                form_fields.append({
                    "type": "hidden",
                    "name": field_name,
                    "value": context_data[field_name]
                })
            else:
                field = self._create_input_field(field_name)
                form_fields.append(field)

        for param_value in parameters.values():
            var_name = _extract_var(param_value)
            if var_name:
                _add_field(var_name)

        if inputs:
            for item in inputs:
                input_name = item.get("name") if isinstance(item, dict) else None
                if input_name:
                    _add_field(input_name)

        for placeholder in placeholders:
            _add_field(placeholder)

        # List-style GET nodes may still require user choice (e.g. choose ticket_number)
        # even when they have no explicit URL/query parameters.
        has_list_selection_outputs = bool(array_outputs) and any(
            isinstance(output, dict)
            and output.get("name")
            and output.get("type", "string") == "string"
            for output in outputs
            if output.get("type") != "array"
        )
        has_params = (
            bool(form_fields)
            or bool(placeholders)
            or bool(parameters)
            or has_list_selection_outputs
        )
        has_visible_fields = any(
            isinstance(field, dict) and field.get("type") != "hidden" for field in form_fields
        )
        media_kind = self._detect_media_kind(
            api_url=api_url,
            description=node.get("description", ""),
        )

        # Fill slots if missing (after form_fields are ready so we can generate labels)
        if not slot_values:
            template_content = self.template_loader.get_template_content("workflow_wizard_get.json.j2")

            api_detail = self._build_api_detail_from_node(
                node,
                route_endpoint=api_endpoint,
                route_method=api_method
            )
            ai_instructions = node.get("ai_instructions") or {}
            default_instruction = ""
            if isinstance(ai_instructions, dict):
                default_instruction = ai_instructions.get("user_message", "") or node.get("description", "")
            else:
                default_instruction = node.get("description", "")

            slot_values = self._run_async(
                self.slot_filling_service.fill_slots(
                    template=template_content,
                    context={
                        "workflow": workflow,
                        "node": node,
                        "outputs": outputs,
                        "fields": form_fields,
                        "context_data": context_data,
                        "api": api_detail,
                        "prompt_type": "workflow_step"
                    },
                    user_instruction=user_instruction or default_instruction
                )
            )

        # Apply AI field labels to input fields (keep placeholder in sync)
        if slot_values:
            for field in form_fields:
                if not isinstance(field, dict) or field.get("type") == "hidden":
                    continue
                name = field.get("name")
                if not name:
                    continue
                label_key = f"field_label_{name}"
                if label_key in slot_values:
                    old_label = field.get("label")
                    field["label"] = slot_values[label_key]
                    placeholder = field.get("placeholder")
                    if placeholder and isinstance(old_label, str):
                        if placeholder in (f"请输入{old_label}", f"请选择{old_label}"):
                            field["placeholder"] = f"请输入{field['label']}"

        # Build display body for GET wizard
        if has_params:
            if media_kind and not has_visible_fields:
                return self._render_media_step_schema(
                    workflow_id=workflow_id,
                    workflow=workflow,
                    node=node,
                    api_url=api_url,
                    media_kind=media_kind,
                    slot_values=slot_values,
                    request_params=request_params,
                    form_fields=form_fields
                )

            path_params = set(placeholders)
            init_api_data = {}
            if request_params:
                init_api_data = {k: v for k, v in request_params.items() if k not in path_params}
            for field in form_fields:
                field_name = field.get("name")
                if field_name and field_name not in init_api_data and field_name not in path_params:
                    init_api_data[field_name] = f"${{{field_name}}}"

            label_map = self._build_field_label_map(outputs, config)
            init_api = {
                "method": "get",
                "url": api_url,
                "adaptor": self._build_init_api_adaptor(list_field, label_map=label_map)
            }
            if init_api_data:
                init_api["data"] = init_api_data

            hidden_fields = self._build_hidden_fields_for_outputs(outputs)

            display_body = []
            existing_field_names = {
                field.get("name") for field in form_fields
                if isinstance(field, dict) and field.get("name")
            }
            array_output = array_outputs[0] if array_outputs else None
            list_source = f"${{{list_field}}}" if list_field else "${items}"

            if array_output:
                array_label = array_output.get("label") or array_output.get("description") or "列表"
                table_columns = config.get("list_columns") or config.get("table_columns")
                if isinstance(table_columns, list) and table_columns:
                    display_body.append({
                        "type": "table",
                        "title": array_label,
                        "source": list_source,
                        "columns": table_columns
                    })
                else:
                    display_body.append({
                        "type": "table",
                        "title": array_label,
                        "source": "${__list_items__}",
                        "columns": [
                            {"name": "__label", "label": "选项", "type": "text"}
                        ]
                    })
                    display_body.append({
                        "type": "alert",
                        "level": "info",
                        "showIcon": True,
                        "body": "列表仅展示前 10 条",
                        "visibleOn": "this.__list_truncated__ === true"
                    })

                for output in outputs:
                    output_name = output.get("name")
                    output_type = output.get("type", "string")
                    if not output_name or output_name in existing_field_names:
                        continue
                    if output_type == "array":
                        continue
                    output_label = output.get("label") or output.get("description") or output_name
                    if output_type in ("string",):
                        item_field = self._guess_item_field_name(output_name)
                        label_field = item_field or "__label"
                        value_field = item_field or "__value"
                        auto_fill = {}
                        auto_fill_from_item = {}
                        for candidate in outputs:
                            candidate_name = candidate.get("name")
                            candidate_type = candidate.get("type", "string")
                            if (
                                not candidate_name
                                or candidate_name in existing_field_names
                                or candidate_type not in ("number", "integer")
                            ):
                                continue
                            candidate_item_field = self._guess_item_field_name(candidate_name)
                            if candidate_item_field:
                                auto_fill[candidate_name] = f"${{{candidate_item_field}}}"
                                auto_fill_from_item[candidate_name] = candidate_item_field

                        select_field = {
                            "type": "select",
                            "name": output_name,
                            "label": output_label,
                            "required": output.get("required", True),
                            "source": list_source,
                            "labelField": label_field,
                            "valueField": value_field,
                            "placeholder": f"请选择{output_label}",
                        }
                        if auto_fill:
                            # When selecting an option from list results, sync numeric companion fields
                            # (e.g. seat_price/amount) from the selected row instead of manual input.
                            select_field["autoFill"] = auto_fill
                            select_field["onEvent"] = {
                                "change": {
                                    "actions": [
                                        {
                                            "actionType": "setValue",
                                            "args": {
                                                "value": {
                                                    key: f"${{event.data.item.{item_field}}}"
                                                    for key, item_field in auto_fill_from_item.items()
                                                }
                                            },
                                        }
                                    ]
                                }
                            }
                        display_body.append(select_field)
                    elif output_type in ("number", "integer"):
                        # Numeric outputs from list-style GET nodes are derived in backend context
                        # (or through select autoFill) and should not require manual input.
                        continue
            elif display_fields:
                display_tpl = "<div class='data-display'>" + "".join(
                    [
                        f"<p><strong>{{field['label']}}:</strong> ${{{field['name']}}}</p>"
                        for field in display_fields
                        if field.get("type") != "array"
                    ]
                ) + "</div>"
                display_body.append({
                    "type": "static",
                    "label": "数据详情",
                    "tpl": display_tpl
                })
            if hidden_fields:
                display_body.extend(hidden_fields)
            else:
                display_body.append({
                    "type": "tpl",
                    "tpl": "<div class='data-loaded'>数据已加载</div>"
                })

            api_request_context = {
                "method": "GET",
                "url": api_url
            }
            if request_params:
                api_request_context["params"] = request_params
            elif init_api_data:
                api_request_context["params"] = init_api_data

            api_data_payload = {
                "workflow_id": workflow_id,
                "node_id": node.get("id"),
                "action": "next",
                "api_request": api_request_context,
                "api_response": "${__api_response__}"
            }
            for field in display_fields:
                field_name = field.get("name")
                if field_name and field_name not in api_data_payload:
                    api_data_payload[field_name] = f"${{{field_name}}}"

            if has_visible_fields:
                schema = {
                    "type": "page",
                    "title": (slot_values or {}).get("page_title", workflow.get("name", "")[:6]),
                    "workflow_id": workflow_id,
                    "current_node_id": node.get("id"),
                    "body": {
                        "type": "wizard",
                        "mode": "horizontal",
                        "steps": [
                            {
                                "title": "输入信息",
                                "body": [
                                    {
                                        "type": "alert",
                                        "level": "info",
                                        "body": (slot_values or {}).get("user_message", node.get("description", "请输入参数")),
                                        "showIcon": True
                                    }
                                ] + form_fields
                            },
                            {
                                "title": node.get("description", "数据详情"),
                                "initApi": init_api,
                                "body": display_body,
                                "api": {
                                    "method": "post",
                                    "url": "/api/v1/workflow/state",
                                    "data": api_data_payload
                                }
                            }
                        ],
                        "actionFinishLabel": (slot_values or {}).get("next_button_text", "下一步")
                    }
                }

                return schema

            # No visible params: render single-step wizard with initApi and display body
            path_params = set(placeholders)
            init_api_data = {}
            if request_params:
                init_api_data = {k: v for k, v in request_params.items() if k not in path_params}
            for field in form_fields:
                field_name = field.get("name")
                if field_name and field_name not in init_api_data and field_name not in path_params:
                    init_api_data[field_name] = f"${{{field_name}}}"

            # resolve hidden field values for initApi when no visible fields
            hidden_values = {
                field.get("name"): field.get("value")
                for field in form_fields
                if isinstance(field, dict) and field.get("type") == "hidden" and field.get("name")
            }
            for key, value in list(init_api_data.items()):
                if isinstance(value, str):
                    match = re.match(r"^\$\{([^}]+)\}$", value)
                    if match and match.group(1) in hidden_values:
                        init_api_data[key] = hidden_values[match.group(1)]

            for key, value in hidden_values.items():
                if key and key not in init_api_data and key not in path_params:
                    init_api_data[key] = value

            resolved_api_url = api_url
            for placeholder in placeholders:
                if placeholder in hidden_values and hidden_values[placeholder] is not None:
                    resolved_api_url = resolved_api_url.replace(
                        f"${{{placeholder}}}",
                        str(hidden_values[placeholder])
                    )

            init_api = {
                "method": "get",
                "url": resolved_api_url,
                "adaptor": self._build_init_api_adaptor(list_field)
            }
            if init_api_data:
                init_api["data"] = init_api_data

            api_request_context = {
                "method": "GET",
                "url": resolved_api_url
            }
            if request_params:
                api_request_context["params"] = request_params
            elif init_api_data:
                api_request_context["params"] = init_api_data

            api_data_payload = {
                "workflow_id": workflow_id,
                "node_id": node.get("id"),
                "action": "next",
                "api_request": api_request_context,
                "api_response": "${__api_response__}"
            }
            for field in display_fields:
                field_name = field.get("name")
                if field_name and field_name not in api_data_payload:
                    api_data_payload[field_name] = f"${{{field_name}}}"

            # prepend user_message for clarity
            if slot_values and slot_values.get("user_message"):
                display_body = [
                    {
                        "type": "alert",
                        "level": "info",
                        "body": slot_values.get("user_message"),
                        "showIcon": True
                    }
                ] + display_body

            schema = {
                "type": "page",
                "title": (slot_values or {}).get("page_title", workflow.get("name", "")[:6]),
                "workflow_id": workflow_id,
                "current_node_id": node.get("id"),
                "body": {
                    "type": "wizard",
                    "mode": "horizontal",
                    "steps": [
                        {
                            "title": node.get("description", "数据详情"),
                            "initApi": init_api,
                            "body": display_body,
                            "api": {
                                "method": "post",
                                "url": "/api/v1/workflow/state",
                                "data": api_data_payload
                            }
                        }
                    ],
                    "actionFinishLabel": (slot_values or {}).get("next_button_text", "下一步")
                }
            }

            return schema

        # No params: render single-step wizard template
        if media_kind:
            return self._render_media_step_schema(
                workflow_id=workflow_id,
                workflow=workflow,
                node=node,
                api_url=api_url,
                media_kind=media_kind,
                slot_values=slot_values,
                request_params=request_params,
                form_fields=form_fields
            )

        template_values = {
            "workflow": workflow_for_template,
            "node": node,
            "api_url": api_url,
            "display_fields": display_fields,
            "list_field": list_field,
            "init_api_adaptor": self._build_init_api_adaptor(list_field),
            "page_title": workflow.get("name", "")[:6],
            "user_message": node.get("description", "正在获取数据..."),
            "next_button_text": "下一步",
            **(slot_values or {})
        }

        schema = self.template_loader.render("workflow_wizard_get.json.j2", **template_values)
        return schema

    
    def _generate_service_display_with_slots(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None,
        user_instruction: str = ""
    ) -> Dict[str, Any]:
        """
        生成服务容器展示界面（Slot-Filling 架构）
        
        使用 AMIS Service 组件 + AI 填充文案
        """
        config = node.get("config", {})
        api_endpoint = config.get("api_endpoint", "")
        outputs = node.get("outputs", [])
        
        context_data = context_data or {}
        
        # 获取模板内容
        template_content = self.template_loader.get_template_content("api_call_service.json.j2")
        
        api_detail = self._build_api_detail_from_node(node)
        ai_instructions = node.get("ai_instructions") or {}
        default_instruction = ""
        if isinstance(ai_instructions, dict):
            default_instruction = ai_instructions.get("user_message", "") or node.get("description", "")
        else:
            default_instruction = node.get("description", "")
        # AI 填充槽位
        slot_values = self._run_async(
            self.slot_filling_service.fill_slots(
                template=template_content,
                context={
                    "workflow": workflow,
                    "node": node,
                    "outputs": outputs,
                    "context_data": context_data,
                    "api": api_detail,
                    "prompt_type": "workflow_step"
                },
                user_instruction=user_instruction or default_instruction
            )
        )
        
        # 合并规则值和槽位值
        template_values = {
            "workflow_id": self._resolve_workflow_id(workflow),
            "node_id": node.get("id", ""),
            "api_endpoint": api_endpoint,
            "outputs": outputs,
            "slot_values": slot_values,
            **slot_values
        }
        
        # 渲染最终 Schema
        schema = self.template_loader.render("api_call_service.json.j2", **template_values)
        
        return schema
    
    def _extract_table_fields(self, array_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从数组输出中提取表格字段
        
        Args:
            array_output: 数组类型的输出定义
        
        Returns:
            字段列表，如 [{"name": "order_id", "description": "订单号"}, ...]
        """
        fields = []
        
        # 尝试从 items 定义中提取
        items_schema = array_output.get("items", {})
        if isinstance(items_schema, dict):
            properties = items_schema.get("properties", {})
            for field_name, field_def in properties.items():
                fields.append({
                    "name": field_name,
                    "description": field_def.get("description", field_name)
                })
        
        # 如果没有定义，使用默认字段
        if not fields:
            fields = [
                {"name": "id", "description": "ID"},
                {"name": "name", "description": "名称"},
                {"name": "status", "description": "状态"}
            ]
        
        return fields
    
    def _infer_display_type(self, node: Dict[str, Any]) -> str:
        """
        自动推断展示类型
        
        推断规则：
        1. 检查节点描述关键词
        2. 检查输出字段结构
        3. 默认 service
        """
        desc = node.get("description", "").lower()
        outputs = node.get("outputs", [])
        
        # 关键词匹配
        if any(kw in desc for kw in ["列表", "查询", "搜索", "list", "search"]):
            return "table"
        elif any(kw in desc for kw in ["卡片", "商品", "用户", "card", "product"]):
            return "cards"
        
        # 检查输出结构
        has_array = any(o.get("type") == "array" for o in outputs)
        if has_array:
            # 有数组输出，默认表格
            return "table"
        
        # 默认 service
        return "service"
    
    def _generate_post_schema(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None,
        user_instruction: str = "",
        slot_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成 POST 请求的界面（Slot-Filling 架构）
        
        根据参数定义生成表单字段 + AI 填充文案
        """
        config = node.get("config", {})
        parameters = config.get("parameters", {})
        
        context_data = context_data or {}
        context_display = self._get_context_display(node, context_data)
        
        # 解析参数，生成表单字段
        form_fields = self._parse_parameters_to_fields(
            parameters,
            context_data,
            workflow
        )
        
        # 获取模板内容
        template_content = self.template_loader.get_template_content("api_call_form.json.j2")
        
        api_detail = self._build_api_detail_from_node(node)
        ai_instructions = node.get("ai_instructions") or {}
        default_instruction = ""
        if isinstance(ai_instructions, dict):
            default_instruction = ai_instructions.get("user_message", "") or node.get("description", "")
        else:
            default_instruction = node.get("description", "")
        # AI 填充槽位（仅在未提供 slot_values 时触发）
        if not slot_values:
            slot_values = self._run_async(
                self.slot_filling_service.fill_slots(
                    template=template_content,
                    context={
                        "workflow": workflow,
                        "node": node,
                        "form_fields": form_fields,
                        "context_data": context_display,
                        "api": api_detail,
                        "prompt_type": "workflow_step"
                    },
                    user_instruction=user_instruction or default_instruction
                )
            )
        
        # 合并规则值和槽位值
        template_values = {
            "workflow_id": self._resolve_workflow_id(workflow),
            "node_id": node.get("id", ""),
            "form_fields": form_fields,
            "context_data": context_data,
            "context_display": context_display,
            "slot_values": slot_values,
            **slot_values
        }
        
        # 渲染最终 Schema
        schema = self.template_loader.render("api_call_form.json.j2", **template_values)
        
        return schema
    
    def _generate_table_display(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成表格展示界面
        
        使用 AMIS Table 组件
        """
        config = node.get("config", {})
        api_endpoint = config.get("api_endpoint", "")
        outputs = node.get("outputs", [])
        
        context_data = context_data or {}
        
        # 找到数组类型的输出
        array_output = next((o for o in outputs if o.get("type") == "array"), None)
        if not array_output:
            # 没有数组输出，降级到 service
            return self._generate_service_display(workflow, node, context_data)
        
        table_source = array_output.get("name", "items")
        
        # 构建表格列（从 array 的 items 定义中提取）
        columns = self._build_table_columns(array_output)
        
        body_content = [
            {
                "type": "alert",
                "level": "info",
                "body": node.get("description", "查询结果"),
                "showIcon": True
            },
            {
                "type": "service",
                "api": {
                    "method": "get",
                    "url": api_endpoint
                },
                "body": {
                    "type": "table",
                    "source": f"${{{table_source}}}",
                    "columns": columns
                }
            },
            {
                "type": "form",
                "api": self.build_workflow_api(
                    workflow_id=self._resolve_workflow_id(workflow),
                    node_id=node.get("id", ""),
                    action="next"
                ),
                "body": self._build_hidden_fields_for_outputs(outputs),
                "actions": [
                    {
                        "type": "submit",
                        "label": "继续",
                        "level": "primary"
                    }
                ]
            }
        ]
        
        return self.build_base_page(workflow, node, body_content)
    
    def _generate_cards_display(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成卡片展示界面
        
        使用 AMIS Cards 组件
        """
        config = node.get("config", {})
        api_endpoint = config.get("api_endpoint", "")
        outputs = node.get("outputs", [])
        
        context_data = context_data or {}
        
        # 找到数组类型的输出
        array_output = next((o for o in outputs if o.get("type") == "array"), None)
        if not array_output:
            # 没有数组输出，降级到 service
            return self._generate_service_display(workflow, node, context_data)
        
        cards_source = array_output.get("name", "items")
        
        # 构建卡片模板
        card_template = self._build_card_template(array_output)
        
        body_content = [
            {
                "type": "alert",
                "level": "info",
                "body": node.get("description", "查询结果"),
                "showIcon": True
            },
            {
                "type": "service",
                "api": {
                    "method": "get",
                    "url": api_endpoint
                },
                "body": {
                    "type": "cards",
                    "source": f"${{{cards_source}}}",
                    "card": card_template
                }
            },
            {
                "type": "form",
                "api": self.build_workflow_api(
                    workflow_id=self._resolve_workflow_id(workflow),
                    node_id=node.get("id", ""),
                    action="next"
                ),
                "body": self._build_hidden_fields_for_outputs(outputs),
                "actions": [
                    {
                        "type": "submit",
                        "label": "继续",
                        "level": "primary"
                    }
                ]
            }
        ]
        
        return self.build_base_page(workflow, node, body_content)
    
    def _generate_service_display(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成服务容器展示界面（默认/降级方案）
        
        使用 AMIS Service 组件 + 模板展示
        """
        config = node.get("config", {})
        api_endpoint = config.get("api_endpoint", "")
        outputs = node.get("outputs", [])
        
        context_data = context_data or {}
        
        # 构建结果展示
        result_body = self._build_result_display(outputs)
        
        body_content = [
            {
                "type": "alert",
                "level": "info",
                "body": node.get("description", "查询结果"),
                "showIcon": True
            },
            {
                "type": "service",
                "api": {
                    "method": "get",
                    "url": api_endpoint
                },
                "body": result_body
            },
            {
                "type": "form",
                "api": self.build_workflow_api(
                    workflow_id=self._resolve_workflow_id(workflow),
                    node_id=node.get("id", ""),
                    action="next"
                ),
                "body": self._build_hidden_fields_for_outputs(outputs),
                "actions": [
                    {
                        "type": "submit",
                        "label": "继续",
                        "level": "primary"
                    }
                ]
            }
        ]
        
        return self.build_base_page(workflow, node, body_content)
    
    def _generate_post_schema_legacy(
        self,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成 POST 请求的界面（表单提交）
        
        根据参数定义生成表单字段
        """
        config = node.get("config", {})
        parameters = config.get("parameters", {})
        
        context_data = context_data or {}
        
        # 解析参数，生成表单字段
        form_fields = self._parse_parameters_to_fields(
            parameters,
            context_data,
            workflow
        )
        
        # 添加上下文信息展示
        body_content = []
        
        ai_instructions = node.get("ai_instructions", {})
        user_message = ai_instructions.get("user_message", "请填写并确认提交")
        
        body_content.append({
            "type": "alert",
            "level": "info",
            "body": user_message,
            "showIcon": True
        })
        
        # 如果有上下文数据，展示已有信息
        if context_data:
            context_display = self._build_context_display(context_data)
            if context_display:
                body_content.append(context_display)
        
        # 表单
        form_config = {
            "type": "form",
            "title": node.get("description", "请填写信息"),
            "mode": "horizontal",
            "horizontal": {"left": 3, "right": 9},
            "api": self.build_workflow_api(
                workflow_id=self._resolve_workflow_id(workflow),
                node_id=node.get("id", ""),
                action="submit"
            ),
            "body": form_fields,
            "actions": [
                {
                    "type": "submit",
                    "label": "提交",
                    "level": "primary"
                }
            ]
        }
        
        body_content.append(form_config)
        
        return self.build_base_page(workflow, node, body_content)
    
    def _parse_parameters_to_fields(
        self,
        parameters: Dict[str, Any],
        context_data: Dict[str, Any],
        workflow: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        解析参数定义，生成表单字段
        
        智能判断：
        - 参数在上下文中 → 隐藏字段（自动填充）
        - 参数不在上下文中 → 输入字段（用户填写）
        """
        fields = []
        template_pattern = re.compile(r'^\$\{(\w+)\}$')
        seen_vars = set()
        
        for param_name, param_value in parameters.items():
            if isinstance(param_value, str):
                match = template_pattern.match(param_value)
                if match:
                    var_name = match.group(1)
                    if var_name not in seen_vars:
                        seen_vars.add(var_name)
                        
                        if var_name in context_data:
                            # 上下文中有值，生成隐藏字段
                            fields.append({
                                "type": "hidden",
                                "name": var_name,
                                "value": context_data[var_name]
                            })
                        else:
                            # 上下文中没有，生成输入字段
                            fields.append(self._create_input_field(var_name))
        
        return fields
    
    def _create_input_field(self, field_name: str) -> Dict[str, Any]:
        """
        创建输入字段
        
        根据字段名推断字段类型和标签
        """
        field_key = field_name.lower()

        # Boolean-like fields (confirm/is/has/can/should)
        boolean_like = (
            field_key.startswith(("is_", "has_", "can_", "should_", "confirm_"))
            or field_key.endswith(("_flag", "_enabled"))
        )

        # 字段类型推断
        if boolean_like:
            field_type = "switch"
            format_config = {
                "trueValue": True,
                "falseValue": False,
                "value": True if field_key.startswith("confirm_") else False
            }
        elif "date" in field_key:
            field_type = "input-date"
            format_config = {"format": "YYYY-MM-DD"}
        elif "time" in field_key and "date" not in field_key:
            field_type = "input-time"
            format_config = {"format": "HH:mm:ss"}
        elif "datetime" in field_key:
            field_type = "input-datetime"
            format_config = {"format": "YYYY-MM-DD HH:mm:ss"}
        elif any(kw in field_key for kw in ["amount", "price", "quantity", "number"]):
            field_type = "input-number"
            format_config = {}
        else:
            field_type = "input-text"
            format_config = {}
        
        label = self._get_field_label(field_name)
        
        field_config = {
            "type": field_type,
            "name": field_name,
            "label": label,
            "required": True,
            "placeholder": f"请输入{label}"
        }
        
        field_config.update(format_config)
        
        return field_config

    def _build_init_api_adaptor(
        self,
        list_field: Optional[str] = None,
        label_map: Optional[Dict[str, str]] = None,
        hidden_fields: Optional[List[str]] = None
    ) -> str:
        """
        Build a generic initApi adaptor to normalize payload shape and inject request params.
        """
        list_field_value = list_field or ""
        label_map_value = label_map or {}
        hidden_value = hidden_fields or ["id", "created_at", "updated_at"]
        return (
            f"var labelMap = {json.dumps(label_map_value, ensure_ascii=False)}; "
            f"var hiddenKeys = {json.dumps(hidden_value, ensure_ascii=False)}; "
            "function _isHidden(k){ return hiddenKeys && hiddenKeys.indexOf(k) >= 0; } "
            "var raw = payload; "
            "var safeRaw = raw; "
            "try { safeRaw = JSON.parse(JSON.stringify(raw)); } catch (e) { safeRaw = raw; } "
            "var data = payload; "
            "if (data && typeof data === 'object' && 'data' in data) { data = data.data; } "
            "if (data == null || typeof data !== 'object') { data = { value: data }; } "
            f"var listField = {json.dumps(list_field_value)}; "
            "if (data.items && listField && data[listField] == null) { data[listField] = data.items; } "
            "var request = (api && api.data) ? api.data : {}; "
            "if (request && typeof request === 'object') { "
            "  for (var k in request) { "
            "    if (Object.prototype.hasOwnProperty.call(request, k)) { "
            "      if (data[k] == null || data[k] === '') { data[k] = request[k]; } "
            "    } "
            "  } "
            "} "
            "var list = null; if (listField && Array.isArray(data[listField])) { list = data[listField]; } else if (Array.isArray(data.items)) { list = data.items; } "
            "if (Array.isArray(list)) { "
            "  var pickKey = function(keys, candidates) { "
            "    for (var i = 0; i < candidates.length; i++) { "
            "      var c = String(candidates[i]).toLowerCase(); "
            "      for (var j = 0; j < keys.length; j++) { if (String(keys[j]) === candidates[i]) { return keys[j]; } } "
            "      for (var j2 = 0; j2 < keys.length; j2++) { if (String(keys[j2]).toLowerCase().indexOf(c) !== -1) { return keys[j2]; } } "
            "    } "
            "    return null; "
            "  }; "
            "  for (var i2 = 0; i2 < list.length; i2++) { "
            "    var item = list[i2]; "
            "    if (item == null) { continue; } "
            "    if (typeof item !== 'object') { list[i2] = { __label: item, __value: item, value: item }; continue; } "
            "    if (item.__label == null || item.__value == null) { "
            "      var keys = Object.keys(item); "
            "      var labelKey = pickKey(keys, ['name','title','label','number','code','no','id']); "
            "      var valueKey = pickKey(keys, ['id','code','number','no','name']); "
            "      var labelVal = labelKey ? item[labelKey] : null; "
            "      if (labelVal == null) { try { labelVal = JSON.stringify(item); } catch (e) { labelVal = String(item); } } "
            "      var valueVal = valueKey ? item[valueKey] : labelVal; "
            "      item.__label = labelVal; "
            "      item.__value = valueVal; "
            "    } "
            "  } "
            "  var columns = []; var rows = []; var truncated = false; "
            "  var maxItems = 10; var maxCols = 8; "
            "  if (list.length > 0 && list[0] && typeof list[0] === 'object') { "
            "    var keys2 = Object.keys(list[0]).filter(function(k){ return k && k.indexOf('__') !== 0 && !_isHidden(k); }); "
            "    keys2.sort(); if (keys2.length > maxCols) { keys2 = keys2.slice(0, maxCols); } "
            "    columns = keys2.map(function(k){ return { name: k, label: (labelMap && labelMap[k]) ? labelMap[k] : k, type: 'text' }; }); "
            "    for (var r = 0; r < list.length && r < maxItems; r++) { "
            "      var row = {}; var it = list[r] || {}; "
            "      for (var c2 = 0; c2 < keys2.length; c2++) { "
            "        var k2 = keys2[c2]; var v2 = it[k2]; "
            "        if (v2 == null) { row[k2] = ''; } else if (typeof v2 === 'string' || typeof v2 === 'number' || typeof v2 === 'boolean') { row[k2] = String(v2); } "
            "        else { try { row[k2] = JSON.stringify(v2); } catch (e) { row[k2] = String(v2); } } "
            "        if (row[k2] && row[k2].length > 200) { row[k2] = row[k2].slice(0, 200) + '...'; } "
            "      } "
            "      rows.push(row); "
            "    } "
            "    if (list.length > maxItems) { truncated = true; } "
            "  } "
            "  if (!columns || columns.length === 0) { columns = [{ name: '__label', label: '选项', type: 'text' }]; } "
            "  if (!rows || rows.length === 0) { "
            "    for (var r2 = 0; r2 < list.length && r2 < maxItems; r2++) { "
            "      var it2 = list[r2] || {}; "
            "      var labelVal = (it2 && it2.__label != null) ? it2.__label : ''; "
            "      rows.push({ __label: labelVal }); "
            "    } "
            "    if (list.length > maxItems) { truncated = true; } "
            "  } "
            "  data.__list_items__ = list.slice(0, maxItems); "
            "  data.__list_columns__ = columns; "
            "  data.__list_rows__ = rows; "
            "  data.__list_truncated__ = truncated; "
            "} "
            "return {status: 0, msg: '', data: data};"
        )

    def _guess_item_field_name(self, output_name: str) -> str:
        """
        Guess list item field name from an output name.
        """
        if not output_name:
            return output_name

        candidates: List[str] = []

        def _add(value: Optional[str]) -> None:
            if value and value not in candidates:
                candidates.append(value)

        base = None
        if output_name.startswith("selected_"):
            base = output_name[len("selected_"):]

        if base:
            for suffix in ("_number", "_no", "_id", "_code", "_name"):
                _add(base + suffix)
            _add(base)

        _add(output_name)

        if "_" in output_name:
            _add(output_name.split("_")[-1])

        suffix_aliases = {
            "_id": "id",
            "_code": "code",
            "_number": "number",
            "_no": "no",
            "_name": "name",
            "_type": "type",
            "_status": "status",
            "_price": "price",
            "_amount": "amount",
            "_date": "date",
            "_time": "time",
        }
        for suffix, alias in suffix_aliases.items():
            if output_name.endswith(suffix):
                _add(alias)
                base_alias = output_name[: -len(suffix)]
                _add(base_alias)

        base_token = output_name.split("_")[-1] if "_" in output_name else output_name
        for extra in ("_id", "_code", "_number", "_no", "_name"):
            _add(base_token + extra)

        return candidates[0] if candidates else output_name

    def _build_table_columns(self, array_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        构建表格列定义
        
        从 array 输出的 items 定义中提取列
        """
        columns = []
        
        # 尝试从 items 定义中提取
        items_schema = array_output.get("items", {})
        if isinstance(items_schema, dict):
            properties = items_schema.get("properties", {})
            for field_name, field_def in properties.items():
                columns.append({
                    "name": field_name,
                    "label": field_def.get("description", field_name)
                })
        
        # 如果没有定义，使用默认列
        if not columns:
            columns = [
                {"name": "id", "label": "ID"},
                {"name": "name", "label": "名称"},
                {"name": "status", "label": "状态"}
            ]
        
        return columns
    
    def _build_card_template(self, array_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建卡片模板
        
        从 array 输出的 items 定义中提取字段
        """
        # 尝试从 items 定义中提取字段
        items_schema = array_output.get("items", {})
        fields = []
        
        if isinstance(items_schema, dict):
            properties = items_schema.get("properties", {})
            for field_name, field_def in properties.items():
                fields.append({
                    "name": field_name,
                    "label": field_def.get("description", field_name)
                })
        
        # 构建卡片模板
        if fields:
            body_items = []
            for field in fields[:5]:  # 最多显示 5 个字段
                body_items.append({
                    "type": "tpl",
                    "tpl": f"<p><strong>{field['label']}:</strong> ${{{field['name']}}}</p>"
                })
            
            return {
                "type": "card",
                "header": {
                    "title": "${name}",
                    "subTitle": "${id}"
                },
                "body": body_items
            }
        else:
            # 默认卡片模板
            return {
                "type": "card",
                "header": {
                    "title": "${name}",
                    "subTitle": "${id}"
                },
                "body": [
                    {
                        "type": "tpl",
                        "tpl": "<p><strong>状态:</strong> ${status}</p>"
                    }
                ]
            }
    
    def _build_result_display(self, outputs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        构建结果展示组件
        
        根据 outputs 定义生成展示组件
        """
        result_body = []
        
        # 检查是否有数组类型的输出（表格展示）
        has_array_output = any(o.get("type") == "array" for o in outputs)
        
        if has_array_output:
            array_output = next((o for o in outputs if o.get("type") == "array"), None)
            table_name = array_output.get("name", "items") if array_output else "items"
            
            result_body.append({
                "type": "table",
                "source": f"${{{table_name}}}",
                "columns": [
                    {"name": "id", "label": "ID"},
                    {"name": "name", "label": "名称"},
                    {"name": "status", "label": "状态"}
                ]
            })
        else:
            # 非数组输出，使用模板展示
            for output in outputs:
                result_body.append({
                    "type": "tpl",
                    "tpl": f"<p><strong>{output.get('description', output.get('name'))}:</strong> ${{{output.get('name')}}}</p>"
                })
        
        # 如果没有输出定义，添加默认展示
        if not result_body:
            result_body.append({
                "type": "tpl",
                "tpl": "<p>查询完成</p>"
            })
        
        return result_body
    
    def _build_hidden_fields_for_outputs(
        self,
        outputs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        为 outputs 构建隐藏字段
        
        用于捕获 GET API 返回的数据，传递到下一步
        """
        hidden_fields = []
        for output in outputs:
            output_name = output.get("name", "")
            output_type = output.get("type", "string")
            if output_name and output_type != "array":
                hidden_fields.append({
                    "type": "hidden",
                    "name": output_name
                })
        return hidden_fields

    def _build_field_label_map(
        self,
        outputs: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Build field label mapping for list/table rendering.
        """
        label_map: Dict[str, str] = {
            "total": "总数",
            "page": "页码",
            "limit": "每页数量",
            "has_next": "是否有下一页",
            "has_prev": "是否有上一页"
        }

        for output in outputs:
            if not isinstance(output, dict):
                continue
            name = output.get("name")
            if not name:
                continue
            label = output.get("label") or output.get("description")
            if label:
                label_map[name] = label

        try:
            handler_cfg = config.get("handler_config") if isinstance(config, dict) else None
            entity_name = None
            if isinstance(handler_cfg, dict):
                entity_name = (
                    handler_cfg.get("entity")
                    or handler_cfg.get("entity_name")
                    or handler_cfg.get("entityName")
                )
            if entity_name:
                from app.services.entity_service import entity_service
                label_map.update(entity_service.get_field_label_map(entity_name=entity_name))
            else:
                from app.services.entity_service import entity_service
                label_map.update(entity_service.get_field_label_map())
        except Exception:
            pass

        return label_map

    def _normalize_api_url(self, api_url: str) -> str:
        """Normalize {param} to ${param} for AMIS url variables."""
        if not api_url:
            return api_url
        return re.sub(r'(?<!\$)\{(\w+)\}', r'${\1}', api_url)

    def _resolve_route_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        通过 api_id/endpoint 在路由表中解析真实配置。
        防止工作流节点中的 endpoint 漂移导致页面和执行行为不一致。
        """
        api_id = config.get("api_id") if isinstance(config, dict) else None
        api_endpoint = config.get("api_endpoint") if isinstance(config, dict) else None
        method = (config.get("method") if isinstance(config, dict) else None) or "GET"

        try:
            with get_db_session() as db:
                query = db.query(APIRouteDBModel)
                route = None

                if api_id:
                    route = query.filter(APIRouteDBModel.api_id == api_id).first()

                if route is None and api_endpoint:
                    endpoint = api_endpoint if str(api_endpoint).startswith("/") else f"/{api_endpoint}"
                    route = query.filter(
                        APIRouteDBModel.endpoint == endpoint,
                        APIRouteDBModel.method == method.upper()
                    ).first()

                if route is None:
                    return {}

                return {
                    "endpoint": route.endpoint,
                    "method": route.method,
                }
        except Exception as exc:
            logger.debug(f"ApiCallStrategy 解析路由配置失败: {exc}")
            return {}

    def _detect_media_kind(self, api_url: str, description: str) -> Optional[str]:
        url = (api_url or "").lower()
        desc = (description or "").lower()

        if any(ext in url for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg")):
            return "image"
        if any(ext in url for ext in (".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac")):
            return "audio"
        if ".pdf" in url:
            return "pdf"

        if any(word in desc for word in ("pdf", "政策", "policy", "文件", "document")):
            return "pdf"
        if any(word in desc for word in ("图片", "image", "photo")):
            return "image"
        if any(word in desc for word in ("音频", "audio", "voice")):
            return "audio"

        return None

    def _build_media_preview_url(self, api_url: str, media_kind: str) -> str:
        if not api_url:
            return ""
        if media_kind not in {"pdf", "image", "audio"}:
            return api_url
        if "download=" in api_url:
            return api_url
        connector = "&" if "?" in api_url else "?"
        return f"{api_url}{connector}download=false"

    def _render_media_step_schema(
        self,
        *,
        workflow_id: str,
        workflow: Dict[str, Any],
        node: Dict[str, Any],
        api_url: str,
        media_kind: str,
        slot_values: Optional[Dict[str, Any]],
        request_params: Dict[str, Any],
        form_fields: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        渲染工作流步骤中的媒体预览页（PDF/图片/音频）。
        """
        merged_slots = {
            "page_title": workflow.get("name", "工作流")[:6],
            "user_message": node.get("description", "请查看内容后继续"),
            "next_button_text": "下一步",
        }
        if isinstance(slot_values, dict):
            merged_slots.update(slot_values)

        schema = self.template_loader.render(
            "api_media_view.json.j2",
            api={"description": node.get("description", "")},
            api_url=api_url,
            api_method="GET",
            slot_values=merged_slots,
            api_adaptor="",
            media_direct=True,
            media_kind=media_kind or "file",
            media_url=api_url,
            media_preview_url=self._build_media_preview_url(api_url, media_kind or "file"),
        )

        form_body: List[Dict[str, Any]] = []
        for field in form_fields:
            if isinstance(field, dict) and field.get("type") == "hidden":
                form_body.append(field)

        api_request_payload: Dict[str, Any] = {
            "method": "GET",
            "url": api_url
        }
        if request_params:
            api_request_payload["params"] = request_params

        body = schema.get("body")
        body_list = body if isinstance(body, list) else ([body] if body else [])
        body_list.append(
            {
                "type": "form",
                "api": {
                    "method": "post",
                    "url": "/api/v1/workflow/state",
                    "data": {
                        "workflow_id": workflow_id,
                        "node_id": node.get("id"),
                        "action": "next",
                        "api_request": api_request_payload,
                    }
                },
                "body": form_body,
                "actions": [
                    {
                        "type": "submit",
                        "label": merged_slots.get("next_button_text", "下一步"),
                        "level": "primary"
                    }
                ]
            }
        )

        schema["workflow_id"] = workflow_id
        schema["current_node_id"] = node.get("id")
        schema["body"] = body_list
        return schema

    def _build_api_detail_from_node(
        self,
        node: Dict[str, Any],
        route_endpoint: Optional[str] = None,
        route_method: Optional[str] = None
    ) -> Dict[str, Any]:
        config = node.get("config", {}) or {}
        detail = {}
        api_endpoint = route_endpoint or config.get("api_endpoint")
        method = route_method or config.get("method")
        if api_endpoint:
            detail["path"] = api_endpoint
        if method:
            detail["method"] = method
        if node.get("description"):
            detail["desc"] = node.get("description")
        if config.get("parameters"):
            detail["request"] = config.get("parameters")
        if node.get("outputs"):
            detail["response"] = node.get("outputs")
        return detail
    
    def _build_context_display(
        self,
        context_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        构建上下文信息展示组件
        
        展示已有的上下文数据
        """
        context_items = []
        for key, value in context_data.items():
            if isinstance(value, (str, int, float, bool)):
                label = self._get_field_label(key)
                context_items.append(f"<li><strong>{label}:</strong> {value}</li>")
        
        if not context_items:
            return None
        
        return {
            "type": "tpl",
            "tpl": f"""
            <div class='context-info' style='background:#f5f5f5;padding:10px;border-radius:4px;margin-bottom:10px;'>
                <p style='margin:0 0 5px 0;color:#666;'>已有信息：</p>
                <ul style='margin:0;padding-left:20px;'>
                    {''.join(context_items)}
                </ul>
            </div>
            """
        }
    
    def _get_context_display(
        self,
        node: Dict[str, Any],
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Return whitelisted context for display (default hidden)."""
        config = node.get("config", {}) or {}
        whitelist = config.get("context_fields") or config.get("context_display_fields") or []
        if not isinstance(whitelist, list) or not whitelist:
            return {}
        display_data: Dict[str, Any] = {}
        for key in whitelist:
            if key in context_data and context_data.get(key) is not None:
                display_data[key] = context_data.get(key)
        return display_data

    def _get_field_label(self, field_name: str) -> str:
        """根据字段名生成标签（优先实体元数据，失败则人性化处理）"""
        if not field_name:
            return ""

        # Try entity metadata first (display_name/aliases).
        try:
            from app.services.entity_service import entity_service
            label = entity_service.get_field_label(field_name)
            if label:
                return label
        except Exception:
            pass

        return self._humanize_field_name(field_name)

    def _humanize_field_name(self, field_name: str) -> str:
        if not field_name:
            return ""
        base = field_name.split(".")[-1].strip()
        # If contains CJK, return as-is.
        if any("\u4e00" <= ch <= "\u9fff" for ch in base):
            return base
        base = re.sub(r"[_\\-]+", " ", base).strip()
        if not base:
            return field_name
        # Title-case for readability
        return base.title()
