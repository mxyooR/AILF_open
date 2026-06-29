"""
纯 LLM 推理脚本 V11 - 两轮对话架构（Slot Filling）

核心架构：
- 移除 GNN 图谱编码
- 两轮对话：第一轮选择 API/Workflow，第二轮生成槽位 JSON
- 与训练脚本 train_pure_llm_v11.py 和数据集 dataset_v11.jsonl 对应

使用方法：
    python inference_v11.py
"""
import os
import json
import time
import torch
from typing import Optional, List, Dict, Set, Tuple, Any
from difflib import SequenceMatcher
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel


# ============================================================================
# 1. 端点验证器 (后处理)
# ============================================================================

class EndpointValidator:
    """端点验证器 - 后处理检查和修复"""
    
    def __init__(self, apis: List[Dict]):
        self.valid_paths: Set[str] = set()
        self.path_to_method: Dict[str, str] = {}
        self.endpoint_info: Dict[str, Dict] = {}
        
        for api in apis:
            path = api.get('path', api.get('endpoint', ''))
            method = api.get('method', 'GET').upper()
            if path:
                self.valid_paths.add(path)
                self.path_to_method[path] = method
                self.endpoint_info[path] = {
                    'method': method,
                    'request': api.get('request', api.get('parameters', []))
                }
        
        # 添加固定的系统端点
        self.valid_paths.add('/api/v1/workflow/state')
        self.valid_paths.add('/api/v1/command')
        self.path_to_method['/api/v1/workflow/state'] = 'POST'
        self.path_to_method['/api/v1/command'] = 'POST'

    def find_best_match(self, url: str) -> Optional[str]:
        if url in self.valid_paths:
            return url
        
        best_match, best_score = None, 0.0
        for valid_path in self.valid_paths:
            score = SequenceMatcher(None, url.lower(), valid_path.lower()).ratio()
            if score > best_score:
                best_score, best_match = score, valid_path
        
        return best_match if best_score >= 0.3 else None
    
    def fix_urls_in_json(self, schema: Dict) -> Tuple[Dict, List[str]]:
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
                    fixes.append(f"Method: '{current_method}' -> '{correct_method}'")
                    obj['method'] = correct_method.lower()
        
        def fix(obj):
            if isinstance(obj, dict):
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
# 2. 纯 LLM 推理器 V10
# ============================================================================

