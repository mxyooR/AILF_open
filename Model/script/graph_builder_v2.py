"""
Graph Context Builder V2 - 图谱驱动的上下文构建器
与后端 graph_ai_model_service.py 格式完全一致

支持三种图谱模式：
1. API-only 图谱：只包含 API 节点（用于直接 API 调用）
2. Workflow 图谱：包含 Workflow 节点（简化格式，用于 Global_Routing）
3. WorkflowNode 图谱：包含 WorkflowNode 和 Field 节点（用于 Workflow_Input/Execute）

节点格式与后端 prepare_graph_batch 方法一致：
- API 节点：id, type, desc, path, method, request, response, domain
- Workflow 节点：id, type, desc, name, domain
- WorkflowNode 节点：id, name, type, description, config, outputs, ai_instructions, domain
- Field 节点：id, type, name, label, field_type, required
"""

import random
from typing import Dict, List, Any, Tuple, Optional


class GraphContextBuilderV2:
    """
    图谱上下文构建器 V2 - 与后端 graph_ai_model_service.py 格式一致
    
    后端 GNN 编码时的文本表示格式：
    - API: "ID:{id}, 类型:api, 描述:{desc}, 方法:{method}, 路径:{path}, 请求参数:[...]"
    - Workflow: "ID:{id}, 类型:workflow, 名称:{name}, 描述:{desc}"
    - WorkflowNode: "ID:{id}, 类型:{type}, 名称:{name}, 描述:{description}, ..."
    """
    
    def __init__(self, scene_loader):
        self.scene_loader = scene_loader
        self.all_domains = scene_loader.get_all_domains()
        self.noise_apis = scene_loader.get_noise_apis()
    
    def build_api_only_graph(
        self, 
        target_api: Dict[str, Any], 
        related_apis: List[Dict[str, Any]], 
        domain: str,
        include_distractors: bool = True
    ) -> Dict[str, Any]:
        """
        构建包含 API 节点的图谱（用于直接 API 调用样本）
        
        与后端 build_graph_input 一致：
        - 图谱中包含所有可访问的 API 和 Workflow（让 AI 自己选择）
        - AI 需要学会：即使有 Workflow 可选，也要根据用户意图选择直接调用 API
        
        Args:
            target_api: 目标 API 定义
            related_apis: 相关 API 列表（同域）
            domain: 业务域
            include_distractors: 是否包含干扰项（包括 Workflow 节点作为干扰）
        
        Returns:
            图谱结构 {"nodes": [...], "edges": [...]}
        """
        nodes = []
        edges = []
        seen_ids = set()  # 用于去重
        
        # 添加目标 API 节点
        target_node = self._build_api_node(target_api, domain)
        nodes.append(target_node)
        seen_ids.add(target_node["id"])
        
        # 添加相关 API 节点
        for api in related_apis:
            if api["id"] not in seen_ids:
                api_node = self._build_api_node(api, domain)
                nodes.append(api_node)
                seen_ids.add(api["id"])
        
        if include_distractors:
            # 添加同域干扰项（包括 API 和 Workflow，让 AI 学会取舍）
            same_domain_items = self._get_same_domain_negatives(
                domain, target_api["id"], count=random.randint(2, 4)
            )
            for item in same_domain_items:
                if item["id"] not in seen_ids:
                    nodes.append(item)
                    seen_ids.add(item["id"])
            
            # 添加跨域干扰项
            cross_domain_items = self._get_cross_domain_negatives(
                domain, count=random.randint(1, 2)
            )
            for item in cross_domain_items:
                if item["id"] not in seen_ids:
                    nodes.append(item)
                    seen_ids.add(item["id"])
        
        return {"nodes": nodes, "edges": edges}
    
    def build_workflow_graph(
        self, 
        workflow: Dict[str, Any], 
        domain: str,
        include_distractors: bool = True,
        db_workflow_id: str = None,
        first_node: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        构建包含 Workflow 节点的图谱（用于工作流入口样本）
        Global_Routing 阶段使用简化的 Workflow 节点格式
        
        与后端 build_graph_input 一致：图谱中的 Workflow ID 应该与输出中的 workflow_id 一致
        
        🔥 V8.1 改进：添加第一个工作流节点（WorkflowNode），让模型学习正确的 node_id
        
        Args:
            workflow: 工作流定义
            domain: 业务域
            include_distractors: 是否包含干扰项
            db_workflow_id: 数据库格式的 workflow_id（如 workflow_1234567890），
                           如果提供，则使用此 ID 替换原始 ID
            first_node: 第一个工作流节点（用于让模型学习正确的 node_id）
        
        Returns:
            图谱结构 {"nodes": [...], "edges": [...]}
        """
        nodes = []
        edges = []
        seen_ids = set()  # 用于去重
        
        # 添加目标 Workflow 节点（简化格式）
        # 如果提供了 db_workflow_id，使用它替换原始 ID
        workflow_for_graph = workflow.copy()
        if db_workflow_id:
            workflow_for_graph["id"] = db_workflow_id
        
        effective_workflow_id = db_workflow_id or workflow["id"]
        
        wf_node = self._build_workflow_node(workflow_for_graph, domain)
        nodes.append(wf_node)
        seen_ids.add(wf_node["id"])
        
        # 🔥 添加第一个工作流节点（WorkflowNode），让模型学习正确的 node_id
        if first_node:
            wf_node_detail = self._build_workflow_node_detail(
                workflow_for_graph, first_node, domain
            )
            nodes.append(wf_node_detail)
            seen_ids.add(wf_node_detail["id"])
            
            # 添加 Workflow -> WorkflowNode 的边
            edges.append({
                "source": effective_workflow_id,
                "target": wf_node_detail["id"],
                "relation": "has_first_node"
            })
            
            # 如果是 api_call 节点且是 POST 方法，添加字段节点
            if first_node.get("type") == "api_call":
                config = first_node.get("config", {})
                if config.get("method", "GET").upper() == "POST":
                    field_nodes, field_edges = self._build_field_nodes_from_api_params(
                        wf_node_detail["id"], first_node, domain
                    )
                    for fn in field_nodes:
                        if fn["id"] not in seen_ids:
                            nodes.append(fn)
                            seen_ids.add(fn["id"])
                    edges.extend(field_edges)
                
                # 🔥 检查参数中是否有需要选项 API 的字段（不添加边，只添加节点）
                options_apis = self._build_options_api_nodes_only(first_node, seen_ids)
                for opt_node in options_apis:
                    if opt_node["id"] not in seen_ids:
                        nodes.append(opt_node)
                        seen_ids.add(opt_node["id"])
        
        if include_distractors:
            # 添加同域干扰项（API 和其他 Workflow）
            same_domain_items = self._get_same_domain_negatives(
                domain, workflow["id"], count=random.randint(3, 5)
            )
            for item in same_domain_items:
                if item["id"] not in seen_ids:
                    nodes.append(item)
                    seen_ids.add(item["id"])
            
            # 添加跨域干扰项
            cross_domain_items = self._get_cross_domain_negatives(
                domain, count=random.randint(1, 2)
            )
            for item in cross_domain_items:
                if item["id"] not in seen_ids:
                    nodes.append(item)
                    seen_ids.add(item["id"])
        
        return {"nodes": nodes, "edges": edges}
    
    def build_workflow_node_graph(
        self, 
        workflow: Dict[str, Any], 
        node: Dict[str, Any], 
        domain: str,
        accessible_apis: Optional[List[Dict[str, Any]]] = None,
        db_workflow_id: str = None
    ) -> Dict[str, Any]:
        """
        构建包含 WorkflowNode 和 Field 节点的图谱（用于工作流步骤样本）
        Workflow_Input/Workflow_Execute 阶段使用
        
        与后端 build_graph_input 完全一致：
        1. 包含所有 accessible_apis（让 AI 知道有哪些 API 可用）
        2. 包含当前节点的详细信息（WorkflowNode + Field）
        3. 包含关联的 API 详情（对于 api_call 节点）
        4. 🔥 包含需要的选项 API（用于 select 字段动态获取选项）
        
        Args:
            workflow: 工作流定义
            node: 当前工作流节点
            domain: 业务域
            accessible_apis: 可访问的 API 列表
            db_workflow_id: 数据库格式的 workflow_id（如 workflow_1234567890），
                           必须与用户输入中的 workflow_id 一致
        
        Returns:
            图谱结构 {"nodes": [...], "edges": [...]}
        """
        nodes = []
        edges = []
        seen_ids = set()  # 用于去重
        
        # 使用 db_workflow_id 或原始 ID
        effective_workflow_id = db_workflow_id or workflow['id']
        
        # ========== 1. 添加所有 accessible_apis（与后端一致）==========
        if accessible_apis:
            for api in accessible_apis:
                if api["id"] not in seen_ids:
                    api_node = self._build_api_node(api, domain)
                    nodes.append(api_node)
                    seen_ids.add(api["id"])
        
        # ========== 2. 添加当前 WorkflowNode 节点（完整格式）==========
        # 构建 WorkflowNode 节点 ID（与后端 convert_workflow_node_to_graph 一致）
        wf_node_id = f"{effective_workflow_id}_node_{node['id']}"
        
        # 创建使用正确 ID 的工作流副本
        workflow_for_graph = workflow.copy()
        workflow_for_graph["id"] = effective_workflow_id
        
        workflow_node = self._build_workflow_node_detail(workflow_for_graph, node, domain)
        nodes.append(workflow_node)
        seen_ids.add(workflow_node["id"])
        
        # ========== 3. 根据节点类型添加关联节点 ==========
        node_type = node.get("type", "")
        
        if node_type == "api_call":
            # 查找关联的 API 详情（可能已经在 accessible_apis 中添加过）
            api_details = self._find_api_details(node, accessible_apis or [])
            if api_details:
                # 如果 API 节点还没添加，添加它
                if api_details["id"] not in seen_ids:
                    api_node = self._build_api_node(api_details, domain)
                    nodes.append(api_node)
                    seen_ids.add(api_details["id"])
                
                # 添加 calls_api 边
                edges.append({
                    "source": wf_node_id,
                    "target": api_details["id"],
                    "relation": "calls_api"
                })
                
                # 从 API request 提取字段节点
                field_nodes, field_edges = self._build_field_nodes_from_api(
                    api_details["id"], api_details, domain
                )
                for fn in field_nodes:
                    if fn["id"] not in seen_ids:
                        nodes.append(fn)
                        seen_ids.add(fn["id"])
                edges.extend(field_edges)
                
                # 🔥 检查参数中是否有需要选项 API 的字段
                options_apis, options_edges = self._build_options_api_nodes(
                    node, api_details, seen_ids
                )
                nodes.extend(options_apis)
                edges.extend(options_edges)
                for api in options_apis:
                    seen_ids.add(api["id"])
            else:
                # 🔥 即使没有找到 API 详情，也要检查节点参数中是否有需要选项 API 的字段
                options_apis = self._build_options_api_nodes_only(node, seen_ids)
                for opt_node in options_apis:
                    if opt_node["id"] not in seen_ids:
                        nodes.append(opt_node)
                        seen_ids.add(opt_node["id"])
        
        # ========== 4. 添加少量干扰项（跨域）==========
        cross_domain_items = self._get_cross_domain_negatives(
            domain, count=random.randint(1, 2)
        )
        for item in cross_domain_items:
            if item["id"] not in seen_ids:
                nodes.append(item)
                seen_ids.add(item["id"])
        
        return {"nodes": nodes, "edges": edges}
    
    def _build_options_api_nodes_only(
        self, 
        node: Dict[str, Any], 
        seen_ids: set
    ) -> List[Dict[str, Any]]:
        """
        🔥 检查节点参数，为需要选项的字段添加选项 API 节点（只返回节点，不返回边）
        用于 build_workflow_graph，不需要字段到选项 API 的边
        
        Args:
            node: 工作流节点
            seen_ids: 已添加的节点 ID 集合
        
        Returns:
            options_api_nodes
        """
        import re
        
        options_nodes = []
        
        # 需要选项 API 的字段名列表
        options_fields = [
            "payment_method", "seat_type", "passenger_type", "id_type",
            "leave_type", "expense_type", "cert_type", "room_type",
            "house_type", "complaint_type", "service_type", "order_status",
            "invoice_type", "reimbursement_type"
        ]
        
        # 从节点参数中提取变量名
        config = node.get("config", {})
        parameters = config.get("parameters", {})
        
        for param_name, param_value in parameters.items():
            if isinstance(param_value, str):
                # 提取 ${xxx} 中的变量名
                match = re.match(r'^\$\{(\w+)\}$', param_value)
                if match:
                    var_name = match.group(1)
                    
                    # 检查是否需要选项 API
                    if var_name in options_fields:
                        options_api = self.scene_loader.get_options_api_for_field(var_name)
                        if options_api and options_api["id"] not in seen_ids:
                            # 构建选项 API 节点
                            options_node = {
                                "id": options_api["id"],
                                "type": "api",
                                "desc": options_api.get("desc", ""),
                                "path": options_api.get("path", ""),
                                "method": options_api.get("method", "GET"),
                                "request": options_api.get("request", []),
                                "response": options_api.get("response", []),
                                "is_options_api": True,
                                "options_for": var_name,
                                "domain": "common"
                            }
                            options_nodes.append(options_node)
        
        return options_nodes
    
    def _build_options_api_nodes(
        self, 
        node: Dict[str, Any], 
        api_details: Dict[str, Any],
        seen_ids: set
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        🔥 检查节点参数，为需要选项的字段添加选项 API 节点
        
        Args:
            node: 工作流节点
            api_details: API 详情
            seen_ids: 已添加的节点 ID 集合
        
        Returns:
            (options_api_nodes, edges)
        """
        import re
        
        options_nodes = []
        edges = []
        
        # 需要选项 API 的字段名列表
        options_fields = [
            "payment_method", "seat_type", "passenger_type", "id_type",
            "leave_type", "expense_type", "cert_type", "room_type",
            "house_type", "complaint_type", "service_type", "order_status",
            "invoice_type", "reimbursement_type"
        ]
        
        # 从节点参数中提取变量名
        config = node.get("config", {})
        parameters = config.get("parameters", {})
        
        for param_name, param_value in parameters.items():
            if isinstance(param_value, str):
                # 提取 ${xxx} 中的变量名
                match = re.match(r'^\$\{(\w+)\}$', param_value)
                if match:
                    var_name = match.group(1)
                    
                    # 检查是否需要选项 API
                    if var_name in options_fields:
                        options_api = self.scene_loader.get_options_api_for_field(var_name)
                        if options_api and options_api["id"] not in seen_ids:
                            # 构建选项 API 节点
                            options_node = {
                                "id": options_api["id"],
                                "type": "api",
                                "desc": options_api.get("desc", ""),
                                "path": options_api.get("path", ""),
                                "method": options_api.get("method", "GET"),
                                "request": options_api.get("request", []),
                                "response": options_api.get("response", []),
                                "is_options_api": True,
                                "options_for": var_name,
                                "domain": "common"
                            }
                            options_nodes.append(options_node)
                            
                            # 添加边：字段 -> 选项 API
                            edges.append({
                                "source": f"{api_details['id']}_param_{param_name}",
                                "target": options_api["id"],
                                "relation": "options_from"
                            })
        
        return options_nodes, edges
    
    def _build_api_node(self, api: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """
        构建 API 节点（与运行时格式一致）
        
        格式：
        {
            "id": "api_xxx",
            "type": "api",
            "desc": "描述",
            "path": "/api/xxx",
            "method": "GET",
            "request": [...],
            "response": [...],
            "domain": "xxx"
        }
        """
        return {
            "id": api["id"],
            "type": "api",
            "desc": api.get("desc", ""),
            "path": api.get("path", ""),
            "method": api.get("method", "GET"),
            "request": api.get("request", []),
            "response": api.get("response", []),
            "domain": domain
        }
    
    def _build_workflow_node(self, workflow: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """
        构建 Workflow 节点（简化格式，用于 Global_Routing）
        
        格式：
        {
            "id": "workflow_xxx",
            "type": "workflow",
            "desc": "描述",
            "name": "名称",
            "domain": "xxx"
        }
        """
        return {
            "id": workflow["id"],
            "type": "workflow",
            "desc": workflow.get("description", workflow.get("desc", "")),
            "name": workflow.get("name", ""),
            "domain": domain
        }
    
    def _build_workflow_node_detail(
        self, 
        workflow: Dict[str, Any], 
        node: Dict[str, Any], 
        domain: str
    ) -> Dict[str, Any]:
        """
        构建 WorkflowNode 节点（完整格式，用于 Workflow_Input/Execute）
        
        与后端 convert_workflow_node_to_graph 方法格式一致：
        {
            "id": "workflow_xxx_node_yyy",
            "name": "节点名称",
            "type": "api_call|condition|start|end|notification",
            "description": "描述",
            "config": {...},
            "outputs": [...],
            "ai_instructions": {...},
            "domain": "xxx"
        }
        
        注意：type 字段直接使用节点类型（api_call, condition 等），
        而不是 "workflow_node"，这与后端一致。
        已移除 user_input 节点支持，所有用户输入通过 api_call POST 表单完成。
        """
        wf_node_id = f"{workflow['id']}_node_{node['id']}"
        
        return {
            "id": wf_node_id,
            "name": node.get("name", ""),
            "type": node.get("type", "unknown"),  # 直接使用节点类型
            "description": node.get("description", ""),
            "config": node.get("config", {}),
            "outputs": node.get("outputs", []),
            "ai_instructions": node.get("ai_instructions", {}),
            "domain": domain
        }
    
    def _build_field_nodes_from_form(
        self, 
        parent_id: str, 
        node: Dict[str, Any],
        domain: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        从节点的 form_schema 构建 Field 节点和边（已废弃，保留兼容）
        @deprecated 使用 _build_field_nodes_from_api_params 代替
        """
        nodes = []
        edges = []
        
        config = node.get("config", {})
        form_schema = config.get("form_schema", {})
        fields = form_schema.get("fields", [])
        
        for field in fields:
            field_node_id = f"{parent_id}_field_{field['name']}"
            nodes.append({
                "id": field_node_id,
                "type": "field",
                "name": field["name"],
                "label": field.get("label", field["name"]),
                "field_type": field.get("type", "string"),
                "required": field.get("required", False),
                "_virtual": True
            })
            edges.append({
                "source": parent_id,
                "target": field_node_id,
                "relation": "has_field"
            })
        
        return nodes, edges
    
    def _build_field_nodes_from_api_params(
        self, 
        parent_id: str, 
        node: Dict[str, Any],
        domain: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        从 api_call 节点的 parameters 构建 Field 节点和边
        用于 POST 请求的表单字段
        """
        nodes = []
        edges = []
        
        config = node.get("config", {})
        parameters = config.get("parameters", {})
        
        # 从 parameters 中提取 ${xxx} 格式的变量
        import re
        for param_name, param_value in parameters.items():
            if isinstance(param_value, str) and param_value.startswith("${") and param_value.endswith("}"):
                field_name = param_value[2:-1]  # 去掉 ${ 和 }
                field_node_id = f"{parent_id}_field_{field_name}"
                nodes.append({
                    "id": field_node_id,
                    "type": "field",
                    "name": field_name,
                    "label": param_name,
                    "field_type": "string",
                    "required": True,
                    "_virtual": True
                })
                edges.append({
                    "source": parent_id,
                    "target": field_node_id,
                    "relation": "has_field"
                })
        
        return nodes, edges
    
    def _build_field_nodes_from_api(
        self, 
        parent_id: str, 
        api: Dict[str, Any],
        domain: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        从 API 的 request 数组构建 Field 节点和边
        """
        nodes = []
        edges = []
        
        request_fields = api.get("request", [])
        
        for field in request_fields:
            field_node_id = f"{parent_id}_param_{field['name']}"
            nodes.append({
                "id": field_node_id,
                "type": "field",
                "name": field["name"],
                "label": field.get("label", field["name"]),
                "field_type": field.get("type", "string"),
                "required": field.get("required", False),
                "_virtual": True
            })
            edges.append({
                "source": parent_id,
                "target": field_node_id,
                "relation": "has_parameter"
            })
        
        return nodes, edges

    
    def _find_api_details(
        self, 
        node: Dict[str, Any], 
        accessible_apis: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        从 accessible_apis 中查找 api_call 节点关联的 API 详情
        
        查找逻辑：
        1. 优先通过 api_id 匹配
        2. 其次通过 api_endpoint 匹配
        """
        config = node.get("config", {})
        api_id = config.get("api_id")
        api_endpoint = config.get("api_endpoint")
        
        for api in accessible_apis:
            # 通过 api_id 匹配
            if api_id and api.get("id") == api_id:
                return api
            # 通过 api_endpoint 匹配
            if api_endpoint and api.get("path") == api_endpoint:
                return api
        
        return None
    
    def _get_same_domain_negatives(
        self, 
        domain: str, 
        exclude_id: str, 
        count: int
    ) -> List[Dict[str, Any]]:
        """获取同域干扰项"""
        negatives = []
        
        domain_apis = self.scene_loader.get_domain_apis(domain)
        domain_workflows = self.scene_loader.get_domain_workflows(domain)
        
        all_items = []
        for api in domain_apis:
            if api["id"] != exclude_id:
                all_items.append(self._build_api_node(api, domain))
        
        for wf in domain_workflows:
            if wf["id"] != exclude_id:
                all_items.append(self._build_workflow_node(wf, domain))
        
        if len(all_items) > count:
            negatives = random.sample(all_items, count)
        else:
            negatives = all_items
        
        return negatives
    
    def _get_cross_domain_negatives(
        self, 
        exclude_domain: str, 
        count: int
    ) -> List[Dict[str, Any]]:
        """获取跨域干扰项"""
        negatives = []
        
        other_domains = [d for d in self.all_domains if d != exclude_domain]
        
        for _ in range(count):
            if not other_domains:
                break
            
            random_domain = random.choice(other_domains)
            
            domain_apis = self.scene_loader.get_domain_apis(random_domain)
            domain_workflows = self.scene_loader.get_domain_workflows(random_domain)
            
            all_items = []
            for api in domain_apis:
                all_items.append(self._build_api_node(api, random_domain))
            
            for wf in domain_workflows:
                all_items.append(self._build_workflow_node(wf, random_domain))
            
            if all_items:
                negatives.append(random.choice(all_items))
        
        return negatives
    
    def _get_noise_negatives(self, count: int) -> List[Dict[str, Any]]:
        """获取噪声域干扰项"""
        if len(self.noise_apis) > count:
            selected = random.sample(self.noise_apis, count)
        else:
            selected = self.noise_apis
        
        negatives = []
        for api in selected:
            negatives.append(self._build_api_node(api, api.get("domain", "noise")))
        
        return negatives
    
    # ========== 兼容旧接口 ==========
    
    def build_routing_graph(
        self, 
        correct_item: Dict[str, Any], 
        domain: str
    ) -> Dict[str, Any]:
        """
        构建路由阶段的混合图谱（兼容旧接口）
        根据 correct_item 类型自动选择构建方法
        """
        correct_type = correct_item.get("type", "api")
        
        if correct_type == "workflow":
            return self.build_workflow_graph(correct_item, domain)
        else:
            # 获取同域相关 API
            related_apis = self.scene_loader.get_domain_apis(domain)[:3]
            return self.build_api_only_graph(correct_item, related_apis, domain)
    
    def build_workflow_input_graph(
        self, 
        workflow: Dict[str, Any], 
        node: Dict[str, Any], 
        domain: str
    ) -> Dict[str, Any]:
        """
        构建工作流输入阶段的图谱（兼容旧接口）
        """
        # 获取可访问的 API 列表
        accessible_apis = self.scene_loader.get_domain_apis(domain)
        return self.build_workflow_node_graph(workflow, node, domain, accessible_apis)
    
    def build_api_call_graph(
        self, 
        api: Dict[str, Any], 
        domain: str
    ) -> Dict[str, Any]:
        """
        构建 API 调用阶段的图谱（兼容旧接口）
        """
        related_apis = self.scene_loader.get_domain_apis(domain)[:2]
        return self.build_api_only_graph(api, related_apis, domain, include_distractors=True)
