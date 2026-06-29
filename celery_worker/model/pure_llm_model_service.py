"""
纯 LLM 模型服务 (Pure LLM Model Service) - V9 两轮对话架构

核心架构：
- 移除 GNN 图谱编码
- 保留 BGE 召回（扩大 topk）
- 两轮对话：第一轮选择 API/Workflow，第二轮生成 AMIS

与训练脚本 train_pure_llm_v9.py 对应
"""
import os
import json
import logging
import asyncio
import threading
import torch
from typing import Optional, List, Dict, Set, Tuple, Any
from difflib import SequenceMatcher

from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

from celery_worker.config import settings
from celery_worker.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# 1. 端点验证器 (后处理)
# ============================================================================

class EndpointValidator:
    """
    端点验证器 - 后处理检查和修复无效的 API URL、Method
    """
    
    def __init__(self, graph_nodes: List[Dict]):
        self.valid_paths: Set[str] = set()
        self.path_to_method: Dict[str, str] = {}
        self.endpoint_info: Dict[str, Dict] = {}
        
        for node in graph_nodes:
            if node.get('type') == 'api' and 'path' in node:
                path = node['path']
                method = node.get('method', 'GET').upper()
                self.valid_paths.add(path)
                self.path_to_method[path] = method
                self.endpoint_info[path] = {
                    'method': method,
                    'request': node.get('request', [])
                }

        # 添加固定的系统端点
        self.valid_paths.add('/api/v1/workflow/state')
        self.valid_paths.add('/api/v1/command')
        self.path_to_method['/api/v1/workflow/state'] = 'POST'
        self.path_to_method['/api/v1/command'] = 'POST'
        self.endpoint_info['/api/v1/workflow/state'] = {
            'method': 'POST', 
            'request': [{'name': 'workflow_id'}, {'name': 'node_id'}, {'name': 'action'}]
        }
        self.endpoint_info['/api/v1/command'] = {'method': 'POST', 'request': []}
        
        logger.debug(f"EndpointValidator初始化: {len(self.valid_paths)}个有效端点")
    
    def find_best_match(self, url: str) -> Optional[str]:
        if url in self.valid_paths:
            return url
        
        best_match, best_score = None, 0.0
        for valid_path in self.valid_paths:
            score = SequenceMatcher(None, url.lower(), valid_path.lower()).ratio()
            if score > best_score:
                best_score, best_match = score, valid_path
        
        return best_match if best_score >= 0.3 else None
    
    def fix_urls_in_json(self, schema: Dict, user_input: str = "") -> Tuple[Dict, List[str]]:
        """修复 JSON 中的无效 URL 和 Method"""
        fixes = []
        
        def fix_api_config(obj: Dict):
            url = obj.get('url', '')
            if url.startswith('${'):
                return
            
            if url and url not in self.valid_paths:
                match = self.find_best_match(url)
                if match:
                    fixes.append(f"URL: '{url}' -> '{match}'")
                    obj['url'] = match
                    url = match
            
            if url in self.path_to_method:
                correct_method = self.path_to_method[url]
                current_method = obj.get('method', 'GET').upper()
                if current_method != correct_method:
                    fixes.append(f"Method: '{current_method}' -> '{correct_method}' for {url}")
                    obj['method'] = correct_method.lower()
        
        def fix(obj):
            if isinstance(obj, dict):
                # 修复无效的 AMIS 组件类型
                if 'type' in obj:
                    obj_type = obj['type']
                    if obj_type == 'input-select':
                        fixes.append(f"组件类型: 'input-select' -> 'select'")
                        obj['type'] = 'select'
                    elif obj_type == 'input-radio':
                        fixes.append(f"组件类型: 'input-radio' -> 'radios'")
                        obj['type'] = 'radios'
                    elif obj_type == 'input-checkbox':
                        fixes.append(f"组件类型: 'input-checkbox' -> 'checkboxes'")
                        obj['type'] = 'checkboxes'
                
                if 'api' in obj and isinstance(obj['api'], dict):
                    fix_api_config(obj['api'])
                
                if 'url' in obj and isinstance(obj['url'], str):
                    if not obj['url'].startswith('${'):
                        url = obj['url']
                        if url not in self.valid_paths:
                            match = self.find_best_match(url)
                            if match:
                                fixes.append(f"URL: '{url}' -> '{match}'")
                                obj['url'] = match
                
                for v in obj.values():
                    fix(v)
            elif isinstance(obj, list):
                for item in obj:
                    fix(item)
        
        fix(schema)
        return schema, fixes


# ============================================================================
# 2. 纯 LLM 模型服务 (单例)
# ============================================================================