class PureLLMInferenceV10:
    """
    纯 LLM 推理器 V10 - 两轮对话架构
    
    推理流程：
    1. 第一轮：根据候选列表选择 API 或 Workflow
    2. 第二轮：根据详情生成槽位 JSON
    """
    
    def __init__(
        self,
        base_model_path: str,
        lora_checkpoint_path: str,
        use_4bit: bool = True
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🔧 使用设备: {self.device}")
        
        # 1. 加载 Tokenizer
        print("📥 加载 Tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            base_model_path,
            trust_remote_code=True,
            local_files_only=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 2. 加载基础 LLM
        print("📥 加载基础 LLM (4-bit 量化)...")
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
        
        # 3. 加载 LoRA 权重
        print(f"📥 加载 LoRA 权重: {lora_checkpoint_path}")
        self.llm = PeftModel.from_pretrained(
            self.base_model,
            lora_checkpoint_path
        )
        self.llm.eval()
        
        self.llm_dtype = torch.bfloat16 if use_4bit else torch.float16
        print("✅ 模型加载完成\n")

    def build_candidate_list(self, apis: List[Dict], workflows: List[Dict]) -> str:
        """构建候选列表文本（与训练数据格式一致）"""
        lines = []
        
        for api in apis:
            method = api.get('method', 'GET').upper()
            path = api.get('path', api.get('endpoint', ''))
            desc = api.get('desc', api.get('description', ''))
            if path:
                tag = "（仅工作流）" if api.get("workflow_only", False) else ""
                lines.append(f"[API] {method} {path} - {desc}{tag}")
        
        for wf in workflows:
            wf_id = wf.get('id', wf.get('workflow_id', ''))
            wf_name = wf.get('name', '')
            if wf_id:
                # 🔥 与训练数据格式一致：[WORKFLOW] id - 名称（不加描述）
                lines.append(f"[WORKFLOW] {wf_id} - {wf_name}")
        
        return "\n".join(lines)
    
    def build_api_detail(self, api: Dict) -> str:
        """构建 API 详情文本（与训练数据格式一致）"""
        detail = {
            "id": api.get('id', api.get('api_id', '')),
            "type": "api",
            "desc": api.get('desc', api.get('description', '')),
            "path": api.get('path', api.get('endpoint', '')),
            "method": api.get('method', 'GET').upper(),
            "request": [],
            "response": [],
            "domain": api.get('domain', '')
        }
        
        for param in api.get('request', api.get('parameters', [])):
            detail["request"].append({
                "name": param.get('name', ''),
                "type": param.get('type', 'string'),
                "label": param.get('label', param.get('description', param.get('name', ''))),
                "required": param.get('required', False)
            })
        
        for resp in api.get('response', []):
            detail["response"].append({
                "name": resp.get('name', ''),
                "type": resp.get('type', 'string'),
                "desc": resp.get('desc', resp.get('description', ''))
            })
        
        return json.dumps(detail, ensure_ascii=False, indent=2)
    
    def build_workflow_detail(self, workflow: Dict, first_node: Dict = None, apis: List[Dict] = None) -> str:
        """
        构建工作流详情文本（与训练数据格式一致）
        
        🔥 关键：必须包含 first_node 的完整 API 详情，否则模型不知道该生成什么
        """
        workflow_id = workflow.get('id', workflow.get('workflow_id', ''))
        
        nodes = workflow.get('nodes', [])
        valid_nodes = [n for n in nodes if n.get('type') not in ('start', 'end')]
        node_names = [n.get('name', n.get('id', '')) for n in valid_nodes[:5]]
        node_chain = " → ".join(node_names)
        if len(valid_nodes) > 5:
            node_chain += " → ..."
        
        detail = {
            "id": workflow_id,
            "name": workflow.get('name', ''),
            "desc": workflow.get('desc', workflow.get('description', '')),
            "node_chain": node_chain
        }
        
        if first_node:
            first_node_id = first_node.get('id', '')
            full_first_node_id = f"{workflow_id}_node_{first_node_id}"
            
            # 获取第一个节点的 API 详情
            first_node_api = self._get_node_api_detail(first_node, apis)
            
            detail["first_node"] = {
                "id": full_first_node_id,
                "name": first_node.get('name', ''),
                "type": first_node.get('type', ''),
                "ai_instructions": first_node.get('ai_instructions', {}),
                "api": first_node_api
            }
        
        return json.dumps(detail, ensure_ascii=False, indent=2)
    
    def _get_node_api_detail(self, node: Dict, apis: List[Dict] = None) -> Optional[Dict]:
        """获取节点对应的 API 详情"""
        config = node.get('config', {})
        api_id = config.get('api_id', '')
        api_endpoint = config.get('api_endpoint', '')
        method = config.get('method', 'GET')
        
        if not api_endpoint and not api_id:
            return None
        
        # 尝试从传入的 APIs 中找到完整信息
        if apis:
            for api in apis:
                if api.get('id') == api_id or api.get('path') == api_endpoint:
                    return {
                        "id": api.get('id', ''),
                        "path": api.get('path', api_endpoint),
                        "method": api.get('method', method),
                        "request": api.get('request', []),
                        "response": api.get('response', [])
                    }
        
        # 如果找不到，返回基本信息
        return {
            "path": api_endpoint,
            "method": method,
            "request": [],
            "response": []
        }

    def _generate_single_turn(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 512,
        temperature: float = 0.2,
        top_p: float = 0.8,
        do_sample: bool = False
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
        
        with torch.no_grad():
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
        
        new_tokens = generated_ids[0][input_ids.shape[1]:]
        output = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
        
        return output.strip()
    
    def _parse_selection(self, output: str) -> Tuple[Optional[str], Optional[str]]:
        """解析第一轮选择结果"""
        output = output.strip()

        first_line = output.splitlines()[0].strip()
        if first_line.upper().startswith("HELP") or first_line.startswith("帮助"):
            return ("HELP", None)
        
        if output.startswith("REJECT"):
            return ("REJECT", None)
        
        if output.startswith("API:") or output.startswith("API："):
            name = output.split(":", 1)[1].strip() if ":" in output else output.split("：", 1)[1].strip()
            return ("API", name)
        
        if output.startswith("WORKFLOW:") or output.startswith("WORKFLOW："):
            name = output.split(":", 1)[1].strip() if ":" in output else output.split("：", 1)[1].strip()
            return ("WORKFLOW", name)
        
        if "{" in output:
            return ("REJECT", None)
        
        return (None, None)

    def _build_slots_for_api(self, api: Dict) -> List[str]:
        fields = [p.get("name") for p in api.get("request", [])[:5] if p.get("name")]
        slots = ["page_title", "user_message", "submit_button_text", "api_url", "api_method"]
        for field in fields:
            slots.append(f"field_label_{field}")
        return slots

    def _build_slots_for_workflow(self, first_node_api: Optional[Dict]) -> List[str]:
        slots = ["page_title", "user_message", "submit_button_text", "reset_button_text"]
        if first_node_api and first_node_api.get("path"):
            slots.extend(["api_url", "api_method"])
            for field in first_node_api.get("request", [])[:5]:
                field_name = field.get("name")
                if field_name:
                    slots.append(f"field_label_{field_name}")
        return slots

    def _build_slot_prompt(self, detail_label: str, detail_json: str, slots: List[str]) -> str:
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
        return f"""{detail_label}：
{detail_json}

任务：为以下槽位生成中文文案（JSON 格式）：
{slots_text}

要求：
{chr(10).join(requirements)}"""

    def _normalize_api_url(self, api_url: str) -> str:
        if not api_url:
            return api_url
        import re
        return re.sub(r'(?<!\\$)\\{(\\w+)\\}', r'${\\1}', api_url)

    def _postprocess_slot_values(self, slot_values: Dict[str, Any]) -> Dict[str, Any]:
        api_url = slot_values.get("api_url")
        if isinstance(api_url, str):
            slot_values["api_url"] = self._normalize_api_url(api_url)
        return slot_values
    
    def _find_api_by_name(self, name: str, apis: List[Dict]) -> Optional[Dict]:
        """根据名称查找 API"""
        name_lower = name.lower().strip()
        
        for api in apis:
            desc = api.get('desc', api.get('description', '')).lower()
            if name_lower in desc or desc in name_lower:
                return api
            
            path = api.get('path', api.get('endpoint', '')).lower()
            if name_lower in path:
                return api
        
        # 模糊匹配
        best_match, best_score = None, 0.0
        for api in apis:
            desc = api.get('desc', api.get('description', ''))
            score = SequenceMatcher(None, name_lower, desc.lower()).ratio()
            if score > best_score:
                best_score, best_match = score, api
        
        return best_match if best_score >= 0.5 else None
    
    def _find_workflow_by_name(self, name: str, workflows: List[Dict]) -> Optional[Dict]:
        """根据名称查找 Workflow"""
        name_lower = name.lower().strip()
        
        for wf in workflows:
            wf_id = wf.get('id', wf.get('workflow_id', '')).lower()
            if name_lower in wf_id or wf_id in name_lower:
                return wf
            
            wf_name = wf.get('name', '').lower()
            if name_lower in wf_name or wf_name in name_lower:
                return wf
        
        # 模糊匹配
        best_match, best_score = None, 0.0
        for wf in workflows:
            wf_name = wf.get('name', '')
            score = SequenceMatcher(None, name_lower, wf_name.lower()).ratio()
            if score > best_score:
                best_score, best_match = score, wf
        
        return best_match if best_score >= 0.5 else None
    
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
    
    @torch.no_grad()
    def generate_two_round(
        self,
        user_instruction: str,
        candidate_apis: List[Dict],
        candidate_workflows: List[Dict],
        domain: str = "general",
        max_new_tokens: int = 800,
        temperature: float = 0.2,
        top_p: float = 0.8,
        do_sample: bool = False
    ) -> Dict:
        """
        两轮对话生成槽位 JSON
        
        第一轮：选择 API 或 Workflow
        第二轮：根据详情生成槽位 JSON
        """
        domain_cn = self._get_domain_cn(domain)
        
        # ========================================
        # 第一轮：选择 API 或 Workflow
        # ========================================
        candidate_list = self.build_candidate_list(candidate_apis, candidate_workflows)
        
        system_prompt_round1 = f"""你是{domain_cn}领域的 AMIS 界面生成助手。

可用资源：
{candidate_list}

任务：根据用户指令选择合适的 API 或工作流。
- 如果匹配到 API，输出：API: <名称>
- 如果匹配到工作流，输出：WORKFLOW: <名称>
- 如果用户在询问你是谁 / 你能做什么 / 你现在能帮我干啥 / 帮助，输出：HELP
- 如果无法匹配，输出：REJECT"""
        
        messages_round1 = [
            {"role": "system", "content": system_prompt_round1},
            {"role": "user", "content": user_instruction}
        ]
        
        print(f"🔄 第一轮对话：选择 API/Workflow")
        print(f"📝 用户指令: {user_instruction}")
        
        round1_start = time.time()
        selection_output = self._generate_single_turn(
            messages_round1,
            max_new_tokens=100,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample
        )
        round1_time = time.time() - round1_start
        
        print(f"📝 第一轮输出: {selection_output}")
        print(f"⏱️ 第一轮耗时: {round1_time:.2f}s")
        
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
            result["validated_json"] = "HELP"
            result["valid"] = True
            result["round1_time"] = round1_time
            result["round2_time"] = 0
            result["total_time"] = round1_time
            return result
        
        # 如果是拒绝或无法解析
        if selection_type == "REJECT" or selection_type is None:
            parsed = self._try_parse_json(selection_output)
            if parsed:
                result["parsed_json"] = parsed
                result["validated_json"] = parsed
                result["valid"] = True
                result["round1_time"] = round1_time
                result["round2_time"] = 0
                result["total_time"] = round1_time
                return result
            else:
                if selection_output.strip().startswith("REJECT"):
                    result["validated_json"] = "REJECT"
                else:
                    result["validated_json"] = "REJECT"
                result["valid"] = True
                result["round1_time"] = round1_time
                result["round2_time"] = 0
                result["total_time"] = round1_time
                return result
        
        # ========================================
        # 第二轮：根据详情生成槽位 JSON
        # ========================================
        detail_json = ""
        slots = []
        selected_item = None
        
        if selection_type == "API":
            selected_item = self._find_api_by_name(selection_name, candidate_apis)
            if selected_item:
                detail_json = self.build_api_detail(selected_item)
                slots = self._build_slots_for_api(selected_item)
            else:
                print(f"⚠️ 未找到选中的 API: {selection_name}")
                result["validated_json"] = "REJECT"
                result["valid"] = True
                result["round1_time"] = round1_time
                result["round2_time"] = 0
                result["total_time"] = round1_time
                return result
        
        elif selection_type == "WORKFLOW":
            selected_item = self._find_workflow_by_name(selection_name, candidate_workflows)
            if selected_item:
                nodes = selected_item.get('nodes', [])
                first_node = None
                for node in nodes:
                    if node.get('type') not in ('start', 'end'):
                        first_node = node
                        break
                first_node_api = self._get_node_api_detail(first_node, candidate_apis) if first_node else None
                detail_json = self.build_workflow_detail(selected_item, first_node, candidate_apis)
                slots = self._build_slots_for_workflow(first_node_api)
            else:
                print(f"⚠️ 未找到选中的 Workflow: {selection_name}")
                result["validated_json"] = "REJECT"
                result["valid"] = True
                result["round1_time"] = round1_time
                result["round2_time"] = 0
                result["total_time"] = round1_time
                return result
        
        # 🔥 第二轮 System Prompt 与训练数据格式一致（Slot Filling）
        if selection_type == "API":
            system_prompt_round2 = self._build_slot_prompt("API详情", detail_json, slots)
        else:  # WORKFLOW
            system_prompt_round2 = self._build_slot_prompt("工作流详情", detail_json, slots)
        
        messages_round2 = [
            {"role": "system", "content": system_prompt_round1},
            {"role": "user", "content": user_instruction},
            {"role": "assistant", "content": selection_output},
            {"role": "system", "content": system_prompt_round2}
        ]
        
        print(f"🔄 第二轮对话：生成槽位 JSON")
        
        round2_start = time.time()
        slot_output = self._generate_single_turn(
            messages_round2,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample
        )
        round2_time = time.time() - round2_start
        
        print(f"⏱️ 第二轮耗时: {round2_time:.2f}s")
        
        result["raw_output"] = slot_output
        result["round1_time"] = round1_time
        result["round2_time"] = round2_time
        result["total_time"] = round1_time + round2_time
        
        # 解析和验证 JSON
        parsed = self._try_parse_json(slot_output)
        if parsed:
            parsed = self._postprocess_slot_values(parsed)
            result["parsed_json"] = parsed
            result["validated_json"] = parsed
            result["valid"] = True
        else:
            result["fixes"].append("JSON 解析失败")
        
        return result
    
    def _create_rejection_schema(self, user_instruction: str) -> Dict:
        """创建拒绝响应的 AMIS Schema（兼容旧逻辑）"""
        return {
            "type": "page",
            "title": "无法处理",
            "body": {
                "type": "alert",
                "level": "warning",
                "body": f"抱歉，无法处理您的请求：「{user_instruction}」\n\n当前系统不支持此操作，请尝试其他功能。",
                "showIcon": True
            }
        }


# ============================================================================
# 3. 后端配置转换器
# ============================================================================

class BackendConfigConverter:
    """将后端配置格式转换为数据集训练格式"""
    
    @staticmethod
    def convert_api(api: Dict, domain: str = "unknown") -> Dict:
        """转换单个 API"""
        request_fields = []
        for param in api.get('parameters', []):
            request_fields.append({
                "name": param.get('name', ''),
                "type": param.get('type', 'string'),
                "label": param.get('description', param.get('name', '')),
                "required": param.get('required', False)
            })
        
        response_fields = []
        responses = api.get('responses', {})
        for status_code, resp_info in responses.items():
            if 'response_schema' in resp_info:
                schema = resp_info['response_schema']
                if 'properties' in schema:
                    data_props = schema['properties'].get('data', {}).get('properties', {})
                    for field_name, field_info in data_props.items():
                        response_fields.append({
                            "name": field_name,
                            "type": field_info.get('type', 'string'),
                            "desc": field_name
                        })
        
        return {
            "id": api.get('api_id', ''),
            "type": "api",
            "desc": api.get('description', api.get('name', '')),
            "path": api.get('endpoint', ''),
            "method": api.get('method', 'GET'),
            "request": request_fields,
            "response": response_fields,
            "domain": domain
        }
    
    @staticmethod
    def convert_workflow(workflow: Dict, domain: str = "unknown") -> Dict:
        """转换单个 Workflow"""
        # 模板中用 name 作为 ID，如 "workflow_book_ticket"
        workflow_id = workflow.get('workflow_id', workflow.get('id', workflow.get('name', '')))
        return {
            "id": workflow_id,
            "type": "workflow",
            "desc": workflow.get('description', ''),
            "name": workflow.get('display_name', workflow.get('name', '')),
            "nodes": workflow.get('nodes', []),
            "domain": domain
        }
    
    @classmethod
    def load_from_template(cls, template_path: str, domain: str = "unknown") -> Tuple[List[Dict], List[Dict]]:
        """从后端模板文件加载并转换"""
        with open(template_path, 'r', encoding='utf-8') as f:
            template = json.load(f)
        
        apis = []
        workflows = []
        
        for api in template.get('api_routes', []):
            apis.append(cls.convert_api(api, domain))
        
        for workflow in template.get('workflows', []):
            workflows.append(cls.convert_workflow(workflow, domain))
        
        print(f"✅ 从模板加载: {len(apis)} 个 API + {len(workflows)} 个 Workflow")
        
        return apis, workflows


# ============================================================================
# 4. 测试函数
# ============================================================================

def create_test_scenario():
    """
    创建全新的测试场景 - 宠物医院管理系统
    这个场景不在训练数据中，用于测试模型的泛化能力
    """
    apis = [
        {
            "id": "api_pet_list",
            "path": "/api/pet/pets",
            "method": "GET",
            "desc": "查询宠物列表",
            "request": [
                {"name": "owner_id", "type": "string", "label": "主人ID", "required": False},
                {"name": "species", "type": "string", "label": "物种", "required": False}
            ],
            "response": [
                {"name": "pets", "type": "array", "desc": "宠物列表"},
                {"name": "total", "type": "integer", "desc": "总数"}
            ]
        },
        {
            "id": "api_pet_detail",
            "path": "/api/pet/pets/{pet_id}",
            "method": "GET",
            "desc": "查询宠物详情",
            "request": [
                {"name": "pet_id", "type": "string", "label": "宠物ID", "required": True}
            ],
            "response": [
                {"name": "pet", "type": "object", "desc": "宠物信息"},
                {"name": "medical_history", "type": "array", "desc": "病历记录"}
            ]
        },
        {
            "id": "api_appointment_create",
            "path": "/api/pet/appointments",
            "method": "POST",
            "desc": "预约挂号",
            "request": [
                {"name": "pet_id", "type": "string", "label": "宠物ID", "required": True},
                {"name": "doctor_id", "type": "string", "label": "医生ID", "required": True},
                {"name": "date", "type": "date", "label": "预约日期", "required": True},
                {"name": "time_slot", "type": "string", "label": "时间段", "required": True},
                {"name": "symptoms", "type": "string", "label": "症状描述", "required": False}
            ],
            "response": [
                {"name": "appointment_id", "type": "string", "desc": "预约号"},
                {"name": "queue_number", "type": "integer", "desc": "排队号"}
            ]
        },
        {
            "id": "api_doctor_list",
            "path": "/api/pet/doctors",
            "method": "GET",
            "desc": "查询医生排班",
            "request": [
                {"name": "date", "type": "date", "label": "日期", "required": False},
                {"name": "specialty", "type": "string", "label": "专科", "required": False}
            ],
            "response": [
                {"name": "doctors", "type": "array", "desc": "医生列表"}
            ]
        },
        {
            "id": "api_vaccine_record",
            "path": "/api/pet/vaccines",
            "method": "GET",
            "desc": "查询疫苗接种记录",
            "request": [
                {"name": "pet_id", "type": "string", "label": "宠物ID", "required": True}
            ],
            "response": [
                {"name": "vaccines", "type": "array", "desc": "疫苗记录"},
                {"name": "next_vaccine", "type": "object", "desc": "下次接种提醒"}
            ]
        },
        {
            "id": "api_vaccine_apply",
            "path": "/api/pet/vaccines/apply",
            "method": "POST",
            "desc": "申请疫苗接种",
            "request": [
                {"name": "pet_id", "type": "string", "label": "宠物ID", "required": True},
                {"name": "vaccine_type", "type": "string", "label": "疫苗类型", "required": True},
                {"name": "appointment_date", "type": "date", "label": "预约日期", "required": True}
            ],
            "response": [
                {"name": "apply_id", "type": "string", "desc": "申请编号"}
            ]
        },
        {
            "id": "api_bill_query",
            "path": "/api/pet/bills",
            "method": "GET",
            "desc": "查询账单",
            "request": [
                {"name": "pet_id", "type": "string", "label": "宠物ID", "required": False},
                {"name": "status", "type": "string", "label": "状态", "required": False}
            ],
            "response": [
                {"name": "bills", "type": "array", "desc": "账单列表"},
                {"name": "total_amount", "type": "float", "desc": "总金额"}
            ]
        },
        {
            "id": "api_bill_pay",
            "path": "/api/pet/bills/{bill_id}/pay",
            "method": "POST",
            "desc": "支付账单",
            "request": [
                {"name": "bill_id", "type": "string", "label": "账单ID", "required": True},
                {"name": "payment_method", "type": "string", "label": "支付方式", "required": True}
            ],
            "response": [
                {"name": "success", "type": "boolean", "desc": "是否成功"},
                {"name": "receipt_no", "type": "string", "desc": "收据号"}
            ]
        },
        {
            "id": "api_medicine_list",
            "path": "/api/pet/medicines",
            "method": "GET",
            "desc": "查询药品库存",
            "request": [
                {"name": "category", "type": "string", "label": "分类", "required": False},
                {"name": "keyword", "type": "string", "label": "关键词", "required": False}
            ],
            "response": [
                {"name": "medicines", "type": "array", "desc": "药品列表"}
            ]
        },
        {
            "id": "api_hospitalize_apply",
            "path": "/api/pet/hospitalize",
            "method": "POST",
            "desc": "住院申请",
            "request": [
                {"name": "pet_id", "type": "string", "label": "宠物ID", "required": True},
                {"name": "reason", "type": "string", "label": "住院原因", "required": True},
                {"name": "expected_days", "type": "integer", "label": "预计天数", "required": True}
            ],
            "response": [
                {"name": "hospitalize_id", "type": "string", "desc": "住院单号"},
                {"name": "bed_no", "type": "string", "desc": "床位号"}
            ]
        }
    ]
    
    workflows = [
        {
            "id": "workflow_pet_checkup",
            "name": "宠物体检流程",
            "desc": "完整的宠物健康体检流程",
            "nodes": [
                {"id": "start", "name": "开始", "type": "start"},
                {"id": "n_register", "name": "登记信息", "type": "api_call", 
                 "ai_instructions": {"user_message": "请输入宠物信息", "action": "登记"}},
                {"id": "n_exam", "name": "基础检查", "type": "api_call",
                 "ai_instructions": {"user_message": "进行基础体检", "action": "检查"}},
                {"id": "n_report", "name": "生成报告", "type": "api_call",
                 "ai_instructions": {"user_message": "生成体检报告", "action": "报告"}},
                {"id": "n_pay", "name": "缴费", "type": "api_call",
                 "ai_instructions": {"user_message": "请支付体检费用", "action": "支付"}},
                {"id": "end", "name": "结束", "type": "end"}
            ]
        },
        {
            "id": "workflow_pet_treatment",
            "name": "宠物诊疗流程",
            "desc": "从挂号到治疗的完整流程",
            "nodes": [
                {"id": "start", "name": "开始", "type": "start"},
                {"id": "n_appointment", "name": "预约挂号", "type": "api_call",
                 "ai_instructions": {"user_message": "请选择医生和时间", "action": "预约"}},
                {"id": "n_checkin", "name": "到院签到", "type": "api_call",
                 "ai_instructions": {"user_message": "请签到", "action": "签到"}},
                {"id": "n_diagnosis", "name": "医生诊断", "type": "api_call",
                 "ai_instructions": {"user_message": "等待诊断结果", "action": "诊断"}},
                {"id": "n_prescription", "name": "开具处方", "type": "api_call",
                 "ai_instructions": {"user_message": "查看处方", "action": "处方"}},
                {"id": "n_pay", "name": "缴费取药", "type": "api_call",
                 "ai_instructions": {"user_message": "请支付并取药", "action": "取药"}},
                {"id": "end", "name": "结束", "type": "end"}
            ]
        },
        {
            "id": "workflow_vaccine",
            "name": "疫苗接种流程",
            "desc": "宠物疫苗接种预约和执行流程",
            "nodes": [
                {"id": "start", "name": "开始", "type": "start"},
                {"id": "n_check", "name": "查询接种记录", "type": "api_call",
                 "ai_instructions": {"user_message": "查询历史接种记录", "action": "查询"}},
                {"id": "n_select", "name": "选择疫苗", "type": "api_call",
                 "ai_instructions": {"user_message": "请选择要接种的疫苗", "action": "选择"}},
                {"id": "n_apply", "name": "预约接种", "type": "api_call",
                 "ai_instructions": {"user_message": "选择接种时间", "action": "预约"}},
                {"id": "n_notify", "name": "接种提醒", "type": "notification",
                 "ai_instructions": {"user_message": "预约成功", "action": "提醒"}},
                {"id": "end", "name": "结束", "type": "end"}
            ]
        }
    ]
    
    return apis, workflows


def test_inference(lora_checkpoint_path: Optional[str] = None):
    """测试推理 - 使用全新场景测试泛化能力"""
    print("="*70)
    print("  纯 LLM 推理测试 V11 - 泛化能力测试")
    print("  场景：宠物医院管理系统（不在训练数据中）")
    print("="*70)
    
    # ========== 路径配置 ==========
    BASE_MODEL_PATH = "e:/Programming/AILF/Qwen/Qwen3-4B"
    LORA_CHECKPOINT_PATH = lora_checkpoint_path or "e:/Programming/AILF/Model/model"
    
    # 检查路径
    if not os.path.exists(BASE_MODEL_PATH):
        BASE_MODEL_PATH = "/root/ailf/Qwen3-4B"
        LORA_CHECKPOINT_PATH = lora_checkpoint_path or "/root/ailf/checkpoints_v11/best_model"
    
    print(f"📁 基础模型: {BASE_MODEL_PATH}")
    print(f"📁 LoRA 权重: {LORA_CHECKPOINT_PATH}")
    
    # 准备报告数据
    report_data = {
        "model_info": {
            "base_model": BASE_MODEL_PATH,
            "lora_checkpoint": LORA_CHECKPOINT_PATH,
            "test_time": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "test_cases": []
    }
    
    # 加载推理器
    inferencer = PureLLMInferenceV10(
        base_model_path=BASE_MODEL_PATH,
        lora_checkpoint_path=LORA_CHECKPOINT_PATH,
        use_4bit=True
    )
    
    # 创建全新测试场景
    print(f"\n📂 创建测试场景：宠物医院管理系统")
    apis, workflows = create_test_scenario()
    
    print(f"\n📊 可用 API ({len(apis)} 个):")
    for api in apis:
        print(f"  - {api['method']} {api['path']} - {api['desc']}")
    
    print(f"\n📊 可用 Workflow ({len(workflows)} 个):")
    for wf in workflows:
        print(f"  - {wf['id']} - {wf['name']}")
    
    # ========== 测试用例 ==========
    test_cases = [
        # API 调用测试
        "查询我家狗狗的信息",
        "帮我看看有哪些医生今天上班",
        "查一下疫苗接种记录",
        "我要给猫咪预约挂号",
        "查询未支付的账单",
        
        # 工作流测试
        "我想带宠物做个全面体检",
        "我家狗狗生病了要看医生",
        "要给小猫打疫苗",
        
        # Help 命令测试
        "你是谁",
        "你能做什么",
        "你现在能帮我干啥",
        "帮助",
        
        # 拒绝测试（无关请求）
        "今天天气怎么样",
        "帮我订个机票",
        "推荐一家好吃的餐厅",
    ]
    
    print("\n" + "="*70)
    print("  开始测试")
    print("="*70)
    
    total_time = 0
    valid_count = 0
    api_count = 0
    workflow_count = 0
    reject_count = 0
    help_count = 0
    unknown_count = 0
    for i, instruction in enumerate(test_cases):
        print(f"\n{'='*60}")
        print(f"测试 {i+1}: {instruction}")
        print('='*60)
        
        test_start = time.time()
        result = inferencer.generate_two_round(
            user_instruction=instruction,
            candidate_apis=apis,
            candidate_workflows=workflows,
            domain="pet_hospital",
            max_new_tokens=800,
            temperature=0.2,
            top_p=0.8,
            do_sample=False
        )
        selection = result.get("selection", "") if isinstance(result, dict) else ""
        if isinstance(result, dict) and result.get("valid"):
            valid_count += 1
        if isinstance(selection, str):
            if selection.startswith("API:"):
                api_count += 1
            elif selection.startswith("WORKFLOW:"):
                workflow_count += 1
            elif selection.startswith("REJECT"):
                reject_count += 1
            elif selection.startswith("HELP") or selection == "HELP":
                help_count += 1
            else:
                unknown_count += 1
        else:
            unknown_count += 1
        test_time = time.time() - test_start
        total_time += test_time
        
        print(f"\n📊 结果:")
        print(f"  选择: {result['selection']}")
        print(f"  有效: {result['valid']}")
        if result['fixes']:
            print(f"  修复: {result['fixes']}")
        print(f"  ⏱️ 总耗时: {test_time:.2f}s")
        
        if result['validated_json']:
            print(f"\n📄 生成的槽位 JSON:")
            print(json.dumps(result['validated_json'], ensure_ascii=False, indent=2))
        elif result.get('raw_output'):
            # JSON 解析失败时显示原始输出
            print(f"\n📄 原始输出 (JSON 解析失败):")
            print(result['raw_output'])
        
        # 保存到报告
        test_case_data = {
            "test_id": i + 1,
            "instruction": instruction,
            "selection": result.get('selection', ''),
            "valid": result.get('valid', False),
            "fixes": result.get('fixes', []),
            "validated_json": result.get('validated_json'),
            "raw_output": result.get('raw_output', ''),
            "round1_output": result.get('round1_output', ''),
            "round2_output": result.get('round2_output', ''),
            "round1_time": result.get('round1_time', 0),
            "round2_time": result.get('round2_time', 0),
            "total_time": test_time
        }
        report_data["test_cases"].append(test_case_data)
    
    print(f"\n{'='*70}")
    print(f"  测试汇总")
    print(f"{'='*70}")
    print(f"总测试数: {len(test_cases)}")
    print(f"有效响应: {valid_count}/{len(test_cases)} ({valid_count/len(test_cases)*100:.1f}%)")
    print(f"  - API 调用: {api_count}")
    print(f"  - 工作流: {workflow_count}")
    print(f"  - 帮助命令: {help_count}")
    print(f"  - 拒绝: {reject_count}")
    print(f"  - 未知: {unknown_count}")
    print(f"平均耗时: {total_time/len(test_cases):.2f}s")
    print("="*70)

    # 保存统计到报告
    report_data["summary"] = {
        "total": len(test_cases),
        "valid": valid_count,
        "api": api_count,
        "workflow": workflow_count,
        "help": help_count,
        "reject": reject_count,
        "unknown": unknown_count,
        "avg_time": total_time / len(test_cases)
    }
    
    # 导出报告
    checkpoint_name = os.path.basename(LORA_CHECKPOINT_PATH)
    report_filename = f"inference_report_{checkpoint_name}_{time.strftime('%Y%m%d_%H%M%S')}.json"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(script_dir, report_filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细报告已导出: {report_path}")

    total = len(test_cases)
    return {
        "total": total,
        "valid": valid_count,
        "api": api_count,
        "workflow": workflow_count,
        "help": help_count,
        "reject": reject_count,
        "unknown": unknown_count,
        "avg_time": (total_time / total) if total else 0
    }


def compare_checkpoints_petshop():
    """对比 V11 模型（宠物医院场景泛化）"""
    print("="*70)
    print("  V11 模型评估：宠物医院场景（泛化）")
    print("="*70)
    
    base_model = "e:/Programming/AILF/Qwen/Qwen3-4B"
    ckpt1 = "e:/Programming/AILF/Model/checkpoint_epoch_1"
    ckpt2 = "e:/Programming/AILF/Model/checkpoint_epoch_2"
    
    if not os.path.exists(base_model):
        base_model = "/root/ailf/Qwen3-4B"
        ckpt1 = "/root/ailf/checkpoints_v11/checkpoint_epoch_1"
        ckpt2 = "/root/ailf/checkpoints_v11/checkpoint_epoch_2"
    
    print(f"📌 Base: {base_model}")
    print(f"📌 Epoch1: {ckpt1}")
    print(f"📌 Epoch2: {ckpt2}")
    
    print("\n" + "="*70)
    print("  Epoch1 测试")
    print("="*70)
    stats1 = test_inference(lora_checkpoint_path=ckpt1)
    
    print("\n" + "="*70)
    print("  Epoch2 测试")
    print("="*70)
    stats2 = test_inference(lora_checkpoint_path=ckpt2)
    
    print("\n" + "="*70)
    print("  对比汇总")
    print("="*70)
    if stats1 and stats2:
        print(f"Epoch1: valid={stats1['valid']}/{stats1['total']}, "
              f"api={stats1['api']}, workflow={stats1['workflow']}, "
              f"help={stats1['help']}, reject={stats1['reject']}, "
              f"unknown={stats1['unknown']}, avg_time={stats1['avg_time']:.2f}s")
        print(f"Epoch2: valid={stats2['valid']}/{stats2['total']}, "
              f"api={stats2['api']}, workflow={stats2['workflow']}, "
              f"help={stats2['help']}, reject={stats2['reject']}, "
              f"unknown={stats2['unknown']}, avg_time={stats2['avg_time']:.2f}s")


    
if __name__ == "__main__":
    compare_checkpoints_petshop()
