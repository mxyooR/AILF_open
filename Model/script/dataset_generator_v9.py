"""
数据集生成器 V9 - Slot-Filling 架构

核心改进（从 V8 升级到 Slot-Filling）：
1. 移除 GNN 图谱输入，改为纯文本候选列表
2. 两轮对话架构：
   - 第一轮：System 给候选列表，User 给指令，Assistant 选择 API/工作流
   - 第二轮：System 给详细信息 + 槽位列表，Assistant 生成槽位值 JSON（不再生成完整 AMIS）
3. 统一选择格式：API: xxx / WORKFLOW: xxx / REJECT: xxx
4. workflow_step 保持单轮（已在工作流中，不需要选择）
5. 🔥 槽填充：AI 只生成动态文案（标题、描述、字段标签），规则生成器负责 AMIS 骨架

样本类型分布：
- 28% 直接 API 调用（两轮）
- 22% 工作流步骤（单轮，已在工作流中）
- 40% 对比样本（两轮，图谱包含 API + 工作流）
- 5% 拒绝响应-无关指令（单轮，直接生成拒绝 AMIS）
- 5% 拒绝响应-不匹配（单轮，直接生成拒绝 AMIS）
"""

import json
import random
import time
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from collections import defaultdict

# 导入组件
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from script.scene_loader import SceneLoader
from script.graph_builder_v2 import GraphContextBuilderV2
# 不再需要 AMIS 生成器，全部改用槽填充
# from script.amis_generator_v3 import AmisSchemaGeneratorV3, ChartSchemaGenerator


# ========== 🔥 语音识别同音字扰动配置（ASR Noise） ==========
ASR_HOMOPHONE_MAP = {
    "查询": ["查寻", "茶询", "察询"],
    "查看": ["茶看", "察看"],
    "添加": ["天加", "填加"],
    "删除": ["山除", "删出"],
    "修改": ["休改", "秀改"],
    "提交": ["题交", "提叫"],
    "预约": ["预越", "鱼约", "余约"],
    "预定": ["预订", "鱼定"],
    "订单": ["定单", "顶单", "钉单"],
    "登录": ["登陆", "等录"],
    "注册": ["住册", "驻册"],
    "支付": ["只付", "纸付", "之付"],
    "付款": ["附款", "负款"],
    "退款": ["腿款", "推款"],
    "取消": ["去消", "曲消"],
    "确认": ["却认", "确人"],
    "审核": ["审和", "身核"],
    "审批": ["审皮", "身批"],
    "统计": ["同计", "通计"],
    "分析": ["分西", "分希"],
    "导出": ["到出", "倒出"],
    "导入": ["到入", "倒入"],
    "上传": ["上川", "尚传"],
    "下载": ["下在", "夏载"],
    "客户": ["客护", "克户"],
    "用户": ["用护", "永户"],
    "员工": ["原工", "圆工"],
    "部门": ["不门", "布门"],
    "商品": ["上品", "尚品"],
    "库存": ["酷存", "苦存"],
    "发票": ["法票", "发飘"],
    "合同": ["和同", "河同"],
    "报表": ["包表", "报彪"],
    "账单": ["张单", "帐单"],
    "账户": ["张户", "帐户"],
    "密码": ["迷码", "米码"],
    "地址": ["地只", "低址"],
    "电话": ["店话", "典话"],
    "邮箱": ["油箱", "邮香"],
    "日期": ["日其", "日起"],
    "时间": ["实间", "石间"],
    "金额": ["今额", "斤额"],
    "数量": ["书量", "数亮"],
    "价格": ["家格", "假格"],
    "折扣": ["哲扣", "折口"],
    "优惠": ["有惠", "优会"],
    "医院": ["一院", "医元"],
    "医生": ["一生", "医声"],
    "挂号": ["瓜号", "挂好"],
    "处方": ["出方", "楚方"],
    "药品": ["要品", "耀品"],
    "酒店": ["九店", "久店"],
    "房间": ["方间", "房坚"],
    "入住": ["如住", "入驻"],
    "退房": ["腿房", "推房"],
    "餐厅": ["残厅", "蚕厅"],
    "菜单": ["才单", "彩单"],
    "外卖": ["外买", "歪卖"],
    "快递": ["快地", "筷递"],
    "物流": ["无流", "五流"],
    "仓库": ["苍库", "藏库"],
    "学生": ["学声", "雪生"],
    "课程": ["可程", "课成"],
    "成绩": ["成级", "城绩"],
    "考试": ["烤试", "考是"],
    "银行": ["音行", "银航"],
    "转账": ["专账", "转帐"],
    "贷款": ["带款", "代款"],
    "利息": ["力息", "立息"],
    "保险": ["包险", "宝险"],
    "理赔": ["里赔", "理陪"],
}

ASR_PERTURBATION_RATE = 0.15


class ASRNoisePerturbator:
    """语音识别噪声扰动器"""
    
    def __init__(self, homophone_map: Dict[str, List[str]] = None, perturbation_rate: float = 0.15):
        self.homophone_map = homophone_map or ASR_HOMOPHONE_MAP
        self.perturbation_rate = perturbation_rate
    
    def perturb(self, text: str, force: bool = False) -> str:
        if not force and random.random() > self.perturbation_rate:
            return text
        
        replaceable = [word for word in self.homophone_map.keys() if word in text]
        if not replaceable:
            return text
        
        num_replace = min(random.randint(1, 2), len(replaceable))
        words_to_replace = random.sample(replaceable, num_replace)
        
        result = text
        for word in words_to_replace:
            replacement = random.choice(self.homophone_map[word])
            result = result.replace(word, replacement, 1)
        
        return result


# ========== 指令模板配置 ==========
INSTRUCTION_CONFIG = {
    "action_prefixes": [
        "", "我想", "我要", "帮我", "请帮我", "麻烦", "能不能",
        "可以帮我", "我需要", "想要", "希望能", "请", "劳驾",
        "能否", "可否", "帮忙"
    ],
    "question_prefixes": [
        "请问怎么", "如何", "怎样", "怎么", "能告诉我怎么"
    ],
    "suffixes": [
        "", "一下", "吧", "可以吗", "行吗", "谢谢",
        "，谢谢", "，麻烦了", "，急用", "，帮帮忙", "好吗"
    ],
    "action_synonyms": {
        "查询": ["查询", "查看", "查一下", "看看", "了解", "获取", "查找", "搜索"],
        "添加": ["添加", "新增", "创建", "录入", "增加", "加入", "新建", "建立"],
        "修改": ["修改", "更新", "编辑", "变更", "调整", "改一下", "更改", "改动"],
        "删除": ["删除", "移除", "取消", "撤销", "去掉", "清除", "删掉", "移走"],
        "提交": ["提交", "申请", "发起", "办理", "处理", "递交", "呈交", "送交"],
        "预约": ["预约", "预定", "订", "约", "挂", "排", "安排", "预订"],
        "统计": ["统计", "汇总", "分析", "查看", "了解", "看看", "查询", "获取"],
    },
    "colloquial_templates": [
        "{action}{target}",
        "我想{action}{target}",
        "帮我{action}一下{target}",
        "{target}怎么{action}",
        "能帮我{action}{target}吗",
        "麻烦{action}{target}",
    ],
    "scenario_expressions": [
        "，急用", "，帮帮忙", "，麻烦了", "，谢谢"
    ],
    "admin_templates": [
        "查看{target}", "看看{target}", "查询{target}",
        "给我看{target}", "展示{target}", "显示{target}",
        "我要看{target}", "帮我查{target}", "统计{target}",
        "分析{target}", "汇总{target}", "报表{target}",
        "{target}是多少", "{target}怎么样", "今天的{target}",
        "本月{target}", "最近{target}", "{target}情况"
    ],
    "chart_templates": [
        "用图表展示{target}", "看{target}趋势", "{target}分布",
        "{target}占比", "{target}走势", "图表分析{target}"
    ]
}

WORKFLOW_STEP_INSTRUCTION_CONFIG = {
    "action_prefixes": [
        "", "我要", "帮我", "请", "现在", "开始", "继续",
        "我想", "请帮我", "麻烦", "好的", "可以", "那就"
    ],
    "suffixes": [
        "", "一下", "吧", "好吗", "可以吗", "，谢谢", "，继续"
    ],
    "node_type_actions": {
        "输入": ["输入", "填写", "录入", "提供", "写入", "填入", "键入"],
        "选择": ["选择", "选", "挑选", "选定", "确定", "指定", "选取"],
        "查询": ["查询", "查看", "查", "搜索", "检索", "获取", "看看"],
        "提交": ["提交", "确认", "发送", "递交", "完成", "执行", "办理"],
        "填写": ["填写", "填入", "录入", "输入", "写入", "补充", "完善"],
        "上传": ["上传", "提交", "添加", "传入", "导入"],
        "确认": ["确认", "核实", "验证", "检查", "审核"],
        "取消": ["取消", "撤销", "放弃", "终止", "退出"],
        "支付": ["支付", "付款", "结算", "缴费", "付费"],
        "预约": ["预约", "预定", "订", "约", "安排"],
    },
    "colloquial_templates": [
        "{name}",
        "我要{name}",
        "帮我{name}",
        "请{name}",
        "现在{name}",
        "开始{name}",
        "继续{name}",
        "{action}{target}",
        "我想{action}{target}",
        "帮我{action}一下{target}",
        "请帮我{action}{target}",
        "现在{action}{target}",
        "好的，{name}",
        "可以，{name}",
        "那就{name}吧",
    ],
    "purpose_templates": [
        "{purpose}",
        "我要{purpose}",
        "帮我{purpose}",
        "请{purpose}",
        "现在{purpose}",
    ],
    "scenario_expressions": [
        "，继续下一步", "，谢谢", "，麻烦了", ""
    ]
}