class PureLLMModelService:
    """
    纯 LLM 模型服务 - V9 两轮对话架构
    
    功能：
    1. 全局加载且仅加载一次模型（Base LLM + LoRA）
    2. 移除 GNN 编码，使用纯文本候选列表
    3. 两轮对话：选择 + 生成
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PureLLMModelService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if PureLLMModelService._initialized:
            return
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.llm = None
        self.base_model = None
        self.llm_dtype = torch.bfloat16
        
        # 生成参数
        self.max_length = 2048  # tokenizer 最大长度
        self.max_new_tokens = 512  # 默认生成 token 数
        self.temperature = 0.7
        self.top_p = 0.9
        
        self._is_loaded = False
        self._loading = False
        self._generate_lock = threading.Lock()
        
        logger.info("PureLLMModelService单例创建(懒加载模式)")
        PureLLMModelService._initialized = True
    
    @property
    def is_loaded(self) -> bool:
        return self._is_loaded
    
    def load_model(
        self,
        base_model_path: str = None,
        lora_checkpoint_path: str = None,
        use_4bit: bool = True
    ):
        """加载模型（Base LLM + LoRA）"""
        if self._is_loaded:
            logger.info("模型已加载，跳过重复加载")
            return
        
        if self._loading:
            logger.info("模型正在加载中...")
            import time
            while self._loading:
                time.sleep(0.5)
            return
        
        self._loading = True
        
        try:
            if base_model_path is None:
                base_model_path = settings.LOCAL_MODEL_BASE_PATH
            if lora_checkpoint_path is None:
                lora_checkpoint_path = settings.LOCAL_MODEL_LORA_PATH
            
            logger.info("=" * 70)
            logger.info("开始加载纯LLM模型 (V9两轮对话架构)")
            logger.info("=" * 70)
            logger.info(f"使用设备: {self.device}")
            logger.info(f"基础模型: {base_model_path}")
            logger.info(f"LoRA权重: {lora_checkpoint_path}")
            
            # 1. 加载 Tokenizer
            logger.info("[1/3] 加载Tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                base_model_path,
                trust_remote_code=True
            )
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            logger.info("Tokenizer加载完成")
            
            # 2. 加载基础 LLM
            logger.info("[2/3] 加载基础LLM (4-bit量化)...")
            if use_4bit:
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.bfloat16
                )
            else:
                bnb_config = None
            
            self.base_model = AutoModelForCausalLM.from_pretrained(
                base_model_path,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
                torch_dtype=torch.bfloat16 if use_4bit else torch.float16,
                local_files_only=True
            )
            logger.info("基础LLM加载完成")
            
            # 3. 加载 LoRA 权重
            logger.info(f"[3/3] 加载LoRA权重: {lora_checkpoint_path}")
            self.llm = PeftModel.from_pretrained(
                self.base_model,
                lora_checkpoint_path
            )
            self.llm.eval()
            logger.info("LoRA权重加载完成")
            
            self.llm_dtype = torch.bfloat16 if use_4bit else torch.float16
            self._is_loaded = True
            
            logger.info("=" * 70)
            logger.info("纯LLM模型加载完成")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            self._loading = False

    def build_candidate_list(
        self,
        apis: List[Dict[str, Any]],
        workflows: List[Dict[str, Any]],
        domain: str = "general"
    ) -> str:
        """
        构建候选列表文本（与新数据集格式一致）
        
        格式：
        [API] GET /api/xxx - 描述
        [WORKFLOW] workflow_id - 名称
        """
        lines = []
        
        # API 列表
        for api in apis:
            method = api.get('method', 'GET').upper()
            path = api.get('endpoint', api.get('path', ''))
            desc = api.get('description', api.get('desc', ''))
            if path:
                is_workflow_only = api.get("workflow_only", False) and self._find_workflow_for_api(api, workflows)
                tag = "（仅工作流）" if is_workflow_only else ""
                lines.append(f"[API] {method} {path} - {desc}{tag}")
        
        # 工作流列表（与数据集格式一致：显示 ID）
        for wf in workflows:
            wf_id = wf.get('workflow_id', wf.get('id', ''))
            wf_name = wf.get('name', '')
            if wf_name and wf_id:
                lines.append(f"[WORKFLOW] {wf_id} - {wf_name}")
            elif wf_name:
                lines.append(f"[WORKFLOW] {wf_name}")
        
        return "\n".join(lines)
    
    def _build_api_detail_dict(
        self,
        api: Dict[str, Any],
        include_id: bool = True,
        include_response: bool = True,
        include_label: bool = True,
        include_required: bool = True
    ) -> Dict[str, Any]:
        detail = {}
        if include_id:
            api_id = api.get('api_id', api.get('id', ''))
            if api_id:
                detail["id"] = api_id
        path = api.get('endpoint', api.get('path', ''))
        method = api.get('method', 'GET')
        desc = api.get('description', api.get('desc', ''))
        if path:
            detail["path"] = path
        if method:
            detail["method"] = method.upper()
        if desc:
            detail["desc"] = desc

        request = []
        for param in api.get('parameters', api.get('request', [])):
            item = {
                'name': param.get('name', ''),
                'type': param.get('type', 'string')
            }
            label = param.get('description', param.get('label'))
            if include_label and label:
                item['label'] = label
            if include_required and param.get("required") is not None:
                item['required'] = param.get('required', False)
            request.append(item)
        if request:
            detail['request'] = request

        if include_response:
            response = []
            for resp in api.get('response', []):
                item = {
                    'name': resp.get('name', ''),
                    'type': resp.get('type', 'string')
                }
                resp_desc = resp.get('description', resp.get('desc', ''))
                if resp_desc:
                    item['desc'] = resp_desc
                response.append(item)
            if response:
                detail['response'] = response

        return detail

    def build_api_detail(
        self,
        api: Dict[str, Any],
        include_id: bool = True,
        include_response: bool = True,
        include_label: bool = True,
        include_required: bool = True
    ) -> str:
        """
        构建 API 详情文本（与训练数据格式一致）
        """
        detail = self._build_api_detail_dict(
            api,
            include_id=include_id,
            include_response=include_response,
            include_label=include_label,
            include_required=include_required
        )
        return json.dumps(detail, ensure_ascii=False, indent=2)

    def build_workflow_detail(
        self, 
        workflow: Dict[str, Any],
        first_node: Dict[str, Any] = None,
        api_details: Dict[str, Any] = None
    ) -> str:
        """
        构建工作流详情文本（与训练数据集格式完全一致）
        
        数据集格式：
        {
          "id": "workflow_id",
          "name": "工作流名称",
          "desc": "描述",
          "node_chain": "节点1 → 节点2 → ...",
          "first_node": {
            "id": "workflow_id_node_xxx",
            "name": "节点名称",
            "type": "api_call",
            "ai_instructions": {...},
            "api": {...}
          }
        }
        """
        workflow_id = workflow.get('workflow_id', workflow.get('id', ''))
        nodes = workflow.get('nodes', [])
        
        # 过滤掉 start/end 节点
        valid_nodes = [n for n in nodes if n.get("type") not in ("start", "end")]
        
        # 构建节点链（最多显示5个节点）
        node_names = [n.get('name', n.get('id', '')) for n in valid_nodes[:5]]
        node_chain = " → ".join(node_names)
        if len(valid_nodes) > 5:
            node_chain += " → ..."
        
        # 构建工作流详情
        detail = {
            "id": workflow_id,
            "name": workflow.get('name', ''),
            "desc": workflow.get('description', workflow.get('desc', '')),
            "node_chain": node_chain
        }
        
        # 添加第一个节点信息（如果提供）
        if first_node:
            first_node_id = first_node.get('id', '')
            full_first_node_id = first_node_id
            if workflow_id and first_node_id and not first_node_id.startswith(f"{workflow_id}_node_"):
                full_first_node_id = f"{workflow_id}_node_{first_node_id}"
            
            first_node_detail = {
                "id": full_first_node_id,
                "name": first_node.get('name', ''),
                "type": first_node.get('type', ''),
                "ai_instructions": first_node.get('ai_instructions', {})
            }
            
            # 如果有 API 详情，添加到 first_node 中
            if api_details:
                if any(k in api_details for k in ("endpoint", "parameters", "description", "api_id", "response")):
                    first_node_detail["api"] = self._build_api_detail_dict(
                        api_details,
                        include_id=True,
                        include_response=True,
                        include_label=True,
                        include_required=True
                    )
                else:
                    first_node_detail["api"] = api_details
            
            detail["first_node"] = first_node_detail
        
        return json.dumps(detail, ensure_ascii=False, indent=2)


    def _build_intent_system_prompt(self, candidate_list: str, domain: str) -> str:
        domain_cn = self._get_domain_cn(domain)
        header = ""
        if domain_cn and domain != "general":
            header = f"你是{domain_cn}领域的 AMIS 界面生成助手。\n\n"
        return f"""{header}可用资源：
{candidate_list}

