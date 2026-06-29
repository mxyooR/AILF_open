"""
AI AMIS Service - 纯 LLM 两轮对话架构

核心架构：
- 移除 GNN 图谱编码
- 保留 BGE 召回（扩大 topk: API 15个, Workflow 5个）
- 两轮对话：第一轮选择 API/Workflow，第二轮生成 AMIS

与训练脚本 train_pure_llm_v9.py 和数据集 dataset_v9.jsonl 对应
"""
import logging
import json
import html
from typing import Dict, Any, List, Optional

from app.core.ai.pure_llm_model_service import pure_llm_model_service
from app.core.ai.ego_graph_service import ego_graph_service
from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# 领域名称映射
DOMAIN_NAMES = {
    "medical": "医疗", "finance": "财务", "ecommerce": "电商",
    "train_ticket": "火车票", "logistics": "物流", "hrm": "人力资源",
    "education": "教育", "hotel": "酒店", "banking": "银行",
    "government": "政务", "realestate": "房产", "catering": "餐饮",
    "general": "通用", "railway_ticketing": "火车票"
}


class AIAmisService:
    """
    AI AMIS Schema 生成服务 - 纯 LLM 两轮对话架构
    """
    
    def __init__(self):
        self.model_service = pure_llm_model_service
        self.top_k_api = settings.EGO_GRAPH_TOP_K_API
        self.top_k_workflow = settings.EGO_GRAPH_TOP_K_WORKFLOW

    @staticmethod
    def _sanitize_untrusted_text(text: str, max_len: int = 180) -> str:
        """
        对来自用户输入的不可信文本做显示级净化，防止在 AMIS 文本节点里触发 XSS。
        """
        if text is None:
            return ""
        raw = str(text).strip()
        if len(raw) > max_len:
            raw = raw[:max_len] + "..."
        # 转义 < > & " '，避免被前端当作 HTML 解析
        return html.escape(raw, quote=True)

    async def generate_schema(
        self,
        command: str,
        accessible_apis: Optional[List[Dict[str, Any]]] = None,
        workflows: Optional[List[Dict[str, Any]]] = None,
        current_workflow_node: Optional[Dict[str, Any]] = None,
        current_workflow_id: Optional[str] = None,
        context: Optional[str] = None,
        workflow_context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成 AMIS Schema - V9 纯 LLM 两轮对话架构
        
        推理流程：
        1. BGE 召回候选 API 和 Workflow（扩大 topk）
        2. 第一轮对话：选择 API 或 Workflow
        3. 第二轮对话：根据详情生成 AMIS Schema
        4. 后处理验证和修复
        
        Args:
            command: 用户命令（简单指令，如 "退票政策检查"）
            accessible_apis: 用户可访问的 API 列表
            workflows: 活跃的工作流列表
            current_workflow_node: 当前工作流节点（用于工作流步骤）
            current_workflow_id: 当前工作流 ID
            context: 业务场景上下文
            workflow_context_data: 工作流上下文数据（前序节点输出）
        
        Returns:
            包含 AMIS schema 的结果
        """
        try:
            # 提取用户指令（去除格式化前缀）
            user_instruction = command
            if command.startswith("指令："):
                lines = command.split("\n")
                user_instruction = lines[0].replace("指令：", "").strip()

            # 检查模型是否已加载
            if not self.model_service.is_loaded:
                logger.error("纯LLM模型未加载")
                return {
                    "success": False,
                    "error": "AI 模型未加载",
                    "amis_schema": self._create_error_amis_schema("AI 模型服务尚未初始化，请稍后重试"),
                    "response_text": "AI 服务暂时不可用，请稍后重试。"
                }
            
            logger.info(f"用户指令: {user_instruction}")
            
            # 检测领域
            domain = self._detect_domain(accessible_apis, workflows)
            
            # ========================================
            # 1. BGE 召回候选（扩大 topk）
            # ========================================
            candidate_apis = accessible_apis or []
            candidate_workflows = workflows or []
            
            # 如果 API 数量超过 topk，使用 BGE 召回
            if len(candidate_apis) > self.top_k_api:
                logger.info(f"BGE召回API: {len(candidate_apis)} -> {self.top_k_api}")
                candidate_apis = self._recall_apis(user_instruction, candidate_apis, self.top_k_api)
            
            # 如果 Workflow 数量超过 topk，使用 BGE 召回
            if len(candidate_workflows) > self.top_k_workflow:
                logger.info(f"BGE召回Workflow: {len(candidate_workflows)} -> {self.top_k_workflow}")
                candidate_workflows = self._recall_workflows(user_instruction, candidate_workflows, self.top_k_workflow)
            
            logger.info(f"候选资源: {len(candidate_apis)}个API + {len(candidate_workflows)}个Workflow")
            
            # ========================================
            # 2. 特殊处理：工作流步骤（单轮）
            # ========================================
            if current_workflow_node and current_workflow_id:
                logger.info(f"工作流步骤模式: {current_workflow_id}/{current_workflow_node.get('id')}")
                return await self._generate_workflow_step_schema(
                    user_instruction=user_instruction,
                    workflow_id=current_workflow_id,
                    node=current_workflow_node,
                    workflows=workflows,
                    apis=candidate_apis,
                    domain=domain,
                    workflow_context_data=workflow_context_data
                )
            
            # ========================================
            # 3. 两轮对话生成
            # ========================================
            result = await self.model_service.generate_two_round_async(
                user_instruction=user_instruction,
                candidate_apis=candidate_apis,
                candidate_workflows=candidate_workflows,
                domain=domain,
                validate_endpoints=True
            )
            
            # 处理结果（后端负责最终 Schema 组装，worker 仅负责推理）
            if result.get("valid"):
                schema = result.get("validated_json")
                if not schema:
                    schema = self._build_schema_from_model_result(
                        result=result,
                        user_instruction=user_instruction
                    )

                logger.info("AMIS Schema生成成功")
                if result.get("fixes"):
                    logger.info(f"修复: {result['fixes']}")

                return {
                    "success": True,
                    "amis_schema": schema,
                    "response_text": "已为您生成界面",
                    "selection": result.get("selection"),
                    "fixes": result.get("fixes", []),
                    "raw_output": result.get("raw_output")  # 保留原始输出用于调试
                }

            # JSON 解析失败，返回 raw_output 用于调试
            raw_output = result.get("raw_output", "")
            logger.error(f"生成结果无效: {result.get('fixes', [])}")
            logger.error(f"原始输出(前200字符): {raw_output[:200]}...")

            return {
                "success": False,
                "error": "生成结果解析失败",
                "raw_output": raw_output,  # 返回原始输出用于调试
                "amis_schema": self._create_error_amis_schema(
                    f"AI 生成的内容无法解析为有效的 AMIS Schema\n\n原始输出（前500字符）：\n{raw_output[:500]}"
                ),
                "response_text": "生成界面失败，请重试"
            }
            
        except Exception as e:
            logger.error(f"Schema生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "amis_schema": self._create_error_amis_schema(str(e)),
                "response_text": f"生成界面失败：{str(e)}"
            }

    def _build_schema_from_model_result(
        self,
        result: Dict[str, Any],
        user_instruction: str
    ) -> Dict[str, Any]:
        """使用模型输出的选择结果 + 槽位值，在后端组装最终 AMIS。"""
        selection_detail = result.get("selection_detail", {})
        selection_type = (
            selection_detail.get("type")
            or result.get("selection", {}).get("type")
        )
        selected_item = selection_detail.get("selected_item")
        first_node = selection_detail.get("first_node")
        slot_values = result.get("slot_values") or {}

        if not selection_type or not selected_item:
            raise ValueError("模型未返回可用的选择结果")

        from app.services.amis_schema_generator import amis_schema_generator

        if selection_type == "API":
            return amis_schema_generator.generate_direct_api_form(
                selected_item,
                slot_values=slot_values
            )

        if selection_type == "WORKFLOW":
            if not first_node:
                raise ValueError("工作流首节点缺失，无法生成入口界面")
            return amis_schema_generator.generate_workflow_entry_form(
                workflow=selected_item,
                first_node=first_node,
                user_instruction=user_instruction,
                slot_values=slot_values
            )

        raise ValueError(f"不支持的选择类型: {selection_type}")

    def _recall_apis(self, query: str, apis: List[Dict], top_k: int) -> List[Dict]:
        """使用 BGE 召回 API"""
        try:
            # 构建图谱数据用于 BGE 召回
            nodes = []
            for api in apis:
                nodes.append({
                    'id': api.get('api_id', api.get('id', '')),
                    'type': 'api',
                    'desc': api.get('description', api.get('desc', '')),
                    'path': api.get('endpoint', api.get('path', '')),
                    'method': api.get('method', 'GET'),
                    'name': api.get('name', '')
                })
            
            graph_data = {"nodes": nodes, "edges": []}
            
            # 使用 ego_graph_service 进行召回
            ego_result = ego_graph_service.get_ego_graph(
                full_graph_data=graph_data,
                user_query=query,
                top_k=top_k
            )
            
            # 从召回结果中提取 API
            recalled_ids = {n.get('id') for n in ego_result.get('nodes', [])}
            recalled_apis = [api for api in apis if api.get('api_id', api.get('id', '')) in recalled_ids]
            
            # 如果召回数量不足，补充原始 API
            if len(recalled_apis) < top_k:
                for api in apis:
                    if api not in recalled_apis:
                        recalled_apis.append(api)
                        if len(recalled_apis) >= top_k:
                            break
            
            return recalled_apis[:top_k]
            
        except Exception as e:
            logger.warning(f"BGE召回失败，使用前{top_k}个: {e}")
            return apis[:top_k]
    
    def _recall_workflows(self, query: str, workflows: List[Dict], top_k: int) -> List[Dict]:
        """使用 BGE 召回 Workflow"""
        try:
            nodes = []
            for wf in workflows:
                nodes.append({
                    'id': wf.get('workflow_id', wf.get('id', '')),
                    'type': 'workflow',
                    'desc': wf.get('description', wf.get('desc', '')),
                    'name': wf.get('name', '')
                })
            
            graph_data = {"nodes": nodes, "edges": []}
            
            ego_result = ego_graph_service.get_ego_graph(
                full_graph_data=graph_data,
                user_query=query,
                top_k=top_k
            )
            
            recalled_ids = {n.get('id') for n in ego_result.get('nodes', [])}
            recalled_wfs = [wf for wf in workflows if wf.get('workflow_id', wf.get('id', '')) in recalled_ids]
            
            if len(recalled_wfs) < top_k:
                for wf in workflows:
                    if wf not in recalled_wfs:
                        recalled_wfs.append(wf)
                        if len(recalled_wfs) >= top_k:
                            break
            
            return recalled_wfs[:top_k]
            
        except Exception as e:
            logger.warning(f"BGE召回失败，使用前{top_k}个: {e}")
            return workflows[:top_k]
    
    async def _generate_workflow_step_schema(
        self,
        user_instruction: str,
        workflow_id: str,
        node: Dict[str, Any],
        workflows: List[Dict],
        apis: List[Dict],
        domain: str,
        workflow_context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成工作流步骤的 AMIS Schema（单轮对话 - Slot-Filling 架构）
        
        对应训练数据中的 workflow_step 样本类型
        
        数据集格式（与 dataset_generator_v9.py 完全一致）：
        - System prompt: 包含领域信息、工作流名称和 ID、节点详情、API 详情、上下文数据、槽位列表
        - User input: 简单的指令（如 "正在查询待发货订单"）
        - Assistant output: 槽位值 JSON（不是完整 AMIS Schema）
        """
        try:
            # 查找当前工作流
            current_workflow = None
            for wf in workflows:
                if wf.get('workflow_id') == workflow_id:
                    current_workflow = wf
                    break
            
            if not current_workflow:
                logger.warning(f"未找到工作流: {workflow_id}")
                return self.create_error_response(f"未找到工作流: {workflow_id}", "工作流错误")
            
            workflow_name = current_workflow.get('name', workflow_id)
            
            # 构建节点详情（基础信息）
            node_id = node.get('id', '')
            node_type = node.get('type', 'unknown')
            node_name = node.get('name', '')
            full_node_id = f"{workflow_id}_node_{node_id}"
            
            ai_inst = node.get('ai_instructions', {})
            user_message = ai_inst.get('user_message', '')
            
            node_detail_parts = [
                f"ID: {full_node_id}",
                f"名称: {node_name}",
                f"类型: {node_type}"
            ]
            
            if user_message:
                node_detail_parts.append(f"提示: {user_message}")
            
            node_detail = "\n".join(node_detail_parts)
            
            # 构建 API 详情部分（如果是 api_call 节点）
            api_detail_section = ""
            if node_type == 'api_call':
                config = node.get('config', {})
                api_id = config.get('api_id', '')
                api_endpoint = config.get('api_endpoint', '')
                
                # 查找 API 详情
                api_detail = None
                for api in apis:
                    if (api_id and api.get('api_id') == api_id) or \
                       (api_endpoint and api.get('endpoint') == api_endpoint):
                        api_detail = api
                        break
                
                if api_detail:
                    api_detail_str = self.model_service.build_api_detail(api_detail)
                    api_detail_section = f"\n\n节点API详情：\n{api_detail_str}"
            
            # 构建上下文数据部分
            context_section = ""
            if workflow_context_data:
                context_str = json.dumps(workflow_context_data, ensure_ascii=False, indent=2)
                context_section = f"\n\n上下文数据（前序节点输出）：\n{context_str}"
            
            # 🔥 提取槽位列表（与数据集生成器逻辑一致）
            config = node.get('config', {})
            parameters = config.get('parameters', {})
            context_data = workflow_context_data or {}
            
            # 过滤掉上下文中已有的字段
            fields = [k for k in parameters.keys() if k not in context_data][:5]
            slots = ["page_title", "user_message", "submit_button_text"]
            for field in fields:
                slots.append(f"field_label_{field}")
            if node_type == "api_call":
                slots.extend(["api_url", "api_method"])
            
            # 🔥 构建系统提示词（Slot-Filling 格式，与数据集完全一致）
            domain_cn = DOMAIN_NAMES.get(domain, domain)
            
            system_content = f"""你是{domain_cn}领域的 AMIS 界面生成助手。

当前工作流：{workflow_name}（ID: {workflow_id}）
当前节点：{node_detail}{api_detail_section}{context_section}

任务：为以下槽位生成中文文案（JSON 格式）：
{json.dumps(slots, ensure_ascii=False)}

要求：
- page_title：3-6 字
- user_message：10-20 字
- field_label_xxx：2-4 字
- api_url：完整的 API 路径（如果有路径参数且上下文中有值，直接使用具体值）
- api_method：HTTP 方法（GET/POST/PUT/DELETE）
- 只输出 JSON，不要其他内容"""
            
            # 单轮对话生成槽位值（User input = 简单指令）
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_instruction}  # 简单指令
            ]
            
            logger.info(f"🎯 工作流步骤 Slot-Filling - System prompt长度={len(system_content)}, User input={user_instruction}")
            logger.debug(f"System prompt:\n{system_content}")
            
            # 调用 AI 生成槽位值
            output = self.model_service._generate_single_turn(
                messages,
                max_new_tokens=300,  # 槽位填充只需要很短的输出
                temperature=settings.LLM_TEMPERATURE,
                top_p=settings.LLM_TOP_P
            )
            
            logger.debug(f"AI 槽位输出:\n{output}")
            
            # 解析槽位值 JSON
            slot_values = self.model_service._try_parse_json(output)
            if not slot_values:
                logger.error("❌ 槽位值 JSON 解析失败")
                logger.error(f"原始输出(前200字符): {output[:200]}...")
                
                # 降级到默认槽位值
                slot_values = {
                    "page_title": node_name[:6] if node_name else "操作",
                    "user_message": user_message or "请填写信息",
                    "submit_button_text": "提交"
                }
                for field in fields:
                    slot_values[f"field_label_{field}"] = field
            
            logger.info(f"✅ 槽位值解析成功: {list(slot_values.keys())}")
            
            # 🔥 使用规则生成器生成最终的 AMIS Schema
            from app.services.amis_schema_generator import amis_schema_generator
            
            try:
                amis_schema = amis_schema_generator.generate_workflow_step_form(
                    workflow=current_workflow,
                    node=node,
                    context_data=workflow_context_data,
                    user_instruction=user_instruction,
                    slot_values=slot_values  # 🔥 传递槽位值
                )
                
                logger.info(f"✅ 工作流步骤 AMIS Schema 生成完成")
                
                return {
                    "success": True,
                    "amis_schema": amis_schema,
                    "response_text": "已为您生成界面",
                    "slot_values": slot_values,  # 保留槽位值用于调试
                    "raw_output": output,  # 保留原始输出用于调试
                    "workflow_node": {
                        "id": node.get("id"),
                        "name": node.get("name"),
                        "type": node.get("type")
                    }
                }
                
            except Exception as e:
                logger.error(f"❌ 规则生成器生成 AMIS Schema 失败: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                
                # 降级：返回错误响应
                error_response = self.create_error_response(
                    f"生成界面失败: {str(e)}", 
                    "生成错误"
                )
                error_response["slot_values"] = slot_values
                error_response["raw_output"] = output
                return error_response
            
        except Exception as e:
            logger.error(f"❌ 工作流步骤生成失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self.create_error_response(str(e), "生成错误")

    def _detect_domain(self, apis: List[Dict], workflows: List[Dict]) -> str:
        """检测业务领域"""
        # 从 API 中检测
        if apis:
            for api in apis:
                domain = api.get('domain', api.get('business_scenario', ''))
                if domain and domain != 'common':
                    return domain
        
        # 从 Workflow 中检测
        if workflows:
            for wf in workflows:
                domain = wf.get('business_scenario', wf.get('domain', ''))
                if domain and domain != 'common':
                    return domain
        
        return "general"
    
    def _create_error_amis_schema(self, error_message: str) -> Dict[str, Any]:
        """生成错误提示的 AMIS schema"""
        return {
            "type": "page",
            "body": {
                "type": "alert",
                "level": "danger",
                "title": "生成失败",
                "body": error_message,
                "showIcon": True
            }
        }
    
    def create_error_response(self, error_message: str, title: str = "操作失败") -> Dict[str, Any]:
        """创建标准错误响应"""
        return {
            "success": False,
            "amis_schema": {
                "type": "page",
                "body": {
                    "type": "alert",
                    "level": "danger",
                    "title": title,
                    "body": error_message,
                    "showIcon": True
                }
            },
            "response_text": f"{title}：{error_message}"
        }
    
    def create_complete_response(self, title: str = "操作完成", subtitle: str = "感谢您的使用！") -> Dict[str, Any]:
        """创建工作流完成响应"""
        return {
            "success": True,
            "amis_schema": {
                "type": "page",
                "title": title,
                "body": [
                    {
                        "type": "alert",
                        "level": "success",
                        "title": title,
                        "body": subtitle,
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
            },
            "response_text": f"{title}！"
        }
    
    async def create_login_response(self, original_command: str) -> Dict[str, Any]:
        """创建登录界面响应（统一入口）"""
        return await self.generate_login_schema(original_command)

    async def generate_login_schema(self, original_command: str) -> Dict[str, Any]:
        """生成登录界面 schema（使用固定硬编码 schema）"""
        try:
            safe_original_command = self._sanitize_untrusted_text(original_command)
            logger.info(f"生成登录界面schema, 原始命令={safe_original_command}")

            login_schema = {
                "type": "page",
                "title": "用户登录",
                "body": [
                    {
                        "type": "alert",
                        "level": "info",
                        "body": f"您需要登录后才能处理「{safe_original_command}」这个请求。",
                        "showIcon": True,
                        "className": "mb-4"
                    },
                    {
                        "type": "form",
                        "title": "用户登录",
                        "mode": "horizontal",
                        "api": {
                            "method": "POST",
                            "url": "/api/v1/user/login",
                            "adaptor": "return {...payload, status: payload.code === 200 ? 0 : payload.code, msg: payload.message};",
                            "messages": {
                                "success": "登录成功！正在处理您的需求...",
                                "failed": "登录失败，请检查用户名和密码"
                            }
                        },
                        "messages": {
                            "saveSuccess": "登录成功！正在处理您的需求，请稍候...",
                            "saveFailed": "登录失败，请检查用户名和密码是否正确"
                        },
                        "body": [
                            {
                                "type": "input-text",
                                "name": "username",
                                "label": "用户名",
                                "required": True,
                                "placeholder": "请输入用户名",
                                "className": "mb-3",
                                "size": "lg"
                            },
                            {
                                "type": "input-password",
                                "name": "password",
                                "label": "密码",
                                "required": True,
                                "placeholder": "请输入密码",
                                "className": "mb-3",
                                "size": "lg"
                            }
                        ],
                        "actions": [
                            {
                                "type": "submit",
                                "label": "登录",
                                "level": "primary",
                                "size": "lg",
                                "className": "me-2"
                            },
                            await self._generate_dynamic_register_button()
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "alert",
                        "level": "warning",
                        "body": "如果您还没有账号，可以点击上方的\"注册账号\"按钮进行注册。",
                        "showIcon": True
                    }
                ]
            }

            return {
                "success": True,
                "amis_schema": login_schema,
                "response_text": f"请先登录后再处理「{safe_original_command}」"
            }

        except Exception as e:
            logger.error(f"生成登录schema失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "amis_schema": self._create_error_amis_schema(f"生成登录界面失败: {str(e)}"),
                "response_text": f"生成登录界面失败: {str(e)}"
            }

    async def _generate_dynamic_register_button(self) -> Dict[str, Any]:
        """动态生成注册按钮，使用注册配置API获取字段"""
        try:
            logger.info("开始生成动态注册按钮")
            from app.core.database import get_db_session
            from app.models.role import RoleDBModel
            from app.config import settings
            from app.services.entity_service import EntityService

            logger.debug("导入完成，开始查询数据库")
            with get_db_session() as db:
                logger.debug("数据库会话已创建")
                logger.debug(f"查询默认角色: {settings.DEFAULT_REGISTER_ROLE_CODE}")
                default_role = db.query(RoleDBModel).filter(
                    RoleDBModel.code == settings.DEFAULT_REGISTER_ROLE_CODE,
                    RoleDBModel.status == "active"
                ).first()

                if not default_role:
                    logger.warning(f"未找到默认角色: {settings.DEFAULT_REGISTER_ROLE_CODE}")
                    return self._get_fallback_register_button()

                logger.debug(f"找到默认角色: {default_role.name}")

                logger.debug(f"获取实体字段: {default_role.code}")
                entity_service = EntityService()
                entity_result = entity_service.get_entity_by_name(default_role.code)
                logger.debug(f"实体字段获取完成: {entity_result.get('success')}")

                register_fields = []

                # 基础认证字段
                register_fields.extend([
                    {
                        "type": "input-text",
                        "name": "username",
                        "label": "用户名",
                        "required": True,
                        "placeholder": "请输入用户名",
                        "validations": {"minLength": 3, "maxLength": 20}
                    },
                    {
                        "type": "input-password",
                        "name": "password",
                        "label": "密码",
                        "required": True,
                        "placeholder": "请输入密码",
                        "validations": {"minLength": 6}
                    },
                    {
                        "type": "input-password",
                        "name": "confirm_password",
                        "label": "确认密码",
                        "required": True,
                        "placeholder": "请再次输入密码",
                        "validations": {"equalsField": "password"}
                    }
                ])

                # 添加角色实体字段
                if entity_result.get("success") and entity_result.get("data"):
                    entity_data = entity_result["data"]["entity"]
                    if hasattr(entity_data, 'fields') and entity_data.fields:
                        logger.debug(f"为注册表单添加{len(entity_data.fields)}个角色实体字段")
                        for field in entity_data.fields:
                            if field.name not in ["id", "created_at", "updated_at", "user_id"]:
                                field_config = self._convert_entity_field_to_register_field(field)
                                if field_config:
                                    register_fields.append(field_config)

                return {
                    "type": "button",
                    "label": "注册账号",
                    "level": "link",
                    "size": "lg",
                    "actionType": "dialog",
                    "dialog": {
                        "title": "用户注册",
                        "size": "md",
                        "body": {
                            "type": "form",
                            "api": {
                                "method": "POST",
                                "url": "/api/v1/user/register",
                                "adaptor": "return {...payload, status: payload.code === 200 ? 0 : payload.code, msg: payload.message};",
                                "messages": {
                                    "success": "注册成功！请登录",
                                    "failed": "注册失败，请检查输入信息"
                                }
                            },
                            "messages": {
                                "saveSuccess": "注册成功！请使用新账号登录",
                                "saveFailed": "注册失败，请检查输入信息是否正确"
                            },
                            "body": register_fields
                        }
                    }
                }

        except Exception as e:
            logger.error(f"生成动态注册按钮失败: {str(e)}")
            return self._get_fallback_register_button()

    def _convert_entity_field_to_register_field(self, field) -> Dict[str, Any]:
        """将实体字段转换为注册表单字段"""
        try:
            field_name = field.name
            field_type = field.type.value if hasattr(field.type, 'value') else str(field.type)
            display_name = field.displayName
            required = field.required

            form_field = {
                "name": field_name,
                "label": display_name,
                "required": required,
                "placeholder": f"请输入{display_name}" + ("" if required else "（可选）")
            }

            if field_type.lower() in ["select", "enum"]:
                form_field["type"] = "select"
                form_field["placeholder"] = f"请选择{display_name}"
                if hasattr(field, 'options') and field.options:
                    form_field["options"] = [{"label": opt, "value": opt} for opt in field.options]
            elif field_type.lower() in ["phone", "mobile"]:
                form_field["type"] = "input-text"
                form_field["validations"] = {"matchRegexp": "^1[3-9]\\d{9}$"}
                form_field["validationErrors"] = {"matchRegexp": "请输入有效的手机号码"}
            elif field_type.lower() == "email":
                form_field["type"] = "input-email"
            elif field_type.lower() in ["textarea", "longtext"]:
                form_field["type"] = "textarea"
            elif field_type.lower() == "number":
                form_field["type"] = "input-number"
            elif field_type.lower() == "date":
                form_field["type"] = "input-date"
            else:
                form_field["type"] = "input-text"

            logger.debug(f"转换注册字段: {field_name} ({field_type}) -> {form_field['type']}")
            return form_field

        except Exception as e:
            logger.error(f"转换注册字段失败: {str(e)}")
            return {}

    def _get_fallback_register_button(self) -> Dict[str, Any]:
        """获取备用注册按钮（硬编码版本）"""
        return {
            "type": "button",
            "label": "注册账号",
            "level": "link",
            "size": "lg",
            "actionType": "dialog",
            "dialog": {
                "title": "用户注册",
                "size": "md",
                "body": {
                    "type": "form",
                    "api": {
                        "method": "POST",
                        "url": "/api/v1/user/register",
                        "adaptor": "return {...payload, status: payload.code === 200 ? 0 : payload.code, msg: payload.message};",
                        "messages": {
                            "success": "注册成功！请登录",
                            "failed": "注册失败，请检查输入信息"
                        }
                    },
                    "messages": {
                        "saveSuccess": "注册成功！请使用新账号登录",
                        "saveFailed": "注册失败，请检查输入信息是否正确"
                    },
                    "body": [
                        {
                            "type": "input-text",
                            "name": "username",
                            "label": "用户名",
                            "required": True,
                            "placeholder": "请输入用户名",
                            "validations": {"minLength": 3, "maxLength": 20}
                        },
                        {
                            "type": "input-email",
                            "name": "email",
                            "label": "邮箱",
                            "required": True,
                            "placeholder": "请输入邮箱地址"
                        },
                        {
                            "type": "input-password",
                            "name": "password",
                            "label": "密码",
                            "required": True,
                            "placeholder": "请输入密码",
                            "validations": {"minLength": 6}
                        },
                        {
                            "type": "input-password",
                            "name": "confirm_password",
                            "label": "确认密码",
                            "required": True,
                            "placeholder": "请再次输入密码",
                            "validations": {"equalsField": "password"}
                        }
                    ]
                }
            }
        }

    def _field_to_amis_input(self, field: Dict[str, Any]) -> Dict[str, Any]:
        """将字段定义转换为 AMIS 输入组件"""
        try:
            field_type = field.get("type", "string")
            field_name = field.get("name", "")
            field_label = field.get("label", field_name)
            required = field.get("required", False)

            if not field_name:
                return {}

            amis_input = {
                "name": field_name,
                "label": field_label,
                "required": required
            }

            if field_type in ["string", "str", "text"]:
                amis_input["type"] = "input-text"
                amis_input["placeholder"] = f"请输入{field_label}"
                amis_input["clearable"] = True
            elif field_type in ["integer", "int"]:
                amis_input["type"] = "input-number"
                amis_input["placeholder"] = f"请输入{field_label}"
                amis_input["min"] = 0
            elif field_type in ["number", "float"]:
                amis_input["type"] = "input-number"
                amis_input["precision"] = 2
                amis_input["placeholder"] = f"请输入{field_label}"
            elif field_type == "date":
                amis_input["type"] = "input-date"
                amis_input["format"] = "YYYY-MM-DD"
                amis_input["placeholder"] = "请选择日期"
                amis_input["clearable"] = True
            elif field_type == "time":
                amis_input["type"] = "input-time"
                amis_input["format"] = "HH:mm:ss"
                amis_input["placeholder"] = "请选择时间"
            elif field_type == "datetime":
                amis_input["type"] = "input-datetime"
                amis_input["format"] = "YYYY-MM-DD HH:mm:ss"
                amis_input["placeholder"] = "请选择日期时间"
            elif field_type in ["boolean", "bool"]:
                amis_input["type"] = "switch"
                amis_input["onText"] = "是"
                amis_input["offText"] = "否"
            elif field_type == "select":
                amis_input["type"] = "select"
                options = field.get("options", [])
                if isinstance(options, list) and len(options) > 0:
                    if isinstance(options[0], str):
                        amis_input["options"] = [{"label": opt, "value": opt} for opt in options]
                    else:
                        amis_input["options"] = options
                else:
                    amis_input["options"] = []
                amis_input["placeholder"] = f"请选择{field_label}"
                amis_input["clearable"] = True
            elif field_type == "textarea":
                amis_input["type"] = "textarea"
                amis_input["minRows"] = 3
                amis_input["placeholder"] = f"请输入{field_label}"
            elif field_type == "email":
                amis_input["type"] = "input-email"
                amis_input["placeholder"] = f"请输入{field_label}"
            elif field_type == "phone":
                amis_input["type"] = "input-text"
                amis_input["placeholder"] = f"请输入{field_label}"
                amis_input["validations"] = {"isPhoneNumber": True}
            elif field_type == "file":
                amis_input["type"] = "input-file"
                amis_input["accept"] = "image/*,.pdf,.doc,.docx"
            elif field_type == "array":
                amis_input["type"] = "combo"
                amis_input["multiple"] = True
                amis_input["addButtonText"] = f"添加{field_label}"
                amis_input["items"] = [{"type": "input-text", "name": "value", "placeholder": f"请输入{field_label}"}]
            else:
                amis_input["type"] = "input-text"
                amis_input["placeholder"] = f"请输入{field_label}"
                amis_input["clearable"] = True

            return amis_input

        except Exception as e:
            logger.warning(f"转换字段失败: {field}, 错误={str(e)}")
            return {}


# 全局实例
ai_amis_service = AIAmisService()