class EnhancedInstructionGenerator:
    """增强版指令生成器"""
    
    def __init__(self):
        self.config = INSTRUCTION_CONFIG
    
    def generate_variants(self, api: Dict, count: int = 30) -> List[str]:
        """
        生成API指令变体
        
        优先使用scene中定义的instruction_variants，
        如果没有则使用原有的生成逻辑
        """
        variants = set()
        
        # 🔥 优先使用scene中定义的指令变体
        if "instruction_variants" in api and api["instruction_variants"]:
            predefined_variants = api["instruction_variants"]
            variants.update(predefined_variants)
            print(f"   使用预定义指令变体: {api.get('id', 'unknown')} - {len(predefined_variants)}个")
        
        desc = api.get("desc", "")
        name = api.get("name", desc)
        is_chart = api.get("response_type") == "chart"
        
        # 添加基础变体
        variants.add(desc)
        variants.add(name)
        
        # 如果预定义变体不够，继续生成
        if len(variants) < count:
            for prefix in self.config["action_prefixes"]:
                if prefix:
                    variants.add(f"{prefix}{desc}")
                    variants.add(f"{prefix}{name}")
            
            for suffix in self.config["suffixes"]:
                if suffix:
                    variants.add(f"{desc}{suffix}")
            
            for action, synonyms in self.config["action_synonyms"].items():
                if action in desc:
                    for syn in synonyms:
                        variants.add(desc.replace(action, syn))
            
            action_word = self._extract_action(desc)
            target = desc.replace(action_word, "").strip() if action_word else desc
            for template in self.config["colloquial_templates"]:
                try:
                    variants.add(template.format(action=action_word or "查询", target=target or desc))
                except:
                    pass
            
            for expr in self.config["scenario_expressions"]:
                variants.add(f"{desc}{expr}")
            
            if is_chart:
                for template in self.config["admin_templates"] + self.config["chart_templates"]:
                    try:
                        variants.add(template.format(target=name))
                    except:
                        pass
            
            base_variants = list(variants)[:10]
            for base in base_variants:
                for prefix in random.sample(self.config["action_prefixes"], min(3, len(self.config["action_prefixes"]))):
                    if prefix and not self._has_prefix(base):
                        variants.add(f"{prefix}{base}")
        
        variants = [v for v in variants if v and len(v.strip()) >= 2]
        variants = list(set(variants))
        random.shuffle(variants)
        return variants[:count]
    
    def _extract_action(self, desc: str) -> str:
        for action in self.config["action_synonyms"].keys():
            if action in desc:
                return action
        return ""
    
    def _has_prefix(self, text: str) -> bool:
        all_prefixes = self.config["action_prefixes"] + self.config["question_prefixes"]
        return any(text.startswith(p) for p in all_prefixes if p)


class WorkflowStepInstructionGenerator:
    """工作流步骤指令生成器"""
    
    def __init__(self):
        self.config = WORKFLOW_STEP_INSTRUCTION_CONFIG
    
    def generate_variants(self, node: Dict, workflow_name: str = "", count: int = 25) -> List[str]:
        """
        生成工作流节点指令变体
        
        优先使用scene中定义的instruction_variants
        """
        variants = set()
        
        # 🔥 优先使用预定义的指令变体
        if "instruction_variants" in node and node["instruction_variants"]:
            predefined_variants = node["instruction_variants"]
            variants.update(predefined_variants)
        
        node_name = node.get("name", "")
        ai_inst = node.get("ai_instructions", {})
        purpose = ai_inst.get("purpose", "")
        user_message = ai_inst.get("user_message", "")
        action = ai_inst.get("action", "")
        
        if node_name:
            variants.add(node_name)
        if purpose:
            variants.add(purpose)
        if user_message:
            variants.add(user_message)
        if action:
            variants.add(action)
        
        # 如果预定义变体不够，继续生成
        if len(variants) < count:
            bases = [b for b in [node_name, purpose] if b]
            for base in bases:
                for prefix in self.config["action_prefixes"]:
                    if prefix:
                        variants.add(f"{prefix}{base}")
            
            for base in bases:
                for suffix in self.config["suffixes"]:
                    if suffix:
                        variants.add(f"{base}{suffix}")
            
            action_word = self._extract_action(node_name)
            synonyms = []  # 初始化synonyms
            if action_word:
                target = node_name.replace(action_word, "").strip()
                synonyms = self.config["node_type_actions"].get(action_word, [])
            
            for syn in synonyms:
                if syn != action_word:
                    variants.add(f"{syn}{target}")
                    variants.add(f"我要{syn}{target}")
                    variants.add(f"帮我{syn}{target}")
                    variants.add(f"请{syn}{target}")
        
        for template in self.config["colloquial_templates"]:
            try:
                if "{name}" in template:
                    variants.add(template.format(name=node_name))
                elif "{action}" in template and "{target}" in template:
                    if action_word:
                        target = node_name.replace(action_word, "").strip()
                        variants.add(template.format(action=action_word, target=target or "信息"))
            except:
                pass
        
        if purpose:
            for template in self.config["purpose_templates"]:
                try:
                    variants.add(template.format(purpose=purpose))
                except:
                    pass
        
        for base in bases[:2]:
            for expr in self.config["scenario_expressions"]:
                if expr:
                    variants.add(f"{base}{expr}")
        
        base_list = list(variants)[:8]
        for base in base_list:
            for prefix in random.sample(self.config["action_prefixes"], min(3, len(self.config["action_prefixes"]))):
                if prefix and not self._has_prefix(base):
                    variants.add(f"{prefix}{base}")
        
        if workflow_name and node_name:
            variants.add(f"继续{workflow_name}，{node_name}")
            variants.add(f"{workflow_name}的{node_name}")
        
        variants = [v for v in variants if v and len(v.strip()) >= 2]
        variants = list(set(variants))
        random.shuffle(variants)
        return variants[:count]
    
    def _extract_action(self, text: str) -> str:
        for action in self.config["node_type_actions"].keys():
            if action in text:
                return action
        return ""
    
    def _has_prefix(self, text: str) -> bool:
        return any(text.startswith(p) for p in self.config["action_prefixes"] if p)


class SmartSamplingStrategy:
    """智能采样策略"""
    
    def __init__(self):
        self.used_variants: Dict[str, Set[str]] = defaultdict(set)
        self.repeat_count: Dict[str, int] = defaultdict(int)
    
    def sample(self, api_id: str, variants: List[str]) -> str:
        if not variants:
            return "查询信息"
        
        unused = [v for v in variants if v not in self.used_variants[api_id]]
        
        if unused:
            selected = random.choice(unused)
            self.used_variants[api_id].add(selected)
            return selected
        else:
            self.repeat_count[api_id] += 1
            return random.choice(variants)
    
    def get_statistics(self) -> Dict:
        return {
            "total_apis": len(self.used_variants),
            "total_used_variants": sum(len(v) for v in self.used_variants.values()),
            "total_repeats": sum(self.repeat_count.values()),
            "apis_with_repeats": len([k for k, v in self.repeat_count.items() if v > 0])
        }
    
    def reset(self):
        self.used_variants.clear()
        self.repeat_count.clear()