任务：根据用户指令选择合适的 API 或工作流。
- 如果匹配到 API，输出：API: <API描述>
- 如果匹配到工作流，输出：WORKFLOW: <工作流名称>
- 如果用户在询问你是谁 / 你能做什么 / 你现在能帮我干啥 / 帮助，输出：HELP
- 如果无法匹配，输出：REJECT"""

    @torch.no_grad()
    def identify_intent(
        self,
        user_instruction: str,
        candidate_apis: List[Dict[str, Any]],
        candidate_workflows: List[Dict[str, Any]],
        domain: str = "general",
        max_new_tokens: int = 100,
        temperature: float = None,
        top_p: float = None,
        do_sample: bool = True
    ) -> Dict:
        """
        意图识别（只做第一轮对话）
        
        新架构：AI 只做意图识别，AMIS Schema 由规则生成
        
        Args:
            user_instruction: 用户指令
            candidate_apis: 候选 API 列表（BGE 召回结果）
            candidate_workflows: 候选工作流列表（BGE 召回结果）
            domain: 业务领域
            max_new_tokens: 最大生成 token 数（意图识别只需要很短）
            temperature: 温度参数
            top_p: Top-p 采样参数
            do_sample: 是否采样
        
        Returns:
            {
                "type": "WORKFLOW" | "API" | "REJECT",
                "target": "退票流程" | "查询订单" | None,
                "id": "workflow_refund_ticket" | "api_query_order" | None,
                "available_actions": [...] (仅 REJECT 时)
            }
        """
        if not self._is_loaded:
            raise RuntimeError("模型未加载！请先调用 load_model() 方法")
        
        if not self._generate_lock.acquire(timeout=120):
            raise RuntimeError("模型正忙，请稍后重试")
        
        try:
            return self._identify_intent_internal(
                user_instruction=user_instruction,
                candidate_apis=candidate_apis,
                candidate_workflows=candidate_workflows,
                domain=domain,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample
            )
        finally:
            self._generate_lock.release()
    
    def _identify_intent_internal(
        self,
        user_instruction: str,
        candidate_apis: List[Dict[str, Any]],
        candidate_workflows: List[Dict[str, Any]],
        domain: str = "general",
        max_new_tokens: int = None,
        temperature: float = None,
        top_p: float = None,
        do_sample: bool = True
    ) -> Dict:
        """内部意图识别方法"""
        if max_new_tokens is None:
            max_new_tokens = 100  # 意图识别只需要很短的输出
        if temperature is None:
            temperature = settings.LLM_TEMPERATURE
        if top_p is None:
            top_p = settings.LLM_TOP_P
        
        # 获取领域中文名
        
        # 构建候选列表
        candidate_list = self.build_candidate_list(candidate_apis, candidate_workflows, domain)
        
        # System Prompt（只做意图识别）
        system_prompt = self._build_intent_system_prompt(candidate_list, domain)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_instruction}
        ]
        
        logger.info("🤖 AI 意图识别（第一轮对话）")
        logger.info(f"📋 System Prompt:\n{system_prompt}")
        
        # 生成
        output = self._generate_single_turn(
            messages,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample
        )
        
        logger.info(f"🤖 AI 识别结果: {output}")
        
        # 解析结果
        selection_type, selection_name = self._parse_selection(output)
        
        result = {
            "type": selection_type or "REJECT",
            "target": selection_name,
            "id": None,
            "available_actions": []
        }

        if selection_type == "HELP":
            result["type"] = "HELP"
            return result
        
        # 查找匹配的资源并获取 ID
        if selection_type == "API" and selection_name:
            matched_api = self._find_api_by_name(selection_name, candidate_apis)
            if matched_api:
                logger.debug(
                    f"✅ 匹配到 API: {matched_api.get('endpoint', matched_api.get('path', ''))} - "
                    f"{matched_api.get('description', matched_api.get('desc', ''))}"
                )
                if matched_api.get("workflow_only"):
                    mapped_workflow = self._find_workflow_for_api(matched_api, candidate_workflows)
                    if mapped_workflow:
                        result["type"] = "WORKFLOW"
                        result["target"] = mapped_workflow.get("name", "")
                        result["id"] = mapped_workflow.get('workflow_id', mapped_workflow.get('id', ''))
                        result["matched_resource"] = mapped_workflow
                        return result
                result["id"] = matched_api.get('api_id', matched_api.get('id', ''))
                result["matched_resource"] = matched_api
            else:
                logger.warning(f"⚠️ 未找到匹配的 API: {selection_name}")
                result["type"] = "REJECT"
        
        elif selection_type == "WORKFLOW" and selection_name:
            matched_workflow = self._find_workflow_by_name(selection_name, candidate_workflows)
            if matched_workflow:
                result["id"] = matched_workflow.get('workflow_id', matched_workflow.get('id', ''))
                result["matched_resource"] = matched_workflow
            else:
                logger.warning(f"⚠️ 未找到匹配的 Workflow: {selection_name}")
                result["type"] = "REJECT"
        
        # 如果是拒绝，提供可用操作列表
        if result["type"] == "REJECT":
            available_actions = []
            for wf in candidate_workflows[:5]:
                available_actions.append(wf.get('name', ''))
            for api in candidate_apis[:5]:
                available_actions.append(api.get('description', api.get('desc', '')))
            result["available_actions"] = available_actions
        
        return result
    
    def _generate_two_round_internal(
        self,
        user_instruction: str,
        candidate_apis: List[Dict[str, Any]],
        candidate_workflows: List[Dict[str, Any]],
        domain: str = "general",
        max_new_tokens: int = None,
        temperature: float = None,
        top_p: float = None,
        do_sample: bool = True,
        validate_endpoints: bool = True
    ) -> Dict:
        """内部两轮对话生成方法"""
        if max_new_tokens is None:
            max_new_tokens = settings.LLM_MAX_NEW_TOKENS
        if temperature is None:
            temperature = settings.LLM_TEMPERATURE
        if top_p is None:
            top_p = settings.LLM_TOP_P
        
        # 获取领域中文名
        
        # ========================================
        # 第一轮：选择 API 或 Workflow
        # ========================================
        candidate_list = self.build_candidate_list(candidate_apis, candidate_workflows, domain)
        
        system_prompt_round1 = self._build_intent_system_prompt(candidate_list, domain)
        
        messages_round1 = [
            {"role": "system", "content": system_prompt_round1},
            {"role": "user", "content": user_instruction}
        ]
        
        logger.info("🤖 第一轮对话: 选择API/Workflow")
        logger.info(f"📋 System Prompt (第一轮):\n{system_prompt_round1}")
        
        selection_output = self._generate_single_turn(
            messages_round1,
            max_new_tokens=100,  # 选择只需要很短的输出
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample
        )
        
        logger.info(f"🤖 第一轮选择: {selection_output}")
        
        # 解析选择结果
        selection_type, selection_name = self._parse_selection(selection_output)
        
        result = {
            "raw_output": selection_output,
            "parsed_json": None,
            "validated_json": None,
            "fixes": [],
            "valid": False,
            "selection": {"type": selection_type, "name": selection_name}
        }

        if selection_type == "HELP":
            result["validated_json"] = {
                "type": "page",
                "title": "功能说明",
                "body": {
                    "type": "alert",
                    "level": "info",
                    "body": "已进入帮助模式，请查看当前场景的功能说明。",
                    "showIcon": True
                }
            }
            result["valid"] = True
            return result
        
        # 🔥 如果是拒绝，直接生成拒绝 AMIS Schema（Slot-Filling 架构）
        if selection_type == "REJECT":
            logger.info("🤖 AI 输出 REJECT，后端直接生成拒绝 Schema")
            # 提取可用操作列表
            available_actions = []
            for wf in candidate_workflows[:5]:
                available_actions.append(wf.get('name', wf.get('workflow_id', '')))
            for api in candidate_apis[:5]:
                available_actions.append(api.get('description', api.get('desc', '')))
            
            # 后端直接生成拒绝 AMIS Schema
            result["validated_json"] = self._create_rejection_schema(
                user_instruction, 
                available_actions=available_actions
            )
            result["valid"] = True
            return result
        
        # 如果无法解析选择，尝试直接解析 JSON（兼容旧格式）
        if selection_type is None:
            logger.warning("⚠️ 无法解析选择，尝试直接解析 JSON")
            parsed = self._try_parse_json(selection_output)
            if parsed:
                result["parsed_json"] = parsed
                result["validated_json"] = parsed
                result["valid"] = True
                return result
            else:
                # 生成默认拒绝响应
                result["validated_json"] = self._create_rejection_schema(user_instruction)
                result["valid"] = True
                return result

        # ========================================
        # 第二轮：根据详情生成 AMIS
        # ========================================
        logger.info(f"🤖 第一轮选择结果: {selection_type} - {selection_name}")
        
        detail_text = ""
        selected_item = None
        
        if selection_type == "API":
            # 查找选中的 API
            selected_item = self._find_api_by_name(selection_name, candidate_apis)
            if selected_item:
                if selected_item.get("workflow_only"):
                    mapped_workflow = self._find_workflow_for_api(selected_item, candidate_workflows)
                    if mapped_workflow:
                        selection_type = "WORKFLOW"
                        selection_name = mapped_workflow.get("name", "")
                        selected_item = mapped_workflow
                    else:
                        logger.warning("⚠️ 选中的 API 为工作流专用，但未找到对应工作流")
                        result["validated_json"] = self._create_rejection_schema(user_instruction)
                        result["valid"] = True
                        return result
                detail_text = f"API详情:\n{self.build_api_detail(selected_item)}"
            else:
                logger.warning(f"⚠️ 未找到选中的API: {selection_name}")
                result["validated_json"] = self._create_rejection_schema(user_instruction)
                result["valid"] = True
                return result
        
        elif selection_type == "WORKFLOW":
            # 查找选中的 Workflow
            selected_item = self._find_workflow_by_name(selection_name, candidate_workflows)
            if selected_item:
                # 获取第一个业务节点（start 节点之后的第一个节点）
                nodes = selected_item.get('nodes', [])
                first_node = None
                api_details = None
                
                # 先找到 start 节点
                start_node = None
                for node in nodes:
                    if node.get('type') == 'start':
                        start_node = node
                        break
                
                # 从 start 节点的 child_nodes 中获取第一个节点
                if start_node and start_node.get('child_nodes'):
                    first_child_id = start_node['child_nodes'][0].get('node_id')
                    # 根据 node_id 找到对应的节点
                    for node in nodes:
                        if node.get('id') == first_child_id:
                            first_node = node
                            # 如果是 api_call，查找 API 详情
                            if node.get('type') == 'api_call':
                                api_details = self._find_api_for_node(node, candidate_apis)
                            break
                
                # 如果没有找到，使用旧逻辑（跳过 start/end 的第一个节点）
                if not first_node:
                    for node in nodes:
                        if node.get('type') not in ('start', 'end'):
                            first_node = node
                            if node.get('type') == 'api_call':
                                api_details = self._find_api_for_node(node, candidate_apis)
                            break
                
                detail_text = self.build_workflow_detail(selected_item, first_node, api_details)
            else:
                logger.warning(f"⚠️ 未找到选中的Workflow: {selection_name}")
                result["validated_json"] = self._create_rejection_schema(user_instruction)
                result["valid"] = True
                return result
        
        # ========================================
        # 🔥 第二轮：生成槽位值（Slot-Filling 架构）
        # ========================================
        
        # 提取槽位列表
        slots = []
        if selection_type == "API":
            # 从 API 请求参数中提取字段
            request_params = selected_item.get('request', selected_item.get('parameters', []))
            fields = [p.get('name') for p in request_params[:5] if p.get('name')]
            slots = ["page_title", "user_message", "submit_button_text"]
            for field in fields:
                slots.append(f"field_label_{field}")
            
            api_detail = self._build_api_detail_dict(
                selected_item,
                include_id=False,
                include_response=False,
                include_label=False,
                include_required=False
            )

            slots.extend(["api_url", "api_method"])

            system_prompt_round2 = f"""API详情：
{json.dumps(api_detail, ensure_ascii=False, indent=2)}