class DatasetGeneratorV9:
    """数据集生成器 V9 - Slot-Filling 架构"""
    
    def __init__(self, enable_asr_noise: bool = True):
        self.scene_loader = SceneLoader()
        self.graph_builder = GraphContextBuilderV2(self.scene_loader)
        # 不再需要 AMIS 生成器，改用槽填充
        # self.amis_generator = AmisSchemaGeneratorV3()
        # self.chart_generator = ChartSchemaGenerator()
        self.instruction_generator = EnhancedInstructionGenerator()
        self.workflow_step_instruction_generator = WorkflowStepInstructionGenerator()
        self.sampling_strategy = SmartSamplingStrategy()
        self.workflow_step_sampling_strategy = SmartSamplingStrategy()
        
        self.enable_asr_noise = enable_asr_noise
        self.asr_perturbator = ASRNoisePerturbator(
            homophone_map=ASR_HOMOPHONE_MAP,
            perturbation_rate=ASR_PERTURBATION_RATE
        )
        
        self.domains = self.scene_loader.get_all_domains()
        self.seen_samples: Set[str] = set()
        
        # 🔥 自动构建字段映射表（从场景模板中提取）
        self.field_label_map = self._build_field_label_map()
        print(f"📋 自动构建字段映射表: {len(self.field_label_map)} 个字段")
        
        self._prebuild_api_instructions()
        self._build_irrelevant_instructions()
        self._build_help_instructions()
        self._prebuild_workflow_step_instructions()
        self._build_workflow_only_api_mapping()  # 🔥 构建 workflow_only API 到工作流的映射
        
        if self.enable_asr_noise:
            print(f"🎤 ASR 噪声扰动: 启用 (扰动率 {ASR_PERTURBATION_RATE*100:.0f}%)")
    
    def _build_field_label_map(self) -> Dict[str, str]:
        """
        自动从场景模板中提取字段名到中文标签的映射
        
        提取来源：
        1. API 参数的 description
        2. 工作流输入/输出的 displayName 或 description
        3. 节点配置中的字段 label
        
        Returns:
            字段名 -> 中文标签的映射字典
        """
        field_map = {}
        
        for domain in self.domains:
            # 1. 从 API 中提取
            apis = self.scene_loader.get_domain_apis(domain)
            for api in apis:
                # API 请求参数
                for param in api.get("request", []):
                    name = param.get("name")
                    label = param.get("label") or param.get("description") or param.get("displayName")
                    if name and label and self._is_chinese(label):
                        # 只保留中文标签，去掉多余描述
                        clean_label = self._extract_chinese_label(label)
                        if clean_label:
                            field_map[name] = clean_label
                
                # API 响应字段
                for resp in api.get("response", []):
                    name = resp.get("name")
                    label = resp.get("desc") or resp.get("description") or resp.get("displayName")
                    if name and label and self._is_chinese(label):
                        clean_label = self._extract_chinese_label(label)
                        if clean_label:
                            field_map[name] = clean_label
                
                # API parameters（路径参数等）
                for param in api.get("parameters", []):
                    name = param.get("name")
                    label = param.get("description") or param.get("label")
                    if name and label and self._is_chinese(label):
                        clean_label = self._extract_chinese_label(label)
                        if clean_label:
                            field_map[name] = clean_label
            
            # 2. 从工作流中提取
            workflows = self.scene_loader.get_domain_workflows(domain)
            for workflow in workflows:
                # 工作流输入
                for input_field in workflow.get("inputs", []):
                    name = input_field.get("name")
                    label = input_field.get("displayName") or input_field.get("description")
                    if name and label and self._is_chinese(label):
                        clean_label = self._extract_chinese_label(label)
                        if clean_label:
                            field_map[name] = clean_label
                
                # 工作流节点
                for node in workflow.get("nodes", []):
                    # 节点输出
                    for output in node.get("outputs", []):
                        name = output.get("name")
                        label = output.get("description") or output.get("displayName")
                        if name and label and self._is_chinese(label):
                            clean_label = self._extract_chinese_label(label)
                            if clean_label:
                                field_map[name] = clean_label
                    
                    # 节点配置中的参数
                    config = node.get("config", {})
                    parameters = config.get("parameters", {})
                    if isinstance(parameters, dict):
                        for param_name, param_config in parameters.items():
                            if isinstance(param_config, dict):
                                label = param_config.get("label") or param_config.get("description")
                                if label and self._is_chinese(label):
                                    clean_label = self._extract_chinese_label(label)
                                    if clean_label:
                                        field_map[param_name] = clean_label
        
        return field_map
    
    def _is_chinese(self, text: str) -> bool:
        """判断文本是否包含中文"""
        if not text:
            return False
        return any('\u4e00' <= char <= '\u9fff' for char in text)
    
    def _extract_chinese_label(self, text: str) -> str:
        """
        从描述文本中提取简洁的中文标签
        
        例如：
        - "需要退订的车票ID" -> "车票ID"
        - "乘客的身份证号码" -> "身份证号"
        - "订单号" -> "订单号"
        """
        if not text:
            return ""
        
        # 去掉常见的前缀词
        prefixes = ["需要", "请输入", "请填写", "请选择", "用户的", "乘客的", "客户的", "订单的"]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):]
        
        # 限制长度（2-6 字）
        if len(text) > 6:
            # 尝试提取关键词
            keywords = ["ID", "号", "名称", "姓名", "日期", "时间", "金额", "数量", "价格", "状态"]
            for keyword in keywords:
                if keyword in text:
                    # 找到关键词前面的主体词
                    idx = text.index(keyword)
                    if idx > 0:
                        return text[max(0, idx-4):idx+len(keyword)]
            # 如果没有关键词，取前6个字
            text = text[:6]
        
        return text.strip()

    
    def _prebuild_api_instructions(self):
        """预生成所有 API 的指令变体"""
        self.api_instructions = {}
        self.standalone_api_ids = set()
        total_variants = 0
        chart_api_count = 0
        workflow_only_count = 0
        
        for domain in self.domains:
            apis = self.scene_loader.get_domain_apis(domain)
            for api in apis:
                api_id = api["id"]
                is_workflow_only = api.get("workflow_only", False)
                
                variants = self.instruction_generator.generate_variants(api, count=35)
                self.api_instructions[api_id] = variants
                total_variants += len(variants)
                
                if api.get("response_type") == "chart":
                    chart_api_count += 1
                
                if is_workflow_only:
                    workflow_only_count += 1
                else:
                    self.standalone_api_ids.add(api_id)
        
        print(f"📝 API 指令变体: {len(self.api_instructions)} 个 API, {total_variants} 种指令")
        print(f"   其中图表类 API: {chart_api_count} 个")
        print(f"   🔒 工作流专用 API: {workflow_only_count} 个")
        print(f"   ✅ 独立 API: {len(self.standalone_api_ids)} 个")
    
    def _generate_slot_values_for_api(self, api: Dict, context_data: Dict = None) -> Dict:
        """为 API 生成槽位值（替代完整 AMIS Schema）"""
        desc = api.get("desc", "")
        path = api.get("path", "")
        method = api.get("method", "GET")
        fields = [p.get("name") for p in api.get("request", [])[:5]]
        
        # 🔥 填充 URL 中的路径参数（从上下文中获取）
        filled_url = self._fill_url_params(path, context_data or {})
        
        slot_values = {
            "page_title": desc[:6],
            "user_message": f"请填写{desc}所需信息",
            "submit_button_text": "提交",
            "api_url": filled_url,  # 🔥 新增：已填充的 API URL
            "api_method": method    # 🔥 新增：API 方法
        }
        
        for field in fields:
            slot_values[f"field_label_{field}"] = self._infer_field_label(field)
        
        return slot_values
    
    def _generate_slot_values_for_workflow(self, workflow: Dict, first_node: Dict) -> Dict:
        """为工作流生成槽位值（替代完整 AMIS Schema）"""
        name = workflow.get("name", "")
        
        # 提取第一个节点的字段
        parameters = first_node.get("config", {}).get("parameters", {})
        fields = list(parameters.keys())[:5]
        
        # 🔥 获取第一个节点的 API 信息（如果是 api_call 节点）
        api_url = ""
        api_method = "POST"
        if first_node.get("type") == "api_call":
            config = first_node.get("config", {})
            api_url = config.get("api_endpoint", "")
            api_method = config.get("method", "POST")
        
        slot_values = {
            "page_title": name[:6],
            "user_message": f"请填写{name}所需信息",
            "submit_button_text": "下一步",
            "reset_button_text": "重置"
        }
        
        # 🔥 新增：API URL 和方法（如果有）
        if api_url:
            slot_values["api_url"] = self._fill_url_params(api_url, {})
            slot_values["api_method"] = api_method
        
        for field in fields:
            slot_values[f"field_label_{field}"] = self._infer_field_label(field)
        
        return slot_values
    
    def _infer_field_label(self, field_name: str) -> str:
        """
        从字段名推断中文标签
        
        优先使用自动构建的映射表，如果没有则使用手动维护的映射表
        """
        # 1. 优先使用自动构建的映射表
        if field_name in self.field_label_map:
            return self.field_label_map[field_name]
        
        # 2. 使用手动维护的映射表（兜底）
        label_map = {
            "order_id": "订单号",
            "booking_id": "订单号",
            "train_number": "车次",
            "departure_station": "出发站",
            "arrival_station": "到达站",
            "departure_date": "出发日期",
            "departure_time": "出发时间",
            "arrival_time": "到达时间",
            "passenger_name": "乘客姓名",
            "passenger_id": "乘客ID",
            "id_number": "身份证号",
            "seat_type": "座位类型",
            "seat_number": "座位号",
            "product_id": "商品ID",
            "product_name": "商品名称",
            "quantity": "数量",
            "price": "价格",
            "customer_name": "客户姓名",
            "customer_id": "客户ID",
            "patient_name": "患者姓名",
            "patient_id": "患者ID",
            "doctor_name": "医生姓名",
            "doctor_id": "医生ID",
            "appointment_date": "预约日期",
            "appointment_time": "预约时间",
            "hotel_name": "酒店名称",
            "hotel_id": "酒店ID",
            "room_type": "房型",
            "room_number": "房间号",
            "check_in_date": "入住日期",
            "check_out_date": "退房日期",
            "status": "状态",
            "phone": "手机号",
            "email": "邮箱",
            "address": "地址",
            "name": "姓名",
            "id_card": "身份证号",
            "date": "日期",
            "time": "时间",
            "amount": "金额",
            "total_amount": "总金额",
            "min_amount": "最小金额",
            "max_amount": "最大金额",
            "reason": "原因",
            "description": "描述",
            "comment": "备注",
            "remark": "备注",
            "user_id": "用户ID",
            "username": "用户名",
            "password": "密码",
            "created_at": "创建时间",
            "updated_at": "更新时间",
            # 🔥 新增：教育领域
            "exam_id": "考试ID",
            "student_id": "学生ID",
            "course_id": "课程ID",
            "teacher_id": "教师ID",
            "class_id": "班级ID",
            "grade": "成绩",
            "score": "分数",
            # 🔥 新增：电商领域
            "category": "分类",
            "stock": "库存",
            "sku_id": "商品SKU",
            "cart_id": "购物车ID",
            "coupon_id": "优惠券ID",
            "refund_id": "退款ID",
            # 🔥 新增：物流领域
            "tracking_no": "运单号",
            "sender_id": "寄件人ID",
            "receiver_id": "收件人ID",
            "weight": "重量",
            "package_id": "包裹ID",
            "from_city": "出发城市",
            "to_city": "到达城市",
            "from_address": "出发地址",
            "to_address": "到达地址",
            "service_type": "服务类型",
            "courier_id": "快递员ID",
            # 🔥 新增：财务领域
            "invoice_id": "发票ID",
            "invoice_no": "发票号",
            "expense_id": "费用ID",
            "budget_id": "预算ID",
            "reimbursement_id": "报销ID",
            "payment_id": "付款ID",
            # 🔥 新增：银行领域
            "account_id": "账户ID",
            "card_id": "卡号",
            "loan_id": "贷款ID",
            "transaction_id": "交易ID",
            "balance": "余额",
            # 🔥 新增：人力资源
            "employee_id": "员工ID",
            "emp_id": "员工ID",
            "department": "部门",
            "position": "职位",
            "salary": "薪资",
            "leave_id": "请假ID",
            "overtime_id": "加班单号",
            "action": "操作",
            "approval_status": "审批状态",
            "transfer_id": "调动ID",
            "month": "月份",
            "week": "周次",
            # 🔥 新增：餐饮领域
            "restaurant_id": "餐厅ID",
            "menu_id": "菜单ID",
            "table_id": "桌号",
            "rider_id": "骑手ID",
            "reservation_id": "预订ID",
            # 🔥 新增：政务领域
            "application_id": "申请ID",
            "license_id": "证照ID",
            "appointment_id": "预约ID",
            "complaint_id": "投诉ID",
            # 🔥 新增：房产领域
            "house_id": "房源ID",
            "contract_id": "合同ID",
            "repair_id": "报修ID",
            "viewing_id": "看房ID",
            # 🔥 新增：其他常见字段
            "city": "城市",
            "star": "星级",
            "loan_type": "贷款类型",
            "task_type": "任务类型",
            "year": "年份"
        }
        return label_map.get(field_name, field_name)
    
    def _fill_url_params(self, url: str, context_data: Dict) -> str:
        """
        填充 URL 中的路径参数（从上下文中获取）
        
        例如：
        - URL: /api/orders/{order_id}/items
        - Context: {"order_id": "12345", "order": "12345"}
        - Result: /api/orders/12345/items  或  /api/orders/${order_id}/items
        
        Args:
            url: API URL 模板（如 /api/orders/{order_id}/items）
            context_data: 上下文数据
        
        Returns:
            填充后的 URL
        """
        if not url or not context_data:
            return url
        
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
        
        def _find_context_key(param_name: str) -> Optional[Tuple[str, Any]]:
            if param_name in context_data:
                return param_name, context_data[param_name]
            
            if param_name.endswith("_id"):
                base_name = param_name[:-3]
                if base_name in context_data:
                    return base_name, context_data[base_name]
                
                plural_key = f"{base_name}s"
                if plural_key in context_data and isinstance(context_data[plural_key], list):
                    found_id = _first_item_id(context_data[plural_key])
                    if found_id is not None:
                        context_data[param_name] = found_id
                        return param_name, found_id
                
                list_key = f"{base_name}_list"
                if list_key in context_data and isinstance(context_data[list_key], list):
                    found_id = _first_item_id(context_data[list_key])
                    if found_id is not None:
                        context_data[param_name] = found_id
                        return param_name, found_id
            
            if f"{param_name}_id" in context_data:
                return f"{param_name}_id", context_data[f"{param_name}_id"]

            # param 为 "id" 时，尝试匹配上下文中唯一的 *_id 字段
            if param_name == "id":
                id_keys = [k for k, v in context_data.items() if k.endswith("_id") and isinstance(v, (str, int, float, bool))]
                if len(id_keys) == 1:
                    key = id_keys[0]
                    return key, context_data[key]
            
            if param_name in context_data and isinstance(context_data[param_name], dict):
                nested = context_data[param_name]
                if "id" in nested:
                    context_data[f"{param_name}_id"] = nested["id"]
                    return f"{param_name}_id", nested["id"]
            
            return None
        
        # 查找所有的路径参数 {param_name}
        params = re.findall(r'\{(\w+)\}', url)
        
        for param in params:
            # 尝试从上下文中查找匹配的值
            match = _find_context_key(param)
            if match:
                context_key, value = match
                if isinstance(value, (str, int, float, bool)):
                    url = url.replace(f"{{{param}}}", str(value))
        
        # 将剩余的路径参数替换为 ${param}（用户输入）
        url = re.sub(r'(?<!\$)\{(\w+)\}', r'${\1}', url)
        
        return url
    
    def _generate_slot_values_for_workflow_step(self, node: Dict, context_data: Dict = None) -> Dict:
        """为工作流步骤节点生成槽位值"""
        node_name = node.get("name", "")
        node_type = node.get("type", "")
        
        # 提取节点的字段
        config = node.get("config", {})
        parameters = config.get("parameters", {})
        
        # 过滤掉上下文中已有的字段
        context_data = context_data or {}
        fields = [k for k in parameters.keys() if k not in context_data][:5]
        
        slot_values = {
            "page_title": node_name[:6] if node_name else "操作",
            "user_message": f"请填写{node_name}所需信息" if node_name else "请填写信息",
            "submit_button_text": "提交"
        }
        
        # 🔥 新增：API URL 和方法（如果是 api_call 节点）
        if node_type == "api_call":
            api_url = config.get("api_endpoint", "")
            api_method = config.get("method", "POST")
            
            # 填充 URL 中的路径参数（从上下文中获取）
            filled_url = self._fill_url_params(api_url, context_data)
            
            slot_values["api_url"] = filled_url
            slot_values["api_method"] = api_method
        
        for field in fields:
            slot_values[f"field_label_{field}"] = self._infer_field_label(field)
        
        return slot_values
    
    def _prebuild_workflow_step_instructions(self):
        """预生成工作流步骤指令"""
        self.workflow_step_instructions = {}
        self.workflow_instructions = {}
        
        for domain in self.domains:
            workflows = self.scene_loader.get_domain_workflows(domain)
            for workflow in workflows:
                wf_id = workflow.get("id", "")
                wf_name = workflow.get("name", "")
                
                intents = workflow.get("user_intents", [])
                keywords = workflow.get("trigger_keywords", [])
                name = workflow.get("name", "")
                variants = set(intents + keywords)
                variants.add(name)
                for prefix in ["我想", "我要", "帮我", "请帮我", "麻烦", "能不能", "可以帮我"]:
                    variants.add(f"{prefix}{name}")
                    for intent in intents[:3]:
                        variants.add(f"{prefix}{intent}")
                for suffix in ["一下", "吧", "可以吗", "，谢谢"]:
                    variants.add(f"{name}{suffix}")
                self.workflow_instructions[wf_id] = [v for v in variants if v]
                
                nodes = workflow.get("nodes", [])
                for node in nodes:
                    node_type = node.get("type", "")
                    if node_type == "api_call":
                        node_id = node.get("id", "")
                        key = f"{wf_id}_{node_id}"
                        node_variants = self.workflow_step_instruction_generator.generate_variants(
                            node, workflow_name=wf_name, count=25
                        )
                        self.workflow_step_instructions[key] = node_variants
        
        print(f"📝 工作流入口指令: {len(self.workflow_instructions)} 个工作流")
        print(f"📝 工作流步骤指令: {len(self.workflow_step_instructions)} 个节点")
    
    def _build_irrelevant_instructions(self):
        """构建无关指令列表"""
        chat = [
            "今天天气怎么样", "明天会下雨吗", "现在几点了", "今天星期几",
            "给我讲个笑话", "讲个故事", "说个冷笑话", "讲个鬼故事",
            "你好", "早上好", "晚安", "再见", "谢谢", "感谢", "辛苦了",
        ]
        knowledge = [
            "1+1等于几", "地球有多大", "太阳系有几颗行星",
            "解释一下量子力学", "什么是相对论", "黑洞是什么",
            "中国有多少人口", "世界上最高的山是什么",
        ]
        creative = [
            "帮我写一首诗", "写一篇作文", "写一段代码",
            "帮我翻译一下", "帮我做数学题", "推荐一部电影",
        ]
        life = [
            "帮我叫个外卖", "附近有什么好吃的", "帮我打车",
            "帮我订机票", "帮我充话费", "帮我找工作",
        ]
        nonsense = [
            "啊", "哦", "嗯", "呃", "什么", "啥", "为啥",
            "不知道", "随便", "都行", "无所谓", "算了",
            "好的", "行", "可以", "没问题", "OK",
            "哈哈哈", "笑死", "无语", "醉了", "服气",
        ]
        
        self.irrelevant_instructions = list(set(chat + knowledge + creative + life + nonsense))
        print(f"📝 无关指令数量: {len(self.irrelevant_instructions)}")

    def _build_help_instructions(self):
        """构建帮助/能力询问指令列表"""
        help_instructions = [
            "你是谁",
            "你叫什么名字",
            "你是AI吗",
            "你能做什么",
            "你可以干啥",
            "你可以做什么",
            "你现在能帮我干啥",
            "你现在能帮我做什么",
            "你可以帮我做什么",
            "你能帮我做什么",
            "能帮我什么",
            "功能有哪些",
            "帮助",
            "help",
            "?",
            "？"
        ]
        self.help_instructions = list(set(help_instructions))
        print(f"📝 帮助指令数量: {len(self.help_instructions)}")
    
    def _build_workflow_only_api_mapping(self):
        """
        🔥 构建 workflow_only API 到工作流的映射
        
        遍历所有工作流的节点，找到每个 workflow_only API 所属的工作流
        """
        self.workflow_only_api_to_workflow: Dict[str, Dict] = {}  # api_id -> workflow
        self.workflow_only_api_to_first_node: Dict[str, Dict] = {}  # api_id -> first_node
        
        for domain in self.domains:
            workflows = self.scene_loader.get_domain_workflows(domain)
            for workflow in workflows:
                wf_id = workflow.get("id", "")
                nodes = workflow.get("nodes", [])
                
                # 找到第一个非 start 节点
                first_node = None
                for node in nodes:
                    if node.get("type") not in ("start", "end"):
                        first_node = node
                        break
                
                # 遍历所有节点，找到引用的 API
                for node in nodes:
                    if node.get("type") == "api_call":
                        config = node.get("config", {})
                        api_id = config.get("api_id", "")
                        
                        if api_id:
                            # 检查这个 API 是否是 workflow_only
                            api = self.scene_loader.get_api_by_id(api_id)
                            if api and api.get("workflow_only", False):
                                # 记录映射（如果同一个 API 在多个工作流中，取第一个）
                                if api_id not in self.workflow_only_api_to_workflow:
                                    self.workflow_only_api_to_workflow[api_id] = workflow
                                    self.workflow_only_api_to_first_node[api_id] = first_node
        
        print(f"📝 workflow_only API 映射: {len(self.workflow_only_api_to_workflow)} 个 API 关联到工作流")
    
    def _get_sample_hash(self, sample: Dict) -> str:
        content = json.dumps(sample["messages"], ensure_ascii=False, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_duplicate(self, sample: Dict) -> bool:
        sample_hash = self._get_sample_hash(sample)
        if sample_hash in self.seen_samples:
            return True
        self.seen_samples.add(sample_hash)
        return False
    
    def generate_dataset(self, total_samples: int = 5000, output_path: str = None) -> List[Dict]:
        """生成完整数据集（Slot-Filling 架构）"""
        samples = []
        self.seen_samples.clear()
        self.sampling_strategy.reset()
        self.workflow_step_sampling_strategy.reset()
        
        api_count = int(total_samples * 0.28)
        workflow_step_count = int(total_samples * 0.22)
        contrastive_count = int(total_samples * 0.40)
        help_count = int(total_samples * 0.02)
        rejection_empty_count = int(total_samples * 0.04)
        rejection_mismatch_count = total_samples - api_count - workflow_step_count - contrastive_count - help_count - rejection_empty_count
        
        print(f"📊 生成数据集（Slot-Filling 架构）: {total_samples} 条")
        print(f"   - 直接 API 调用（两轮，槽填充）: {api_count} (28%)")
        print(f"   - 工作流步骤（单轮，槽填充）: {workflow_step_count} (22%)")
        print(f"   - 对比样本（两轮，槽填充）: {contrastive_count} (40%)")
        print(f"   - 帮助意图(单轮，输出HELP): {help_count} (2%)")
        print(f"   - 拒绝响应(无关指令，单轮，输出REJECT): {rejection_empty_count} (4%)")
        print(f"   - 拒绝响应(不匹配，单轮，输出REJECT): {rejection_mismatch_count} (4%)")
        
        print("\n🔄 生成直接 API 调用样本...")
        samples.extend(self._generate_samples_with_retry(
            self._generate_api_only_sample, api_count, "api_only"
        ))
        
        print("\n🔄 生成工作流步骤样本...")
        samples.extend(self._generate_samples_with_retry(
            self._generate_workflow_step_sample, workflow_step_count, "workflow_step"
        ))
        
        print("\n🔄 生成对比样本...")
        samples.extend(self._generate_samples_with_retry(
            self._generate_contrastive_sample, contrastive_count, "contrastive"
        ))

        print("\n生成帮助意图样本...")
        samples.extend(self._generate_samples_with_retry(
            self._generate_help_sample, help_count, "help_intent"
        ))
        
        print("\n🔄 生成拒绝响应样本(无关指令)...")
        samples.extend(self._generate_samples_with_retry(
            self._generate_rejection_sample, rejection_empty_count, "rejection"
        ))
        
        print("\n🔄 生成拒绝响应样本(不匹配)...")
        samples.extend(self._generate_samples_with_retry(
            self._generate_mismatch_rejection_sample, rejection_mismatch_count, "rejection_mismatch"
        ))
        
        random.shuffle(samples)
        self._validate_and_report(samples)
        
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                for sample in samples:
                    f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            print(f"\n✅ 数据集已保存到: {output_path}")
        
        return samples
    
    def _generate_samples_with_retry(self, generator_func, target_count: int, sample_type: str, max_retries: int = 3) -> List[Dict]:
        """带去重和重试机制的样本生成"""
        samples = []
        attempts = 0
        max_attempts = target_count * max_retries
        
        while len(samples) < target_count and attempts < max_attempts:
            sample = generator_func()
            attempts += 1
            
            if sample and not self._is_duplicate(sample):
                samples.append(sample)
                
                if len(samples) % 500 == 0:
                    print(f"   已生成 {len(samples)}/{target_count} (尝试 {attempts} 次)")
        
        if len(samples) < target_count:
            print(f"   ⚠️ {sample_type}: 只生成了 {len(samples)}/{target_count} 个唯一样本")
        
        return samples


    # ========== 🔥 核心：两轮对话样本生成 ==========
    
    def _generate_api_only_sample(self) -> Optional[Dict]:
        """
        生成直接 API 调用样本（两轮对话 - Slot-Filling）
        
        第一轮：System 给候选列表，User 给指令，Assistant 选择 API
        第二轮：System 给 API 详情 + 槽位列表，Assistant 生成槽位值 JSON
        """
        domain = random.choice(self.domains)
        apis = self.scene_loader.get_domain_apis(domain)
        workflows = self.scene_loader.get_domain_workflows(domain)
        
        if not apis:
            return None
        
        # 排除工作流专用 API
        standalone_apis = [api for api in apis if not api.get("workflow_only", False)]
        if not standalone_apis:
            return None
        
        target_api = random.choice(standalone_apis)
        api_id = target_api["id"]
        is_chart = target_api.get("response_type") == "chart"
        
        # 获取指令
        if api_id in self.api_instructions:
            instruction = self.sampling_strategy.sample(api_id, self.api_instructions[api_id])
        else:
            instruction = f"查询{target_api.get('desc', '信息')}"
        
        if self.enable_asr_noise:
            instruction = self.asr_perturbator.perturb(instruction)
        
        # 构建候选列表（目标 API + 干扰 API + 工作流）
        other_apis = [a for a in standalone_apis if a["id"] != api_id]
        num_noise_apis = random.randint(12, 20)  # 扩大：模拟 BGE 召回 15-25 个
        noise_apis = random.sample(other_apis, min(num_noise_apis, len(other_apis)))
        
        num_noise_wfs = random.randint(3, 6)  # 扩大：模拟召回 4-8 个工作流
        noise_wfs = random.sample(workflows, min(num_noise_wfs, len(workflows))) if workflows else []
        
        # 生成槽位值（替代完整 AMIS Schema）
        slot_values = self._generate_slot_values_for_api(target_api)
        
        return self._build_two_round_api_sample(
            domain=domain,
            instruction=instruction,
            target_api=target_api,
            noise_apis=noise_apis,
            noise_workflows=noise_wfs,
            slot_values=slot_values,
            sample_type="api_only"
        )
    
    def _generate_contrastive_sample(self) -> Optional[Dict]:
        """
        生成对比样本（两轮对话 - Slot-Filling）
        
        样本类型：
        A. 用户明确想走工作流 → 选择 WORKFLOW
        B. 用户只想简单查询 → 选择 API
        C. 用户意图匹配工作流专用 API → 选择 WORKFLOW
        """
        domain = random.choice(self.domains)
        workflows = self.scene_loader.get_domain_workflows(domain)
        apis = self.scene_loader.get_domain_apis(domain)
        
        if not workflows or not apis:
            return None
        
        workflow = random.choice(workflows)
        db_workflow_id = workflow["id"]
        
        # 找到第一个节点
        nodes = workflow.get("nodes", [])
        first_node = None
        for node in nodes:
            if node.get("type") not in ("start", "end"):
                first_node = node
                break
        
        if not first_node:
            return None
        
        standalone_apis = [api for api in apis if not api.get("workflow_only", False)]
        workflow_only_apis = [
            api for api in apis
            if api.get("workflow_only", False) and api.get("id") in self.workflow_only_api_to_workflow
        ]
        
        # 构建候选列表
        num_noise_apis = random.randint(12, 20)  # 扩大召回
        noise_apis = random.sample(apis, min(num_noise_apis, len(apis)))
        
        other_wfs = [wf for wf in workflows if wf["id"] != db_workflow_id]
        num_noise_wfs = random.randint(3, 6)  # 扩大召回
        noise_wfs = random.sample(other_wfs, min(num_noise_wfs, len(other_wfs))) if other_wfs else []
        
        # 随机决定生成哪种样本
        sample_type_rand = random.random()
        
        if sample_type_rand < 0.35:
            # 样本类型 A：用户明确想走工作流
            wf_id = workflow["id"]
            if wf_id in self.workflow_instructions and self.workflow_instructions[wf_id]:
                instruction = random.choice(self.workflow_instructions[wf_id])
            else:
                instruction = f"我要{workflow.get('name', '办理业务')}"
            
            if self.enable_asr_noise:
                instruction = self.asr_perturbator.perturb(instruction)
            
            # 生成槽位值（替代完整 AMIS Schema）
            slot_values = self._generate_slot_values_for_workflow(workflow, first_node)
            
            return self._build_two_round_workflow_sample(
                domain=domain,
                instruction=instruction,
                target_workflow=workflow,
                first_node=first_node,
                noise_apis=noise_apis,
                noise_workflows=noise_wfs,
                slot_values=slot_values,
                sample_type="contrastive_workflow"
            )
        
        elif sample_type_rand < 0.70 and standalone_apis:
            # 样本类型 B：用户只想查询
            target_api = random.choice(standalone_apis)
            api_id = target_api["id"]
            
            if api_id in self.api_instructions:
                instruction = self.sampling_strategy.sample(api_id, self.api_instructions[api_id])
            else:
                instruction = f"查询{target_api.get('desc', '信息')}"
            
            if self.enable_asr_noise:
                instruction = self.asr_perturbator.perturb(instruction)
            
            # 生成槽位值（替代完整 AMIS Schema）
            slot_values = self._generate_slot_values_for_api(target_api)
            
            # 把目标工作流也加入候选
            all_noise_wfs = noise_wfs + [workflow]
            
            return self._build_two_round_api_sample(
                domain=domain,
                instruction=instruction,
                target_api=target_api,
                noise_apis=[a for a in noise_apis if a["id"] != target_api["id"]],
                noise_workflows=all_noise_wfs,
                slot_values=slot_values,
                sample_type="contrastive_api"
            )
        
        elif workflow_only_apis:
            # 样本类型 C：工作流专用 API
            # 🔥 修复：根据 workflow_only API 找到对应的工作流
            
            # 筛选出有映射的 workflow_only API
            mapped_workflow_only_apis = [
                api for api in workflow_only_apis 
                if api["id"] in self.workflow_only_api_to_workflow
            ]
            
            if not mapped_workflow_only_apis:
                # 没有可用的映射，回退到样本类型 A
                return None
            
            target_api = random.choice(mapped_workflow_only_apis)
            api_id = target_api["id"]
            
            # 🔥 使用映射找到正确的工作流和首节点
            target_workflow = self.workflow_only_api_to_workflow[api_id]
            target_first_node = self.workflow_only_api_to_first_node[api_id]
            
            if not target_first_node:
                return None
            
            if api_id in self.api_instructions:
                instruction = self.sampling_strategy.sample(api_id, self.api_instructions[api_id])
            else:
                instruction = f"{target_api.get('desc', '办理业务')}"
            
            if self.enable_asr_noise:
                instruction = self.asr_perturbator.perturb(instruction)
            
            # 生成槽位值（替代完整 AMIS Schema）
            slot_values = self._generate_slot_values_for_workflow(target_workflow, target_first_node)
            
            # 🔥 更新 noise_wfs：排除目标工作流，加入原来随机选的工作流
            other_wfs = [wf for wf in workflows if wf["id"] != target_workflow["id"]]
            num_noise_wfs = random.randint(3, 6)
            noise_wfs = random.sample(other_wfs, min(num_noise_wfs, len(other_wfs))) if other_wfs else []
            
            return self._build_two_round_workflow_sample(
                domain=domain,
                instruction=instruction,
                target_workflow=target_workflow,
                first_node=target_first_node,
                noise_apis=noise_apis,
                noise_workflows=noise_wfs,
                slot_values=slot_values,
                sample_type="contrastive_workflow_only"
            )
        
        else:
            # 回退到样本类型 A
            wf_id = workflow["id"]
            if wf_id in self.workflow_instructions and self.workflow_instructions[wf_id]:
                instruction = random.choice(self.workflow_instructions[wf_id])
            else:
                instruction = f"我要{workflow.get('name', '办理业务')}"
            
            if self.enable_asr_noise:
                instruction = self.asr_perturbator.perturb(instruction)
            
            # 生成槽位值（替代完整 AMIS Schema）
            slot_values = self._generate_slot_values_for_workflow(workflow, first_node)
            
            return self._build_two_round_workflow_sample(
                domain=domain,
                instruction=instruction,
                target_workflow=workflow,
                first_node=first_node,
                noise_apis=noise_apis,
                noise_workflows=noise_wfs,
                slot_values=slot_values,
                sample_type="contrastive_workflow"
            )
    
    def _generate_workflow_step_sample(self) -> Optional[Dict]:
        """
        生成工作流步骤样本（单轮对话 - Slot-Filling）
        
        已在工作流中，不需要选择，直接生成槽位值
        """
        domain = random.choice(self.domains)
        workflows = self.scene_loader.get_domain_workflows(domain)
        apis = self.scene_loader.get_domain_apis(domain)
        
        if not workflows:
            return None
        
        workflow = random.choice(workflows)
        db_workflow_id = workflow["id"]
        
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])
        
        # 分类节点
        api_call_nodes = [n for n in nodes if n.get("type") == "api_call"]
        notification_nodes = [n for n in nodes if n.get("type") == "notification"]
        end_nodes = [n for n in nodes if n.get("type") == "end"]
        
        # 按权重选择节点类型
        node_type_weights = []
        if api_call_nodes:
            node_type_weights.append(("api_call", 0.75, api_call_nodes))
        if notification_nodes:
            node_type_weights.append(("notification", 0.22, notification_nodes))
        if end_nodes:
            node_type_weights.append(("end", 0.03, end_nodes))
        
        if not node_type_weights:
            return None
        
        total_weight = sum(w[1] for w in node_type_weights)
        rand = random.random() * total_weight
        cumulative = 0
        selected_nodes = None
        for _, weight, nodes_list in node_type_weights:
            cumulative += weight
            if rand <= cumulative:
                selected_nodes = nodes_list
                break
        
        if not selected_nodes:
            selected_nodes = node_type_weights[-1][2]
        
        node = random.choice(selected_nodes)
        node_id = node.get("id", "")
        node_type = node.get("type", "")
        
        # 收集上下文
        if node_type == "end":
            context_data = self._collect_all_workflow_outputs(nodes)
        else:
            context_data = self._collect_previous_outputs(nodes, edges, node_id)
        
        if node_type == "notification":
            context_data = self._ensure_notification_vars(node, context_data)
        
        # 🔥 生成槽位值（替代完整 AMIS Schema）
        slot_values = self._generate_slot_values_for_workflow_step(node, context_data)
        
        # 获取指令
        ai_instructions = node.get("ai_instructions", {})
        instruction = ai_instructions.get("user_message", node.get("name", "执行步骤"))
        
        if self.enable_asr_noise:
            instruction = self.asr_perturbator.perturb(instruction)
        
        full_node_id = f"{db_workflow_id}_node_{node_id}"
        
        return self._build_single_round_workflow_step_sample(
            domain=domain,
            instruction=instruction,
            workflow=workflow,
            node=node,
            context_data=context_data,
            slot_values=slot_values
        )
    
    def _generate_rejection_sample(self) -> Optional[Dict]:
        """
        生成拒绝样本（单轮对话）
        
        AI 只需要输出 REJECT，后端直接生成拒绝 AMIS Schema
        """
        domain = random.choice(self.domains)
        instruction = random.choice(self.irrelevant_instructions)
        
        apis = self.scene_loader.get_domain_apis(domain)
        workflows = self.scene_loader.get_domain_workflows(domain)
        
        # 构建候选列表
        num_apis = random.randint(12, 20)  # 扩大召回
        noise_apis = random.sample(apis, min(num_apis, len(apis))) if apis else []
        
        num_wfs = random.randint(3, 6)  # 扩大召回
        noise_wfs = random.sample(workflows, min(num_wfs, len(workflows))) if workflows else []
        
        return self._build_single_round_rejection_sample(
            domain=domain,
            instruction=instruction,
            noise_apis=noise_apis,
            noise_workflows=noise_wfs,
            sample_type="rejection"
        )

    def _generate_help_sample(self) -> Optional[Dict]:
        """生成帮助样本（单轮对话），输出 HELP"""
        if not getattr(self, "help_instructions", None):
            return None

        domain = random.choice(self.domains)
        instruction = random.choice(self.help_instructions)

        apis = self.scene_loader.get_domain_apis(domain)
        workflows = self.scene_loader.get_domain_workflows(domain)

        num_apis = random.randint(12, 20)
        noise_apis = random.sample(apis, min(num_apis, len(apis))) if apis else []

        num_wfs = random.randint(3, 6)
        noise_wfs = random.sample(workflows, min(num_wfs, len(workflows))) if workflows else []

        return self._build_single_round_help_sample(
            domain=domain,
            instruction=instruction,
            noise_apis=noise_apis,
            noise_workflows=noise_wfs,
            sample_type="help_intent"
        )
    
    def _generate_mismatch_rejection_sample(self) -> Optional[Dict]:
        """生成不匹配拒绝样本（单轮对话）"""
        all_domains = list(self.domains)
        if len(all_domains) < 2:
            return None
        
        intent_domain = random.choice(all_domains)
        graph_domain = random.choice([d for d in all_domains if d != intent_domain])
        
        intent_apis = self.scene_loader.get_domain_apis(intent_domain)
        if not intent_apis:
            return None
        
        target = random.choice(intent_apis)
        if target["id"] in self.api_instructions:
            instruction = random.choice(self.api_instructions[target["id"]])
        else:
            instruction = target.get("desc", "查询信息")
        
        graph_apis = self.scene_loader.get_domain_apis(graph_domain)
        graph_workflows = self.scene_loader.get_domain_workflows(graph_domain)
        
        num_apis = random.randint(12, 20)  # 扩大召回
        noise_apis = random.sample(graph_apis, min(num_apis, len(graph_apis))) if graph_apis else []
        
        num_wfs = random.randint(3, 6)  # 扩大召回
        noise_wfs = random.sample(graph_workflows, min(num_wfs, len(graph_workflows))) if graph_workflows else []
        
        return self._build_single_round_rejection_sample(
            domain=graph_domain,
            instruction=instruction,
            noise_apis=noise_apis,
            noise_workflows=noise_wfs,
            sample_type="mismatch_rejection"
        )


    # ========== 🔥 构建样本的核心方法 ==========
    
    def _build_two_round_api_sample(
        self,
        domain: str,
        instruction: str,
        target_api: Dict,
        noise_apis: List[Dict],
        noise_workflows: List[Dict],
        slot_values: Dict,
        sample_type: str
    ) -> Dict:
        """
        构建两轮对话的 API 样本（Slot-Filling 版本）
        
        结构：
        - system1: 候选列表
        - user: 指令
        - assistant1: API: xxx
        - system2: API 详情 + 槽位列表
        - assistant2: 槽位值 JSON
        """
        # 第一轮 System：候选列表
        all_apis = noise_apis + [target_api]
        random.shuffle(all_apis)
        
        candidates_text = self._build_candidates_text(all_apis, noise_workflows)
        system1 = f"""可用资源：
{candidates_text}

任务：根据用户指令选择合适的 API 或工作流。
- 如果匹配到 API，输出：API: <API描述>
- 如果匹配到工作流，输出：WORKFLOW: <工作流名称>
- 如果用户在询问你是谁 / 你能做什么 / 你现在能帮我干啥 / 帮助，输出：HELP
- 如果无法匹配，输出：REJECT"""
        
        # 第一轮 Assistant：选择 API
        api_desc = target_api.get("desc", target_api.get("name", ""))
        assistant1 = f"API: {api_desc}"
        
        # 第二轮 System：API 详情 + 槽位列表
        api_path = target_api.get("path", "")
        api_method = target_api.get("method", "GET")
        api_request = target_api.get("request", [])
        
        fields = [p.get("name") for p in api_request[:5]]
        slots = ["page_title", "user_message", "submit_button_text", "api_url", "api_method"]  # 🔥 新增 api_url 和 api_method
        for field in fields:
            slots.append(f"field_label_{field}")
        
        system2 = f"""API详情：
{{
  "path": "{api_path}",
  "method": "{api_method}",
  "desc": "{api_desc}",
  "request": {json.dumps([{"name": p.get("name"), "type": p.get("type")} for p in api_request[:5]], ensure_ascii=False)}
}}

任务：为以下槽位生成中文文案（JSON 格式）：
{json.dumps(slots, ensure_ascii=False)}

要求：
- page_title：3-6 字
- user_message：10-20 字
- field_label_xxx：2-4 字
- api_url：完整的 API 路径（如果有路径参数，使用 ${{param}} 格式）
- api_method：HTTP 方法（GET/POST/PUT/DELETE）
- 只输出 JSON，不要其他内容"""
        
        # 第二轮 Assistant：槽位值
        assistant2 = json.dumps(slot_values, ensure_ascii=False, indent=2)
        
        return {
            "messages": [
                {"role": "system", "content": system1},
                {"role": "user", "content": instruction},
                {"role": "assistant", "content": assistant1},
                {"role": "system", "content": system2},
                {"role": "assistant", "content": assistant2}
            ],
            "metadata": {
                "domain": domain,
                "sample_type": sample_type,
                "target_api_id": target_api.get("id"),
                "target_api_path": target_api.get("path")
            }
        }
    
    def _build_two_round_workflow_sample(
        self,
        domain: str,
        instruction: str,
        target_workflow: Dict,
        first_node: Dict,
        noise_apis: List[Dict],
        noise_workflows: List[Dict],
        slot_values: Dict,
        sample_type: str
    ) -> Dict:
        """
        构建两轮对话的工作流样本（Slot-Filling 版本）
        
        结构：
        - system1: 候选列表
        - user: 指令
        - assistant1: WORKFLOW: xxx
        - system2: 工作流详情 + 槽位列表
        - assistant2: 槽位值 JSON
        """
        domain_cn = self._get_domain_cn(domain)
        
        # 第一轮 System：候选列表
        all_workflows = noise_workflows + [target_workflow]
        random.shuffle(all_workflows)
        
        candidates_text = self._build_candidates_text(noise_apis, all_workflows)
        system1 = (
            f"你是{domain_cn}领域的 AMIS 界面生成助手。\n\n"
            f"可用资源：\n{candidates_text}\n\n"
            "任务：根据用户指令选择合适的 API 或工作流。\n"
            "- 如果匹配到 API，输出：API: <名称>\n"
            "- 如果匹配到工作流，输出：WORKFLOW: <名称>\n"
            "- 如果用户在询问你是谁 / 你能做什么 / 你现在能帮我干啥 / 帮助，输出：HELP\n"
            "- 如果无法匹配，输出：REJECT"
        )
        
        # 第一轮 Assistant：选择工作流
        wf_name = target_workflow.get("name", target_workflow.get("id", ""))
        assistant1 = f"WORKFLOW: {wf_name}"
        
        # 第二轮 System：工作流详情 + 槽位列表
        workflow_detail = self._build_workflow_detail(target_workflow, first_node)
        
        # 提取槽位列表
        parameters = first_node.get("config", {}).get("parameters", {})
        fields = list(parameters.keys())[:5]
        slots = ["page_title", "user_message", "submit_button_text", "reset_button_text"]
        
        # 🔥 如果第一个节点是 api_call，添加 api_url 和 api_method 槽位
        if first_node.get("type") == "api_call":
            slots.extend(["api_url", "api_method"])
        
        for field in fields:
            slots.append(f"field_label_{field}")
        
        system2 = f"""工作流详情：
{workflow_detail}

任务：为以下槽位生成中文文案（JSON 格式）：
{json.dumps(slots, ensure_ascii=False)}

要求：
- page_title：3-6 字
- user_message：10-20 字
- field_label_xxx：2-4 字
- api_url：完整的 API 路径（如果有路径参数，使用 ${{param}} 格式）
- api_method：HTTP 方法（GET/POST/PUT/DELETE）
- 只输出 JSON，不要其他内容"""
        
        # 第二轮 Assistant：槽位值
        assistant2 = json.dumps(slot_values, ensure_ascii=False, indent=2)
        
        return {
            "messages": [
                {"role": "system", "content": system1},
                {"role": "user", "content": instruction},
                {"role": "assistant", "content": assistant1},
                {"role": "system", "content": system2},
                {"role": "assistant", "content": assistant2}
            ],
            "metadata": {
                "domain": domain,
                "sample_type": sample_type,
                "target_workflow_id": target_workflow.get("id"),
                "target_workflow_name": target_workflow.get("name")
            }
        }
    
    def _build_single_round_workflow_step_sample(
        self,
        domain: str,
        instruction: str,
        workflow: Dict,
        node: Dict,
        context_data: Dict,
        slot_values: Dict
    ) -> Dict:
        """
        构建单轮对话的工作流步骤样本（Slot-Filling 版本）
        
        已在工作流中，不需要选择，直接生成槽位值
        上下文数据放在 system prompt 中（模拟后端传递）
        如果是 api_call 节点，需要包含完整的 API 详情
        """
        domain_cn = self._get_domain_cn(domain)
        workflow_id = workflow.get("id", "")
        workflow_name = workflow.get("name", "")
        node_id = node.get("id", "")
        node_type = node.get("type", "")
        full_node_id = f"{workflow_id}_node_{node_id}"
        
        # 构建节点详情（基础信息）
        node_detail = self._build_node_detail_for_step(node, workflow_id)
        
        # 如果是 api_call 节点，添加完整的 API 详情
        api_detail_section = ""
        if node_type == "api_call":
            api_detail = self._get_node_api_detail(node)
            if api_detail:
                api_detail_str = json.dumps(api_detail, ensure_ascii=False, indent=2)
                api_detail_section = f"\n\n节点API详情：\n{api_detail_str}"
        
        # 构建上下文数据部分
        context_section = ""
        if context_data:
            context_str = json.dumps(context_data, ensure_ascii=False, indent=2)
            context_section = f"\n\n上下文数据（前序节点输出）：\n{context_str}"
        
        # 提取槽位列表
        config = node.get("config", {})
        parameters = config.get("parameters", {})
        fields = [k for k in parameters.keys() if k not in context_data][:5]
        slots = ["page_title", "user_message", "submit_button_text"]
        
        # 🔥 如果是 api_call 节点，添加 api_url 和 api_method 槽位
        if node_type == "api_call":
            slots.extend(["api_url", "api_method"])
        
        for field in fields:
            slots.append(f"field_label_{field}")
        
        # System prompt（包含 API 详情、上下文数据和槽位列表）
        system_prompt = f"""你是{domain_cn}领域的 AMIS 界面生成助手。

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
        
        # User input（只有指令，不包含上下文）
        user_input = instruction
        
        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": json.dumps(slot_values, ensure_ascii=False, indent=2)}
            ],
            "metadata": {
                "domain": domain,
                "sample_type": "workflow_step",
                "workflow_id": workflow_id,
                "node_id": full_node_id
            }
        }
    
    def _build_node_detail_for_step(self, node: Dict, workflow_id: str) -> str:
        """构建节点基础详情（用于 workflow_step）"""
        node_id = node.get("id", "")
        full_node_id = f"{workflow_id}_node_{node_id}"
        node_type = node.get("type", "")
        node_name = node.get("name", "")
        
        detail_parts = [
            f"ID: {full_node_id}",
            f"名称: {node_name}",
            f"类型: {node_type}"
        ]
        
        ai_inst = node.get("ai_instructions", {})
        if ai_inst.get("user_message"):
            detail_parts.append(f"提示: {ai_inst['user_message']}")
        
        return "\n".join(detail_parts)
    
    def _build_single_round_rejection_sample(
        self,
        domain: str,
        instruction: str,
        noise_apis: List[Dict],
        noise_workflows: List[Dict],
        sample_type: str
    ) -> Dict:
        """
        构建单轮对话的拒绝样本
        
        结构：
        - system: 候选列表
        - user: 无关指令
        - assistant: REJECT
        
        后端匹配到 REJECT 后直接生成拒绝 AMIS Schema
        """
        domain_cn = self._get_domain_cn(domain)
        
        # System：候选列表
        candidates_text = self._build_candidates_text(noise_apis, noise_workflows)
        system_prompt = (
            f"你是{domain_cn}领域的 AMIS 界面生成助手。\n\n"
            f"可用资源：\n{candidates_text}\n\n"
            "任务：根据用户指令选择合适的 API 或工作流。\n"
            "- 如果匹配到 API，输出：API: <名称>\n"
            "- 如果匹配到工作流，输出：WORKFLOW: <名称>\n"
            "- 如果用户在询问你是谁 / 你能做什么 / 你现在能帮我干啥 / 帮助，输出：HELP\n"
            "- 如果无法匹配，输出：REJECT"
        )
        
        # Assistant：REJECT
        assistant_content = "REJECT"
        
        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": instruction},
                {"role": "assistant", "content": assistant_content}
            ],
            "metadata": {
                "domain": domain,
                "sample_type": sample_type
            }
        }

    def _build_single_round_help_sample(
        self,
        domain: str,
        instruction: str,
        noise_apis: List[Dict],
        noise_workflows: List[Dict],
        sample_type: str
    ) -> Dict:
        """
        构建单轮对话的帮助样本

        结构：
        - system: 候选列表
        - user: 帮助类指令
        - assistant: HELP
        """
        domain_cn = self._get_domain_cn(domain)
        candidates_text = self._build_candidates_text(noise_apis, noise_workflows)

        system_prompt = (
            f"你是{domain_cn}领域的 AMIS 界面生成助手。\n\n"
            f"可用资源：\n{candidates_text}\n\n"
            "任务：根据用户指令选择合适的 API 或工作流。\n"
            "- 如果匹配到 API，输出：API: <名称>\n"
            "- 如果匹配到工作流，输出：WORKFLOW: <名称>\n"
            "- 如果用户在询问你是谁 / 你能做什么 / 你现在能帮我干啥 / 帮助，输出：HELP\n"
            "- 如果无法匹配，输出：REJECT"
        )

        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": instruction},
                {"role": "assistant", "content": "HELP"}
            ],
            "metadata": {
                "domain": domain,
                "sample_type": sample_type
            }
        }


    # ========== 辅助方法 ==========
    
    def _get_domain_cn(self, domain: str) -> str:
        """获取领域中文名"""
        domain_names = {
            "medical": "医疗", "finance": "财务", "ecommerce": "电商",
            "train_ticket": "火车票", "logistics": "物流", "hrm": "人力资源",
            "education": "教育", "hotel": "酒店", "banking": "银行",
            "government": "政务", "realestate": "房产", "catering": "餐饮"
        }
        return domain_names.get(domain, domain)
    
    def _build_candidates_text(self, apis: List[Dict], workflows: List[Dict]) -> str:
        """构建候选列表文本"""
        lines = []
        
        # API 列表
        for api in apis:
            method = api.get("method", "GET")
            path = api.get("path", "")
            desc = api.get("desc", "")
            is_workflow_only = api.get("workflow_only", False) and api.get("id") in self.workflow_only_api_to_workflow
            tag = "（仅工作流）" if is_workflow_only else ""
            lines.append(f"[API] {method} {path} - {desc}{tag}")
        
        # 工作流列表
        for wf in workflows:
            wf_id = wf.get("id", "")
            wf_name = wf.get("name", "")
            wf_desc = wf.get("desc", "")[:50] if wf.get("desc") else ""
            lines.append(f"[WORKFLOW] {wf_id} - {wf_name}" + (f" ({wf_desc})" if wf_desc else ""))
        
        return "\n".join(lines)
    
    def _build_api_detail(self, api: Dict) -> str:
        """
        构建 API 详情（和 graph_input 格式一致）
        """
        detail = {
            "id": api.get("id", ""),
            "type": "api",
            "desc": api.get("desc", ""),
            "path": api.get("path", ""),
            "method": api.get("method", "GET"),
            "request": api.get("request", []),
            "response": api.get("response", []),
            "domain": api.get("domain", "")
        }
        return json.dumps(detail, ensure_ascii=False, indent=2)
    
    def _build_workflow_detail(self, workflow: Dict, first_node: Dict) -> str:
        """
        构建工作流详情（包含完整流程 + 第一个节点 + 节点 API 详情）
        """
        workflow_id = workflow.get("id", "")
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])
        
        # 过滤掉 start/end 节点
        valid_nodes = [n for n in nodes if n.get("type") not in ("start", "end")]
        
        # 构建节点链
        node_names = [n.get("name", n.get("id", "")) for n in valid_nodes[:5]]
        node_chain = " → ".join(node_names)
        if len(valid_nodes) > 5:
            node_chain += " → ..."
        
        # 构建第一个节点详情
        first_node_id = first_node.get("id", "")
        full_first_node_id = f"{workflow_id}_node_{first_node_id}"
        first_node_detail = self._build_node_detail(first_node, workflow_id)
        
        # 获取第一个节点的 API 详情
        first_node_api_detail = self._get_node_api_detail(first_node)
        
        detail = {
            "id": workflow_id,
            "name": workflow.get("name", ""),
            "desc": workflow.get("desc", ""),
            "node_chain": node_chain,
            "first_node": {
                "id": full_first_node_id,
                "name": first_node.get("name", ""),
                "type": first_node.get("type", ""),
                "ai_instructions": first_node.get("ai_instructions", {}),
                "api": first_node_api_detail
            }
        }
        
        return json.dumps(detail, ensure_ascii=False, indent=2)
    
    def _build_node_detail(self, node: Dict, workflow_id: str) -> str:
        """构建节点详情"""
        node_id = node.get("id", "")
        full_node_id = f"{workflow_id}_node_{node_id}"
        node_type = node.get("type", "")
        node_name = node.get("name", "")
        
        config = node.get("config", {})
        api_endpoint = config.get("api_endpoint", "")
        method = config.get("method", "GET")
        
        outputs = node.get("outputs", [])
        output_names = [o.get("name", "") for o in outputs[:4] if o.get("name")]
        
        detail_parts = [
            f"ID: {full_node_id}",
            f"名称: {node_name}",
            f"类型: {node_type}"
        ]
        
        if api_endpoint:
            detail_parts.append(f"API: {method} {api_endpoint}")
        
        if output_names:
            detail_parts.append(f"输出: {', '.join(output_names)}")
        
        ai_inst = node.get("ai_instructions", {})
        if ai_inst.get("user_message"):
            detail_parts.append(f"提示: {ai_inst['user_message']}")
        
        return "\n".join(detail_parts)
    
    def _get_node_api_detail(self, node: Dict) -> Optional[Dict]:
        """获取节点对应的 API 详情"""
        config = node.get("config", {})
        api_id = config.get("api_id", "")
        api_endpoint = config.get("api_endpoint", "")
        method = config.get("method", "GET")
        
        if not api_endpoint:
            return None
        
        # 尝试从场景定义中找到完整的 API 信息
        for domain in self.domains:
            apis = self.scene_loader.get_domain_apis(domain)
            for api in apis:
                if api.get("id") == api_id or api.get("path") == api_endpoint:
                    return {
                        "id": api.get("id", ""),
                        "path": api.get("path", ""),
                        "method": api.get("method", method),
                        "request": api.get("request", []),
                        "response": api.get("response", [])
                    }
        
        # 如果找不到，返回基本信息
        return {
            "path": api_endpoint,
            "method": method,
            "request": [],
            "response": []
        }
    
    def _collect_all_workflow_outputs(self, nodes: List[Dict]) -> Dict[str, Any]:
        """收集工作流所有节点的输出"""
        context_data = {}
        
        for node in nodes:
            node_type = node.get("type", "")
            if node_type in ("start", "end"):
                continue
            
            outputs = node.get("outputs", [])
            for output in outputs:
                output_name = output.get("name", "")
                output_type = output.get("type", "string")
                if output_name and output_name not in context_data:
                    context_data[output_name] = self._generate_mock_value(output_name, output_type)
        
        return context_data
    
    def _collect_previous_outputs(self, nodes: List[Dict], edges: List[Dict], current_node_id: str) -> Dict[str, Any]:
        """收集当前节点之前所有节点的输出"""
        node_map = {n["id"]: n for n in nodes}
        
        reverse_edges = {}
        for edge in edges:
            target = edge.get("target", "")
            source = edge.get("source", "")
            if target not in reverse_edges:
                reverse_edges[target] = []
            reverse_edges[target].append(source)
        
        visited = set()
        queue = [current_node_id]
        previous_nodes = []
        
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            
            for source_id in reverse_edges.get(node_id, []):
                if source_id not in visited:
                    queue.append(source_id)
                    if source_id != current_node_id:
                        previous_nodes.append(source_id)
        
        context_data = {}
        for prev_node_id in previous_nodes:
            prev_node = node_map.get(prev_node_id, {})
            outputs = prev_node.get("outputs", [])
            for output in outputs:
                output_name = output.get("name", "")
                output_type = output.get("type", "string")
                if output_name and output_name not in context_data:
                    context_data[output_name] = self._generate_mock_value(output_name, output_type)
        
        return context_data
    
    def _ensure_notification_vars(self, node: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """确保 notification 节点的变量都在上下文中"""
        import re
        
        config = node.get("config", {})
        message_template = config.get("message_template", "")
        
        var_names = re.findall(r'\$\{(\w+)\}', message_template)
        
        for var_name in var_names:
            if var_name not in context_data:
                context_data[var_name] = self._generate_mock_value(var_name, "string")
        
        return context_data
    
    def _generate_mock_value(self, field_name: str, field_type: str) -> Any:
        """根据字段名和类型生成模拟值"""
        name_lower = field_name.lower()
        
        if "train" in name_lower and ("number" in name_lower or "no" in name_lower):
            train_types = ["G", "D", "C", "K", "T", "Z"]
            return f"{random.choice(train_types)}{random.randint(1, 9999)}"
        
        if "station" in name_lower:
            stations = ["北京南", "上海虹桥", "广州南", "深圳北", "杭州东", "南京南"]
            return random.choice(stations)
        
        if "seat_type" in name_lower:
            return random.choice(["商务座", "一等座", "二等座", "硬卧", "软卧"])
        
        if "seat" in name_lower and ("number" in name_lower or "selected" in name_lower):
            return f"{random.randint(1, 16)}车{random.randint(1, 100)}{random.choice(['A', 'B', 'C', 'D', 'F'])}"
        
        if "payment_method" in name_lower:
            return random.choice(["微信支付", "支付宝", "银行卡"])
        
        if "id" in name_lower:
            prefixes = {
                "order": "ORD", "payment": "PAY", "ticket": "TKT", "user": "USR",
                "patient": "PAT", "loan": "LOAN", "contract": "CTR", "house": "HSE"
            }
            for key, prefix in prefixes.items():
                if key in name_lower:
                    return f"{prefix}{random.randint(100000, 999999)}"
            return f"ID{random.randint(100000, 999999)}"
        
        if any(kw in name_lower for kw in ["amount", "price", "total", "fee"]) and field_type != "array":
            return round(random.uniform(10, 10000), 2)
        
        if any(kw in name_lower for kw in ["count", "num", "quantity"]):
            return random.randint(1, 100)
        
        if "status" in name_lower:
            return random.choice(["pending", "confirmed", "completed"])
        
        if any(kw in name_lower for kw in ["date", "time"]):
            return f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        
        if "name" in name_lower:
            surnames = ["张", "李", "王", "刘", "陈"]
            names = ["伟", "芳", "娜", "敏", "静"]
            return f"{random.choice(surnames)}{random.choice(names)}"
        
        if field_type == "array":
            return [{"id": random.randint(1, 100), "name": f"项目{random.randint(1,10)}"}]
        elif field_type in ["float", "number"]:
            return round(random.uniform(1, 1000), 2)
        elif field_type in ["integer", "int"]:
            return random.randint(1, 100)
        elif field_type == "boolean":
            return random.choice([True, False])
        else:
            return f"mock_{field_name}_{random.randint(1000, 9999)}"
    
    def _randomize_amis_details(self, schema: Dict) -> Dict:
        """随机化 AMIS Schema 细节"""
        body = schema.get("body", {})
        
        if isinstance(body, dict) and body.get("type") == "form":
            body["mode"] = random.choice(["horizontal", "inline", "normal"])
            body["labelAlign"] = random.choice(["left", "right"])
            
            if body["mode"] == "horizontal":
                left = random.choice([2, 3, 4])
                body["horizontal"] = {"left": left, "right": 12 - left}
            
            submit_texts = ["提交", "确定", "下一步", "确认", "保存"]
            body["submitText"] = random.choice(submit_texts)
        
        return schema


    def _validate_and_report(self, samples: List[Dict]):
        """验证数据集质量并输出报告"""
        print("\n" + "=" * 60)
        print("📊 数据集质量报告")
        print("=" * 60)
        
        # 按类型统计
        type_samples = {}
        for s in samples:
            t = s['metadata']['sample_type']
            if t not in type_samples:
                type_samples[t] = []
            type_samples[t].append(s)
        
        # 提取指令
        def get_instruction(sample):
            # 两轮对话：指令在 messages[1]
            # 单轮对话：指令在 messages[1]
            if len(sample['messages']) >= 2:
                return sample['messages'][1]['content'].split('\n')[0]
            return ""
        
        print(f"\n总样本数: {len(samples)}")
        
        # 统计轮数分布
        three_msg = sum(1 for s in samples if len(s['messages']) == 3)
        five_msg = sum(1 for s in samples if len(s['messages']) == 5)
        print(f"单轮对话(3条消息): {three_msg} ({three_msg/len(samples)*100:.1f}%)")
        print(f"两轮对话(5条消息): {five_msg} ({five_msg/len(samples)*100:.1f}%)")
        
        all_unique_rate_ok = True
        for t, ss in sorted(type_samples.items()):
            instructions = [get_instruction(s) for s in ss]
            unique_instructions = set(instructions)
            unique_rate = len(unique_instructions) / len(ss) * 100 if ss else 0
            
            status = "✅" if unique_rate >= 80 else "⚠️"
            if unique_rate < 80:
                all_unique_rate_ok = False
            
            print(f"{t:25s}: {len(ss):4d} ({len(ss)/len(samples)*100:5.1f}%), 唯一指令 {len(unique_instructions):4d}, 唯一率 {unique_rate:5.1f}% {status}")
            
            if unique_rate < 80:
                from collections import Counter
                counter = Counter(instructions)
                print(f"   重复最多的指令:")
                for inst, cnt in counter.most_common(3):
                    print(f"      {cnt:3d}x: {inst[:50]}")
        
        # 采样统计
        stats = self.sampling_strategy.get_statistics()
        print(f"\n采样统计:")
        print(f"   总 API 数: {stats['total_apis']}")
        print(f"   已使用变体数: {stats['total_used_variants']}")
        print(f"   重复采样次数: {stats['total_repeats']}")
        
        print("\n" + "=" * 60)
        if all_unique_rate_ok:
            print("✅ 所有类型唯一率均达标 (>= 80%)")
        else:
            print("⚠️ 部分类型唯一率未达标，请检查")
        print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="生成训练数据集 V9 - Slot-Filling 架构")
    parser.add_argument("--total", type=int, default=5000, help="总样本数")
    parser.add_argument("--output", type=str, default=None, help="输出文件路径")
    parser.add_argument("--no-asr", action="store_true", help="禁用 ASR 噪声扰动")
    
    args = parser.parse_args()
    
    if args.output is None:
        args.output = str(Path(__file__).parent.parent / "dataset_v9.jsonl")
    
    generator = DatasetGeneratorV9(enable_asr_noise=not args.no_asr)
    samples = generator.generate_dataset(
        total_samples=args.total,
        output_path=args.output
    )
    
    print(f"\n🎉 数据集生成完成！共 {len(samples)} 条样本（Slot-Filling 架构）")