任务：为以下槽位生成中文文案（JSON 格式）：
{json.dumps(slots, ensure_ascii=False)}

要求：
- page_title：3-6 字
- user_message：10-20 字
- field_label_xxx：2-4 字
- api_url：完整的 API 路径（如果有路径参数，使用 ${param} 格式）
- api_method：HTTP 方法（GET/POST/PUT/DELETE）
- 只输出 JSON，不要其他内容"""
        
        else:  # WORKFLOW
            # 从工作流第一个节点的参数中提取字段
            first_node_config = first_node.get('config', {}) if first_node else {}
            parameters = first_node_config.get('parameters', {})
            fields = [k for k in list(parameters.keys())[:5]]
            slots = ["page_title", "user_message", "submit_button_text", "reset_button_text"]
            for field in fields:
                slots.append(f"field_label_{field}")
            slots.extend(["api_url", "api_method"])

            workflow_detail = self.build_workflow_detail(selected_item, first_node, api_details)

            system_prompt_round2 = f"""工作流详情：
{workflow_detail}

任务：为以下槽位生成中文文案（JSON 格式）：
{json.dumps(slots, ensure_ascii=False)}

要求：
- page_title：3-6 字
- user_message：10-20 字
- field_label_xxx：2-4 字
- api_url：完整的 API 路径（如果有路径参数，使用 ${param} 格式）
- api_method：HTTP 方法（GET/POST/PUT/DELETE）
- 只输出 JSON，不要其他内容"""
        
        messages_round2 = [
            {"role": "system", "content": system_prompt_round1},
            {"role": "user", "content": user_instruction},
            {"role": "assistant", "content": selection_output},
            {"role": "system", "content": system_prompt_round2}
        ]
        
        logger.info("🎯 第二轮对话: 生成槽位值（Slot-Filling）")
        logger.info(f"📋 System Prompt (第二轮):\n{system_prompt_round2}")
        
        slot_output = self._generate_single_turn(
            messages_round2,
            max_new_tokens=300,  # 槽位填充只需要很短的输出
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample
        )
        
        result["raw_output"] = slot_output
        logger.info(f"🤖 槽位原始输出:\n{slot_output}")
        
        # 解析槽位值 JSON
        slot_values = self._try_parse_json(slot_output)
        
        if not slot_values:
            logger.error("❌ 槽位值 JSON 解析失败")
            logger.error(f"原始输出(前200字符): {slot_output[:200]}...")
            
            # 降级到默认槽位值
            slot_values = self._get_default_slot_values(slots, selected_item, selection_type)
            logger.warning(f"⚠️ 使用默认槽位值: {list(slot_values.keys())}")
        
        logger.info(f"✅ 槽位值解析成功: {list(slot_values.keys())}")
        slot_values = self._normalize_slot_values(slot_values)
        result["slot_values"] = slot_values
        
        # ========================================
        # Worker 仅负责推理，不负责后端业务 Schema 组装
        # ========================================
        result["selection_detail"] = {
            "type": selection_type,
            "selected_item": selected_item,
            "first_node": first_node if selection_type == "WORKFLOW" else None
        }
        result["parsed_json"] = slot_values
        result["validated_json"] = None
        result["valid"] = True
        result["fixes"] = []
        
        return result

    def _normalize_slot_values(self, slot_values: Dict[str, Any]) -> Dict[str, Any]:
        api_url = slot_values.get("api_url")
        if isinstance(api_url, str) and api_url:
            import re
            slot_values["api_url"] = re.sub(r'(?<!\$)\{(\w+)\}', r'${\1}', api_url)
        return slot_values

    def _generate_single_turn(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True
    ) -> str:
        """单轮对话生成"""
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False
        )
        
        inputs = self.tokenizer(
            prompt,
            return_tensors='pt',
            add_special_tokens=False
        )
        
        input_ids = inputs['input_ids'].to(self.device)
        attention_mask = inputs['attention_mask'].to(self.device)
        
        generated_ids = self.llm.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=max_new_tokens,
            do_sample=do_sample,
            temperature=temperature,
            top_p=top_p,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id
        )
        
        # 只解码新生成的部分
        new_tokens = generated_ids[0][input_ids.shape[1]:]
        output = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
        
        # 记录 AI 原始输出（完整内容）
        logger.info(f"🤖 AI原始输出:\n{output.strip()}")
        
        return output.strip()
    
    def _parse_selection(self, output: str) -> Tuple[Optional[str], Optional[str]]:
        """
        解析第一轮选择结果
        
        格式：
        - "API: 查询订单" -> ("API", "查询订单")
        - "WORKFLOW: 购票流程" -> ("WORKFLOW", "购票流程")
        - 其他 -> (None, None) 或 ("REJECT", None)
        """
        output = output.strip()

        first_line = output.splitlines()[0].strip()
        if first_line.upper().startswith("HELP") or first_line.startswith("帮助"):
            return ("HELP", None)
        
        if output.startswith("API:") or output.startswith("API："):
            name = output.split(":", 1)[1].strip() if ":" in output else output.split("：", 1)[1].strip()
            return ("API", name)
        
        if output.startswith("WORKFLOW:") or output.startswith("WORKFLOW："):
            name = output.split(":", 1)[1].strip() if ":" in output else output.split("：", 1)[1].strip()
            return ("WORKFLOW", name)
        
        # 检查是否是拒绝响应（直接输出 JSON）
        if "{" in output:
            return ("REJECT", None)
        
        return (None, None)
    
    def _find_api_by_name(self, name: str, apis: List[Dict]) -> Optional[Dict]:
        """根据名称查找 API"""
        import re

        def _normalize(text: str) -> str:
            if not isinstance(text, str):
                return ""
            text = text.lower()
            # Remove whitespace + common zero-width separators (models sometimes insert them).
            text = re.sub(r"[\s\u200b\u200c\u200d\ufeff]+", "", text)
            # Keep only: Chinese, letters, digits, underscore.
            return re.sub(r"[^\w\u4e00-\u9fff]+", "", text)

        name_lower = (name or "").lower().strip()
        name_norm = _normalize(name)
        if not name_norm and not name_lower:
            return None

        # Score all candidates and pick the best. This avoids "first match wins" bugs when
        # descriptions contain empty/odd values or the model inserts invisible separators.
        best_match: Optional[Dict] = None
        best_score = 0.0

        def _score_pair(query_norm: str, cand_norm: str) -> float:
            if not query_norm or not cand_norm:
                return 0.0
            if query_norm == cand_norm:
                return 1.0
            if query_norm in cand_norm:
                return 0.95
            if cand_norm in query_norm:
                return 0.9
            return SequenceMatcher(None, query_norm, cand_norm).ratio()

        for api in apis:
            desc_raw = api.get("description") or api.get("desc") or ""
            name_raw = api.get("name") or ""
            path_raw = api.get("endpoint") or api.get("path") or ""

            desc_norm = _normalize(desc_raw)
            api_name_norm = _normalize(name_raw)
            path_norm = _normalize(path_raw)

            # Prefer semantic fields over paths.
            score = 0.0
            score = max(score, _score_pair(name_norm, desc_norm) * 1.0)
            score = max(score, _score_pair(name_norm, api_name_norm) * 0.98)
            score = max(score, _score_pair(name_norm, path_norm) * 0.7)

            # Also try raw substring match (helps when normalization erases separators).
            if name_lower and isinstance(desc_raw, str) and name_lower in desc_raw.lower():
                score = max(score, 0.93)

            if score > best_score:
                best_score = score
                best_match = api

        return best_match if best_score >= 0.6 else None
    
    def _find_workflow_by_name(self, name: str, workflows: List[Dict]) -> Optional[Dict]:
        """根据名称查找 Workflow"""
        name_lower = name.lower().strip()
        
        for wf in workflows:
            # 匹配 ID
            wf_id = wf.get('workflow_id', wf.get('id', '')).lower()
            if name_lower in wf_id or wf_id in name_lower:
                return wf
            
            # 匹配名称
            wf_name = wf.get('name', '').lower()
            if name_lower in wf_name or wf_name in name_lower:
                return wf
            
            # 匹配描述
            desc = wf.get('description', wf.get('desc', '')).lower()
            if name_lower in desc:
                return wf
        
        # 模糊匹配
        best_match, best_score = None, 0.0
        for wf in workflows:
            wf_name = wf.get('name', '')
            score = SequenceMatcher(None, name_lower, wf_name.lower()).ratio()
            if score > best_score:
                best_score, best_match = score, wf
        
        return best_match if best_score >= 0.5 else None
    
    def _get_default_slot_values(
        self, 
        slots: List[str], 
        selected_item: Dict[str, Any],
        selection_type: str
    ) -> Dict[str, str]:
        """
        获取默认槽位值（当 AI 生成失败时使用）
        
        Args:
            slots: 槽位列表
            selected_item: 选中的 API 或 Workflow
            selection_type: "API" 或 "WORKFLOW"
        
        Returns:
            默认槽位值字典
        """
        default_values = {}
        
        # 获取名称和描述
        name = selected_item.get('name', selected_item.get('description', selected_item.get('desc', '')))
        
        for slot in slots:
            if slot == "page_title":
                default_values[slot] = name[:6] if name else "操作界面"
            elif slot == "user_message":
                default_values[slot] = f"请填写{name}所需信息" if name else "请填写信息"
            elif slot == "submit_button_text":
                default_values[slot] = "提交"
            elif slot == "reset_button_text":
                default_values[slot] = "重置"
            elif slot == "api_url" and selection_type == "API":
                default_values[slot] = selected_item.get("endpoint", selected_item.get("path", ""))
            elif slot == "api_method" and selection_type == "API":
                default_values[slot] = selected_item.get("method", "GET")
            elif slot == "cancel_button_text":
                default_values[slot] = "取消"
            elif slot.startswith("field_label_"):
                # 全部字段强制走 AI，默认不做本地映射兜底
                default_values[slot] = ""
            else:
                default_values[slot] = "内容"
        
        return default_values
    
    
    def _find_api_for_node(self, node: Dict, apis: List[Dict]) -> Optional[Dict]:
        """为 api_call 节点查找关联的 API"""
        config = node.get('config', {})
        api_id = config.get('api_id', '')
        api_endpoint = config.get('api_endpoint', '')
        
        for api in apis:
            if api_id and api.get('api_id') == api_id:
                return api
            if api_endpoint and api.get('endpoint') == api_endpoint:
                return api
        
        return None

    def _find_workflow_for_api(self, api: Dict[str, Any], workflows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        api_id = api.get('api_id', api.get('id', ''))
        api_path = api.get('endpoint', api.get('path', ''))
        
        for workflow in workflows:
            nodes = workflow.get('nodes', [])
            for node in nodes:
                if node.get('type') != 'api_call':
                    continue
                config = node.get('config', {})
                node_api_id = config.get('api_id')
                node_endpoint = config.get('api_endpoint')
                if api_id and node_api_id == api_id:
                    return workflow
                if api_path and node_endpoint == api_path:
                    return workflow
        
        return None

    def _try_parse_json(self, text: str) -> Optional[Dict]:
        """尝试从文本中解析 JSON"""
        if not text:
            return None
        try:
            import re
            cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
            cleaned = re.sub(r"<thinking>.*?</thinking>", "", cleaned, flags=re.S)

            candidates = []
            fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned, flags=re.I)
            if fence:
                candidates.append(fence.group(1).strip())
            candidates.append(cleaned.strip())

            decoder = json.JSONDecoder()
            for cand in candidates:
                if not cand:
                    continue
                try:
                    return json.loads(cand)
                except Exception:
                    pass
                for idx, ch in enumerate(cand):
                    if ch in "{[":
                        try:
                            obj, _ = decoder.raw_decode(cand[idx:])
                            return obj
                        except Exception:
                            continue
        except Exception:
            return None
        return None
    
    def _create_rejection_schema(
        self, 
        user_instruction: str,
        available_actions: List[str] = None
    ) -> Dict:
        """
        创建拒绝响应的 AMIS Schema（Slot-Filling 架构）
        
        Args:
            user_instruction: 用户指令
            available_actions: 可用操作列表（可选）
        
        Returns:
            拒绝响应的 AMIS Schema
        """
        message = f"抱歉，无法处理您的请求：「{user_instruction}」"
        
        # 如果有可用操作，添加建议
        if available_actions:
            message += "\n\n您可以尝试以下操作：\n" + "\n".join([f"- {action}" for action in available_actions[:5]])
        else:
            message += "\n\n当前系统不支持此操作，请尝试其他功能。"
        
        return {
            "type": "page",
            "title": "无法处理",
            "body": {
                "type": "alert",
                "level": "warning",
                "body": message,
                "showIcon": True
            }
        }
    
    def _get_domain_cn(self, domain: str) -> str:
        """获取领域中文名"""
        domain_names = {
            "medical": "医疗", "finance": "财务", "ecommerce": "电商",
            "train_ticket": "火车票", "logistics": "物流", "hrm": "人力资源",
            "education": "教育", "hotel": "酒店", "banking": "银行",
            "government": "政务", "realestate": "房产", "catering": "餐饮",
            "general": "通用", "railway_ticketing": "火车票"
        }
        return domain_names.get(domain, domain)
    
    async def generate_two_round_async(
        self,
        user_instruction: str,
        candidate_apis: List[Dict[str, Any]],
        candidate_workflows: List[Dict[str, Any]],
        domain: str = "general",
        max_new_tokens: int = None,
        temperature: float = None,
        top_p: float = None,
        do_sample: bool = True,
        validate_endpoints: bool = True
    ) -> Dict:
        """异步版本的两轮对话生成"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate_two_round(
                user_instruction=user_instruction,
                candidate_apis=candidate_apis,
                candidate_workflows=candidate_workflows,
                domain=domain,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                validate_endpoints=validate_endpoints
            )
        )
    
    async def generate_slot_values(
        self,
        system_prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.2,
        top_p: float = 0.8,
        do_sample: bool = False
    ) -> str:
        """
        生成槽位值（第二轮对话）
        
        Args:
            system_prompt: 第二轮的 system prompt（包含详情和槽位列表）
            max_new_tokens: 最大生成 token 数
            temperature: 温度参数
            top_p: top_p 参数
            do_sample: 是否采样
        
        Returns:
            生成的槽位 JSON 字符串
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._generate_slot_values_sync(
                system_prompt=system_prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample
            )
        )
    
    def _generate_slot_values_sync(
        self,
        system_prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.2,
        top_p: float = 0.8,
        do_sample: bool = False
    ) -> str:
        """同步版本的槽位值生成"""
        if not self._is_loaded:
            raise RuntimeError("模型未加载")
        
        # 构建消息（只有 system prompt，因为这是第二轮）
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 应用 chat template
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False
        )
        
        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length
        ).to(self.device)
        
        # 生成
        with torch.no_grad():
            outputs = self.llm.generate(
                **inputs,
                max_new_tokens=max_new_tokens or self.max_new_tokens,
                temperature=temperature or self.temperature,
                top_p=top_p or self.top_p,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # 解码（只取新生成的部分）
        generated_ids = outputs[0][inputs['input_ids'].shape[1]:]
        output_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        return output_text.strip()
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy" if self._is_loaded else "not_loaded",
            "model_loaded": self._is_loaded,
            "device": str(self.device)
        }


# ============================================================================
# 3. 全局单例
# ============================================================================

pure_llm_model_service = PureLLMModelService()


def init_pure_llm_model():
    """
    初始化纯 LLM 模型（应在应用启动时调用）
    """
    logger.info("初始化纯LLM模型服务 (V9)...")
    try:
        pure_llm_model_service.load_model()
        logger.info("纯LLM模型服务初始化成功")
        return True
    except Exception as e:
        logger.error(f"纯LLM模型服务初始化失败: {e}")
        return False
