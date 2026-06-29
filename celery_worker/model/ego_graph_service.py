"""
Ego-Graph 图裁剪服务 (Graph Pruning Service)

核心职责：接收用户上下文和全量图谱数据，通过算法筛选出最相关的"局部子图 (Ego-Graph)"

三种裁剪策略：
- 策略模式 A：基于意图的检索 (Intent-Based Retrieval) - 用户输入自然语言，无确定状态节点
- 策略模式 B：基于状态的扩展 (State-Based Expansion) - 已知用户当前节点 ID
- 策略模式 C：工作流内约束检索 (Workflow-Constrained Retrieval) - Workflow_Execute 状态下，强制只检索当前工作流关联的节点

不涉及调用生成式 LLM，纯后端算法与检索模块。
"""
import os
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict

import torch
from sentence_transformers import SentenceTransformer

from celery_worker.config import settings

from celery_worker.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# 1. Embedding 服务（向量化）
# ============================================================================

class EmbeddingService:
    """
    Embedding 向量化服务
    
    支持两种模式：
    1. 本地模型（推荐：BGE-small-zh）
    2. API 调用（可选：阿里云 DashScope）
    """
    
    _instance = None
    _is_loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.model = None
            self.device = settings.EMBEDDING_DEVICE
            self.model_path = settings.EMBEDDING_MODEL_PATH
            self.use_api = settings.EMBEDDING_USE_API
            self._initialized = True
    
    def load_model(self) -> bool:
        """加载 Embedding 模型"""
        if self._is_loaded:
            return True
        
        try:
            if self.use_api:
                logger.info("📡 使用 API 模式进行 Embedding")
                self._is_loaded = True
                return True
            
            # 本地模型加载
            if os.path.exists(self.model_path):
                logger.info(f"加载本地Embedding模型: {self.model_path}")
                self.model = SentenceTransformer(self.model_path, device=self.device)
            else:
                # 使用 Hugging Face 下载
                logger.info("从Hugging Face下载Embedding模型: BAAI/bge-small-zh-v1.5")
                self.model = SentenceTransformer('BAAI/bge-small-zh-v1.5', device=self.device)
            
            self._is_loaded = True
            logger.info(f"Embedding模型加载完成, 设备={self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Embedding模型加载失败: {e}")
            # 降级到简单的 TF-IDF 向量化
            self._is_loaded = True  # 标记为已加载，使用降级方案
            return False
    
    def encode(self, texts: List[str], normalize: bool = True) -> np.ndarray:
        """
        将文本列表转换为向量
        
        Args:
            texts: 文本列表
            normalize: 是否 L2 归一化（用于余弦相似度计算）
        
        Returns:
            向量矩阵 [N, dim]
        """
        if not self._is_loaded:
            self.load_model()
        
        if self.model is not None:
            # 使用 SentenceTransformer
            embeddings = self.model.encode(
                texts, 
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
            return np.array(embeddings)
        else:
            # 降级：使用简单的字符级向量化
            logger.warning("使用降级的字符级向量化")
            return self._fallback_encode(texts, normalize)
    
    def encode_query(self, query: str, normalize: bool = True) -> np.ndarray:
        """编码单个查询"""
        return self.encode([query], normalize)[0]
    
    def _fallback_encode(self, texts: List[str], normalize: bool = True) -> np.ndarray:
        """
        降级的向量化方案：基于字符 n-gram 的简单向量化
        """
        dim = 256  # 固定维度
        embeddings = []
        
        for text in texts:
            # 简单的字符哈希向量
            vec = np.zeros(dim, dtype=np.float32)
            for i, char in enumerate(text):
                idx = hash(char) % dim
                vec[idx] += 1.0
            
            if normalize and np.linalg.norm(vec) > 0:
                vec = vec / np.linalg.norm(vec)
            
            embeddings.append(vec)
        
        return np.array(embeddings)


# ============================================================================
# 1.5 Query 增强器（优化检索查询）
# ============================================================================

class QueryEnhancer:
    """
    Query 增强器 - 优化检索查询
    
    功能：
    1. 移除通用指令词（如"生成节点界面"）
    2. 提取并重复业务关键词
    3. 添加工作流/节点上下文
    """
    
    # 需要移除的通用指令词
    GENERIC_PHRASES = [
        "生成节点界面",
        "生成界面",
        "生成表单",
        "执行操作",
        "处理请求",
        "请帮我",
        "帮我",
        "我想",
        "我要",
        "请",
    ]
    
    # 业务关键词（用于识别和强调）
    BUSINESS_KEYWORDS = [
        "退票", "购票", "查询", "预订", "取消", "修改",
        "挂号", "就诊", "缴费", "报告", "处方",
        "订单", "支付", "退款", "发货", "收货",
        "登录", "注册", "认证", "授权",
    ]
    
    def enhance(
        self,
        original_query: str,
        workflow_name: str = None,
        node_name: str = None,
        api_description: str = None,
        repeat_count: int = 2
    ) -> str:
        """
        增强检索查询
        
        Args:
            original_query: 原始查询文本
            workflow_name: 工作流名称（可选）
            node_name: 当前节点名称（可选）
            api_description: 关联 API 的描述（可选）
            repeat_count: 关键词重复次数
        
        Returns:
            增强后的查询文本
        """
        # 1. 移除通用指令词
        enhanced = self._remove_generic_phrases(original_query)
        
        # 2. 提取业务关键词
        keywords = self._extract_business_keywords(enhanced)
        
        # 3. 添加工作流/节点上下文
        context_parts = []
        
        if workflow_name:
            context_parts.append(workflow_name)
            # 从工作流名称中提取关键词
            wf_keywords = self._extract_business_keywords(workflow_name)
            keywords.extend(wf_keywords)
        
        if node_name:
            # 重复节点名称以增加权重
            for _ in range(repeat_count):
                context_parts.append(node_name)
        
        if api_description:
            context_parts.append(api_description)
        
        # 4. 重复业务关键词
        for keyword in keywords:
            for _ in range(repeat_count):
                context_parts.append(keyword)
        
        # 5. 组合最终查询
        if context_parts:
            enhanced = f"{enhanced} {' '.join(context_parts)}"
        
        logger.debug(f"Query增强: '{original_query[:30]}...' -> '{enhanced[:50]}...'")
        return enhanced.strip()
    
    def _remove_generic_phrases(self, text: str) -> str:
        """移除通用指令词"""
        result = text
        for phrase in self.GENERIC_PHRASES:
            result = result.replace(phrase, "")
        return result.strip()
    
    def _extract_business_keywords(self, text: str) -> List[str]:
        """从文本中提取业务关键词"""
        found = []
        for keyword in self.BUSINESS_KEYWORDS:
            if keyword in text:
                found.append(keyword)
        return found


# ============================================================================
# 1.6 结果验证器（检测并修正错误检索）
# ============================================================================

class ResultValidator:
    """
    结果验证器 - 检测并修正错误检索
    
    功能：
    1. 检测低分结果
    2. 验证结果与工作流上下文的相关性
    3. 必要时注入关联 API
    """
    
    SCORE_THRESHOLD = 0.3  # 最低可接受分数
    
    def validate(
        self,
        results: List[Tuple[str, float, Dict]],
        workflow_id: str = None,
        associated_api_id: str = None,
        associated_api_data: Dict = None,
        graph_structure: 'GraphStructure' = None
    ) -> List[Tuple[str, float, Dict]]:
        """
        验证并修正检索结果
        
        Args:
            results: 检索结果 [(node_id, score, node_data), ...]
            workflow_id: 当前工作流 ID
            associated_api_id: 关联的 API ID
            associated_api_data: 关联的 API 数据
            graph_structure: 图结构（用于获取节点数据）
        
        Returns:
            验证/修正后的结果
        """
        if not results:
            # 如果结果为空且有关联 API，注入它
            if associated_api_id and associated_api_data:
                logger.warning(f"检索结果为空，注入关联API: {associated_api_id}")
                return [(associated_api_id, 1.0, associated_api_data)]
            return results
        
        validated_results = list(results)
        
        # 1. 检查 top 结果的分数
        top_score = results[0][1] if results else 0
        
        if top_score < self.SCORE_THRESHOLD:
            logger.warning(f"Top结果分数过低: {top_score:.4f} < {self.SCORE_THRESHOLD}")
            
            # 如果有关联 API，注入到结果中
            if associated_api_id and associated_api_data:
                # 检查关联 API 是否已在结果中
                existing_ids = [r[0] for r in validated_results]
                if associated_api_id not in existing_ids:
                    logger.info(f"注入关联API: {associated_api_id}")
                    validated_results.insert(0, (associated_api_id, 1.0, associated_api_data))
                else:
                    # 提升关联 API 的排名
                    for i, (node_id, score, data) in enumerate(validated_results):
                        if node_id == associated_api_id:
                            validated_results.pop(i)
                            validated_results.insert(0, (node_id, max(score, 0.9), data))
                            logger.info(f"提升关联API排名: {associated_api_id}")
                            break
        
        # 2. 检查结果与工作流上下文的相关性
        if workflow_id:
            mismatched = []
            for node_id, score, data in validated_results[:3]:  # 只检查 top 3
                node_type = data.get('type', '')
                # 检查是否是其他工作流的节点
                if node_type == 'workflow' and node_id != workflow_id:
                    mismatched.append((node_id, score))
                elif node_type == 'workflow_node' and not node_id.startswith(workflow_id):
                    mismatched.append((node_id, score))
            
            if mismatched:
                logger.warning(f"检测到与当前工作流不匹配的节点: {mismatched}")
        
        # 3. 确保关联 API 在 top 3 中
        if associated_api_id:
            top_3_ids = [r[0] for r in validated_results[:3]]
            if associated_api_id not in top_3_ids:
                # 查找关联 API 在结果中的位置
                for i, (node_id, score, data) in enumerate(validated_results):
                    if node_id == associated_api_id:
                        # 移动到 top 3
                        validated_results.pop(i)
                        validated_results.insert(2, (node_id, max(score, 0.8), data))
                        logger.info(f"将关联API移动到top3: {associated_api_id}")
                        break
                else:
                    # 关联 API 不在结果中，需要注入
                    if associated_api_data:
                        validated_results.insert(2, (associated_api_id, 0.8, associated_api_data))
                        logger.info(f"注入关联API到top3: {associated_api_id}")
        
        return validated_results
    
    def _inject_associated_api(
        self,
        results: List[Tuple[str, float, Dict]],
        api_id: str,
        api_data: Dict,
        position: int = 0
    ) -> List[Tuple[str, float, Dict]]:
        """
        注入关联 API 到结果中
        
        Args:
            results: 原始结果
            api_id: API ID
            api_data: API 数据
            position: 插入位置
        
        Returns:
            注入后的结果
        """
        new_results = list(results)
        new_results.insert(position, (api_id, 1.0, api_data))
        return new_results


# ============================================================================
# 2. 向量索引（用于相似度搜索）
# ============================================================================

class VectorIndex:
    """
    向量索引服务
    
    支持：
    1. 内存索引（默认）
    2. Faiss 索引（大规模数据，可选）
    """
    
    def __init__(self):
        self.embeddings: Optional[np.ndarray] = None  # [N, dim]
        self.node_ids: List[str] = []
        self.node_data: Dict[str, Dict] = {}  # id -> node_data
        self.is_built = False
    
    def build_index(
        self, 
        nodes: List[Dict[str, Any]], 
        embedding_service: EmbeddingService,
        entry_types: List[str] = None
    ) -> None:
        """
        构建向量索引
        
        Args:
            nodes: 图谱节点列表
            embedding_service: Embedding 服务
            entry_types: 入口节点类型（默认 ['api', 'workflow']）
        """
        if entry_types is None:
            entry_types = ['api', 'workflow']
        
        # 筛选入口节点
        entry_nodes = [n for n in nodes if n.get('type') in entry_types]
        
        if not entry_nodes:
            logger.warning("没有找到入口节点，索引为空")
            self.is_built = True
            return
        
        # 构建节点描述文本
        texts = []
        self.node_ids = []
        self.node_data = {}
        
        for node in entry_nodes:
            node_id = node.get('id', '')
            # 组合多个字段作为描述
            desc_parts = [
                node.get('desc', ''),
                node.get('name', ''),
                node.get('path', ''),
                ' '.join([f.get('name', '') for f in node.get('request', [])[:5]])
            ]
            text = ' '.join(filter(None, desc_parts))
            
            if text.strip():
                texts.append(text)
                self.node_ids.append(node_id)
                self.node_data[node_id] = node
        
        if not texts:
            logger.warning("所有入口节点描述为空，索引为空")
            self.is_built = True
            return
        
        # 向量化
        logger.info(f"构建向量索引: {len(texts)}个入口节点")
        self.embeddings = embedding_service.encode(texts, normalize=True)
        self.is_built = True
        logger.info(f"向量索引构建完成, 维度={self.embeddings.shape}")
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 5
    ) -> List[Tuple[str, float, Dict]]:
        """
        向量相似度搜索
        
        Args:
            query_embedding: 查询向量 [dim]
            top_k: 返回的最大数量
        
        Returns:
            [(node_id, score, node_data), ...]
        """
        if not self.is_built or self.embeddings is None or len(self.embeddings) == 0:
            return []
        
        # 余弦相似度（向量已归一化，点积 = 余弦相似度）
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        scores = np.dot(self.embeddings, query_embedding.T).flatten()
        
        # Top-K
        k = min(top_k, len(scores))
        top_indices = np.argsort(scores)[-k:][::-1]
        
        results = []
        for idx in top_indices:
            node_id = self.node_ids[idx]
            score = float(scores[idx])
            node_data = self.node_data.get(node_id, {})
            results.append((node_id, score, node_data))
        
        return results


# ============================================================================
# 3. 图结构管理（邻接表 + BFS 遍历）
# ============================================================================

class GraphStructure:
    """
    图结构管理器
    
    维护节点邻接关系，支持 BFS 遍历获取邻居
    """
    
    def __init__(self):
        self.nodes: Dict[str, Dict] = {}  # id -> node_data
        self.adjacency: Dict[str, Set[str]] = defaultdict(set)  # id -> neighbor_ids
        self.reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)  # 反向边
    
    def build_from_graph_data(self, graph_data: Dict[str, Any]) -> None:
        """
        从全量图谱数据构建图结构
        
        Args:
            graph_data: {"nodes": [...], "edges": [...]}
        """
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        
        # 建立节点索引
        self.nodes = {n.get('id', ''): n for n in nodes if n.get('id')}
        
        # 建立边关系
        for edge in edges:
            source = edge.get('source', edge.get('from', ''))
            target = edge.get('target', edge.get('to', ''))
            if source and target:
                self.adjacency[source].add(target)
                self.reverse_adjacency[target].add(source)
        
        # 隐式边：从节点结构推断（API -> Field, WorkflowNode -> Field）
        self._infer_implicit_edges(nodes)
        
        logger.info(f"图结构构建完成: {len(self.nodes)}节点, {sum(len(v) for v in self.adjacency.values())}边")
    
    def _infer_implicit_edges(self, nodes: List[Dict]) -> None:
        """
        推断隐式边关系
        
        - API 节点 -> 其 request 参数作为 field 子节点
        - WorkflowNode -> 其 fields 配置作为 field 子节点
        """
        for node in nodes:
            node_id = node.get('id', '')
            node_type = node.get('type', '')
            
            if node_type == 'api':
                # API 的 request 参数
                for param in node.get('request', []):
                    param_name = param.get('name', '')
                    # 查找是否存在对应的 field 节点
                    field_id = f"{node_id}_field_{param_name}"
                    if field_id in self.nodes:
                        self.adjacency[node_id].add(field_id)
                        self.reverse_adjacency[field_id].add(node_id)
                    else:
                        # 创建虚拟 field 节点
                        self.nodes[field_id] = {
                            "id": field_id,
                            "type": "field",
                            "name": param_name,
                            "label": param.get('label', param_name),
                            "field_type": param.get('type', 'string'),
                            "required": param.get('required', False),
                            "_virtual": True
                        }
                        self.adjacency[node_id].add(field_id)
                        self.reverse_adjacency[field_id].add(node_id)
            
            elif node_type == 'workflow_node':
                # WorkflowNode 的 fields 配置已在转换时处理
                # 查找以该节点 ID 为前缀的 field 节点
                prefix = f"{node_id}_field_"
                for other_id in self.nodes:
                    if other_id.startswith(prefix):
                        self.adjacency[node_id].add(other_id)
                        self.reverse_adjacency[other_id].add(node_id)
    
    def get_neighbors(
        self, 
        node_id: str, 
        hops: int = 1, 
        include_reverse: bool = True
    ) -> Set[str]:
        """
        BFS 获取 N-Hop 邻居
        
        Args:
            node_id: 中心节点 ID
            hops: 跳数
            include_reverse: 是否包含反向邻居
        
        Returns:
            邻居节点 ID 集合
        """
        if node_id not in self.nodes:
            return set()
        
        visited = {node_id}
        frontier = {node_id}
        
        for _ in range(hops):
            new_frontier = set()
            for nid in frontier:
                # 正向邻居
                new_frontier.update(self.adjacency.get(nid, set()))
                # 反向邻居
                if include_reverse:
                    new_frontier.update(self.reverse_adjacency.get(nid, set()))
            
            new_frontier -= visited
            visited.update(new_frontier)
            frontier = new_frontier
        
        return visited - {node_id}
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """获取节点数据"""
        return self.nodes.get(node_id)
    
    def get_nodes_by_type(self, node_type: str) -> List[Dict]:
        """
        获取指定类型的所有节点
        
        Args:
            node_type: 节点类型 (api, workflow, field, workflow_node 等)
        
        Returns:
            匹配类型的节点列表
        """
        return [n for n in self.nodes.values() if n.get('type') == node_type]
    
    def get_subgraph(self, node_ids: Set[str]) -> Dict[str, Any]:
        """
        提取子图
        
        Args:
            node_ids: 节点 ID 集合
        
        Returns:
            {"nodes": [...], "edges": [...]}
        """
        # 提取节点
        nodes = [self.nodes[nid] for nid in node_ids if nid in self.nodes]
        
        # 提取边（只保留两端都在子图中的边）
        edges = []
        for source in node_ids:
            for target in self.adjacency.get(source, set()):
                if target in node_ids:
                    edges.append({"source": source, "target": target})
        
        return {"nodes": nodes, "edges": edges}


# ============================================================================
# 4. 工作流节点索引（用于策略 C 的快速查询）
# ============================================================================

class WorkflowNodeIndex:
    """
    工作流节点索引 - 支持 O(1) 查询工作流关联的节点
    
    用于策略 C（工作流内约束检索），快速获取某个工作流关联的所有节点
    """
    
    def __init__(self):
        self.workflow_to_nodes: Dict[str, Set[str]] = {}  # workflow_id -> node_ids
        self.workflow_to_apis: Dict[str, Set[str]] = {}   # workflow_id -> api_ids
        self.node_to_workflows: Dict[str, Set[str]] = {}  # node_id -> workflow_ids
    
    def build_from_graph(self, graph_data: Dict[str, Any]) -> None:
        """
        从图谱数据构建索引
        
        Args:
            graph_data: {"nodes": [...], "edges": [...]}
        """
        self.workflow_to_nodes.clear()
        self.workflow_to_apis.clear()
        self.node_to_workflows.clear()
        
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        
        # 建立节点 ID -> 节点数据的映射
        node_map = {n.get('id', ''): n for n in nodes if n.get('id')}
        
        # 1. 找出所有 workflow 节点
        workflow_nodes = [n for n in nodes if n.get('type') == 'workflow']
        
        for wf_node in workflow_nodes:
            wf_id = wf_node.get('id', '')
            if not wf_id:
                continue
            
            self.workflow_to_nodes[wf_id] = {wf_id}  # 包含自身
            self.workflow_to_apis[wf_id] = set()
        
        # 2. 遍历所有节点，找出 workflow_node 类型的节点
        for node in nodes:
            node_id = node.get('id', '')
            node_type = node.get('type', '')
            
            if node_type == 'workflow_node':
                # workflow_node 的 ID 格式通常是 "{workflow_id}_node_{node_name}"
                # 尝试从 ID 中提取 workflow_id
                workflow_id = self._extract_workflow_id_from_node(node_id, node)
                
                if workflow_id and workflow_id in self.workflow_to_nodes:
                    self.workflow_to_nodes[workflow_id].add(node_id)
                    self._add_node_to_workflow_mapping(node_id, workflow_id)
                    
                    # 如果是 api_call 类型的节点，记录关联的 API
                    if node.get('node_type') == 'api_call':
                        api_id = node.get('api_id', '')
                        if api_id:
                            self.workflow_to_apis[workflow_id].add(api_id)
                            self.workflow_to_nodes[workflow_id].add(api_id)
            
            elif node_type == 'field':
                # field 节点可能属于某个 workflow_node 或 api
                # 尝试从 ID 中提取父节点信息
                parent_workflow_id = self._extract_workflow_id_from_field(node_id)
                if parent_workflow_id and parent_workflow_id in self.workflow_to_nodes:
                    self.workflow_to_nodes[parent_workflow_id].add(node_id)
                    self._add_node_to_workflow_mapping(node_id, parent_workflow_id)
        
        # 3. 通过边关系补充索引
        for edge in edges:
            source = edge.get('source', edge.get('from', ''))
            target = edge.get('target', edge.get('to', ''))
            
            # 如果 source 是 workflow，target 是 workflow_node
            if source in self.workflow_to_nodes and target not in self.workflow_to_nodes.get(source, set()):
                target_node = node_map.get(target, {})
                if target_node.get('type') in ['workflow_node', 'field']:
                    self.workflow_to_nodes[source].add(target)
                    self._add_node_to_workflow_mapping(target, source)
        
        logger.info(f"工作流节点索引构建完成: {len(self.workflow_to_nodes)}个工作流")
        # 详细信息移到 debug 级别
        for wf_id, node_ids in self.workflow_to_nodes.items():
            api_ids = self.workflow_to_apis.get(wf_id, set())
            logger.debug(f"   - {wf_id}: {len(node_ids)} 节点, {len(api_ids)} API")
    
    def _extract_workflow_id_from_node(self, node_id: str, node: Dict) -> Optional[str]:
        """
        从 workflow_node 的 ID 或属性中提取 workflow_id
        
        ID 格式通常是: "{workflow_id}_node_{node_name}"
        """
        # 优先从节点属性中获取
        if 'workflow_id' in node:
            return node['workflow_id']
        
        # 从 ID 中解析
        if '_node_' in node_id:
            return node_id.split('_node_')[0]
        
        return None
    
    def _extract_workflow_id_from_field(self, field_id: str) -> Optional[str]:
        """
        从 field 节点的 ID 中提取 workflow_id
        
        ID 格式通常是: "{workflow_id}_node_{node_name}_field_{field_name}"
        """
        if '_node_' in field_id and '_field_' in field_id:
            return field_id.split('_node_')[0]
        return None
    
    def _add_node_to_workflow_mapping(self, node_id: str, workflow_id: str) -> None:
        """添加节点到工作流的反向映射"""
        if node_id not in self.node_to_workflows:
            self.node_to_workflows[node_id] = set()
        self.node_to_workflows[node_id].add(workflow_id)
    
    def get_nodes_by_workflow(self, workflow_id: str) -> Set[str]:
        """
        获取工作流关联的所有节点 ID
        
        Args:
            workflow_id: 工作流 ID
        
        Returns:
            节点 ID 集合
        """
        return self.workflow_to_nodes.get(workflow_id, set())
    
    def get_apis_by_workflow(self, workflow_id: str) -> Set[str]:
        """
        获取工作流关联的所有 API ID
        
        Args:
            workflow_id: 工作流 ID
        
        Returns:
            API ID 集合
        """
        return self.workflow_to_apis.get(workflow_id, set())
    
    def get_workflows_by_node(self, node_id: str) -> Set[str]:
        """
        获取节点所属的所有工作流 ID
        
        Args:
            node_id: 节点 ID
        
        Returns:
            工作流 ID 集合
        """
        return self.node_to_workflows.get(node_id, set())


# ============================================================================
# 5. Ego-Graph 主服务
# ============================================================================

class EgoGraphService:
    """
    Ego-Graph 图裁剪服务
    
    统一入口，根据输入条件自动选择裁剪策略：
    - 策略 A：基于意图的检索 (Intent-Based Retrieval)
    - 策略 B：基于状态的扩展 (State-Based Expansion)
    - 策略 C：工作流内约束检索 (Workflow-Constrained Retrieval)
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.embedding_service = EmbeddingService()
            self.vector_index = VectorIndex()
            self.graph_structure = GraphStructure()
            self.workflow_node_index = WorkflowNodeIndex()  # 新增：工作流节点索引
            self.top_k = settings.EGO_GRAPH_TOP_K
            self.hop = settings.EGO_GRAPH_HOP
            self._current_graph_hash = None
            self._initialized = True
    
    def initialize(self) -> bool:
        """初始化服务（加载 Embedding 模型）"""
        return self.embedding_service.load_model()
    
    def get_ego_graph(
        self,
        full_graph_data: Dict[str, Any],
        user_query: str = None,
        current_node_id: str = None,
        workflow_id: str = None,
        current_state: str = None,
        top_k: int = None,
        hop: int = None
    ) -> Dict[str, Any]:
        """
        获取 Ego-Graph（裁剪后的局部子图）
        
        统一入口方法，策略选择优先级：
        1. 如果 current_state == 'Workflow_Execute' 且 workflow_id 已知，使用策略 C（工作流内约束检索）
        2. 如果传入 current_node_id，使用策略 B（基于状态的扩展）
        3. 否则如果传入 user_query，使用策略 A（基于意图的检索）
        
        Args:
            full_graph_data: 全量图谱数据 {"nodes": [...], "edges": [...]}
            user_query: 用户自然语言查询（策略 A）
            current_node_id: 当前节点 ID（策略 B）
            workflow_id: 当前工作流 ID（策略 C）
            current_state: 当前状态（Global_Routing, Workflow_Input, Workflow_Execute 等）
            top_k: 覆盖默认的 Top-K 值
            hop: 覆盖默认的邻居扩展跳数
        
        Returns:
            裁剪后的子图 {"nodes": [...], "edges": [...], "strategy": "A"|"B"|"C", "core_nodes": [...]}
        """
        top_k = top_k or self.top_k
        hop = hop or self.hop
        
        # 更新图结构（如果图数据变化）
        self._update_graph_if_needed(full_graph_data)
        
        # 策略选择（按优先级）
        # 🔥 策略 C：Workflow_Execute 状态下，强制使用工作流内约束检索
        if current_state == 'Workflow_Execute' and workflow_id:
            logger.info(f"使用策略C(工作流内约束检索): workflow_id={workflow_id}, state={current_state}")
            return self._strategy_c_workflow_constrained(
                workflow_id=workflow_id,
                user_query=user_query,
                current_node_id=current_node_id,
                top_k=top_k,
                hop=hop
            )
        elif current_node_id:
            logger.info(f"使用策略B(基于状态的扩展): center={current_node_id}")
            return self._strategy_b_state_expansion(current_node_id, hop)
        elif user_query:
            logger.info(f"使用策略A(基于意图的检索): query='{user_query[:50]}...'")
            return self._strategy_a_intent_retrieval(user_query, top_k, hop)
        else:
            logger.warning("未提供user_query或current_node_id，返回空子图")
            return {"nodes": [], "edges": [], "strategy": None, "core_nodes": []}
    
    def _update_graph_if_needed(self, full_graph_data: Dict[str, Any]) -> None:
        """检查并更新图结构（避免重复构建）"""
        # 简单的哈希检查
        graph_hash = hash(json.dumps(full_graph_data, sort_keys=True, default=str))
        
        if graph_hash != self._current_graph_hash:
            logger.info("检测到图谱数据变化，重新构建索引...")
            
            # 重建图结构
            self.graph_structure.build_from_graph_data(full_graph_data)
            
            # 重建向量索引
            self.vector_index.build_index(
                nodes=full_graph_data.get('nodes', []),
                embedding_service=self.embedding_service,
                entry_types=['api', 'workflow']
            )
            
            # 🔥 新增：重建工作流节点索引（用于策略 C）
            self.workflow_node_index.build_from_graph(full_graph_data)
            
            self._current_graph_hash = graph_hash
            logger.info("图谱索引更新完成")
    
    def _strategy_a_intent_retrieval(
        self, 
        user_query: str, 
        top_k: int, 
        hop: int
    ) -> Dict[str, Any]:
        """
        策略 A：基于意图的检索
        
        流程：
        1. 将用户 query 向量化
        2. 在入口节点中搜索 Top-K 相似节点
        3. 对每个核心节点进行 N-Hop 邻居扩展
        4. 始终保留所有 Workflow 节点（让模型决定是否使用工作流）
        5. 合并构建子图
        """
        # 1. 向量化查询
        query_embedding = self.embedding_service.encode_query(user_query, normalize=True)
        
        # 2. 向量相似度搜索
        search_results = self.vector_index.search(query_embedding, top_k=top_k)
        
        if not search_results:
            logger.warning("策略A: 未找到相似节点")
            return {"nodes": [], "edges": [], "strategy": "A", "core_nodes": []}
        
        core_nodes = [r[0] for r in search_results]
        scores = {r[0]: r[1] for r in search_results}
        
        logger.info(f"策略A找到{len(core_nodes)}个核心节点")
        # 详细评分信息只在需要时输出
        if logger.isEnabledFor(5):  # 比 DEBUG 更低的级别
            for node_id, score in scores.items():
                logger.debug(f"   - {node_id}: score={score:.4f}")
        
        # 3. 邻居扩展
        all_nodes = set(core_nodes)
        for core_id in core_nodes:
            neighbors = self.graph_structure.get_neighbors(core_id, hops=hop)
            all_nodes.update(neighbors)
        
        # 4. 🔥 始终保留所有 Workflow 节点
        # Global_Routing 阶段需要让模型看到所有可用的工作流，由模型决定是否进入工作流
        workflow_nodes = self.graph_structure.get_nodes_by_type('workflow')
        workflow_ids = [n.get('id') for n in workflow_nodes]
        all_nodes.update(workflow_ids)
        
        logger.info(f"策略A扩展后: {len(all_nodes)}节点 ({len(core_nodes)}核心 + {len(workflow_ids)}Workflow + {len(all_nodes) - len(core_nodes) - len(workflow_ids)}邻居)")
        
        # 5. 提取子图
        subgraph = self.graph_structure.get_subgraph(all_nodes)
        subgraph["strategy"] = "A"
        subgraph["core_nodes"] = core_nodes
        subgraph["scores"] = scores
        
        # ========================================
        # DEBUG: 输出裁剪后的完整子图
        # ========================================
        logger.debug("=" * 80)
        logger.debug("[DEBUG] 策略A裁剪后的Ego-Graph")
        logger.debug("=" * 80)
        logger.debug(f"核心节点数量: {len(core_nodes)}")
        logger.debug(f"节点总数: {len(subgraph.get('nodes', []))}")
        # 详细节点信息只在极低日志级别显示
        if logger.isEnabledFor(5):
            for i, node in enumerate(subgraph.get('nodes', [])):
                logger.debug(f"  节点[{i}]: id={node.get('id')}, type={node.get('type')}, desc={node.get('desc', '')[:50]}")
            logger.debug(f"边: {subgraph.get('edges', [])}")
        logger.debug("=" * 80)
        
        return subgraph
    
    def _strategy_b_state_expansion(
        self, 
        current_node_id: str, 
        hop: int
    ) -> Dict[str, Any]:
        """
        策略 B：基于状态的扩展
        
        流程：
        1. 定位中心节点
        2. BFS 获取 N-Hop 邻居
        3. 构建子图
        """
        # 1. 定位中心节点
        center_node = self.graph_structure.get_node(current_node_id)
        
        if not center_node:
            logger.warning(f"策略B: 未找到节点{current_node_id}")
            return {"nodes": [], "edges": [], "strategy": "B", "core_nodes": [current_node_id]}
        
        logger.info(f"策略B中心节点: {current_node_id} (type={center_node.get('type')})")
        
        # 2. 邻居扩展
        neighbors = self.graph_structure.get_neighbors(current_node_id, hops=hop)
        all_nodes = {current_node_id} | neighbors
        
        logger.info(f"策略B扩展: 1中心 + {len(neighbors)}邻居 = {len(all_nodes)}节点")
        
        # 3. 提取子图
        subgraph = self.graph_structure.get_subgraph(all_nodes)
        subgraph["strategy"] = "B"
        subgraph["core_nodes"] = [current_node_id]
        subgraph["center_node"] = center_node
        
        # ========================================
        # DEBUG: 输出裁剪后的完整子图
        # ========================================
        logger.debug("=" * 80)
        logger.debug("[DEBUG] 策略B裁剪后的Ego-Graph")
        logger.debug("=" * 80)
        logger.debug(f"中心节点: {current_node_id}")
        logger.debug(f"节点总数: {len(subgraph.get('nodes', []))}")
        # 详细节点信息只在极低日志级别显示
        if logger.isEnabledFor(5):
            for i, node in enumerate(subgraph.get('nodes', [])):
                logger.debug(f"  节点[{i}]: id={node.get('id')}, type={node.get('type')}, desc={node.get('desc', '')[:50]}")
            logger.debug(f"边: {subgraph.get('edges', [])}")
        logger.debug("=" * 80)
        
        return subgraph
    
    def _strategy_c_workflow_constrained(
        self,
        workflow_id: str,
        user_query: str = None,
        current_node_id: str = None,
        top_k: int = 5,
        hop: int = 2
    ) -> Dict[str, Any]:
        """
        策略 C：工作流内约束检索 (Workflow-Constrained Retrieval)
        
        🔥 核心目标：在 Workflow_Execute 状态下，强制只检索当前工作流关联的节点，
        完全排除其他工作流和无关 API（如 train_search、ticket_purchase）
        
        流程：
        1. 从工作流节点索引获取当前工作流关联的所有节点 ID
        2. 硬性过滤：只保留关联节点（Workflow 节点、WorkflowNode 节点、关联的 API 节点）
        3. 如果候选节点数 < 3，扩展到域级别过滤
        4. 在过滤后的候选集中进行语义搜索（如果有 user_query）
        5. 优先返回关联的 API 节点
        
        Args:
            workflow_id: 当前工作流 ID
            user_query: 用户查询（可选，用于语义排序）
            current_node_id: 当前节点 ID（可选，用于邻居扩展）
            top_k: 返回的最大节点数
            hop: 邻居扩展跳数
        
        Returns:
            裁剪后的子图 {"nodes": [...], "edges": [...], "strategy": "C", ...}
        """
        MIN_CANDIDATES = 3  # 最小候选数量
        
        # 1. 从索引获取工作流关联的节点
        workflow_node_ids = self.workflow_node_index.get_nodes_by_workflow(workflow_id)
        workflow_api_ids = self.workflow_node_index.get_apis_by_workflow(workflow_id)
        
        logger.info(f"策略C: workflow_id={workflow_id}")
        logger.debug(f"   - 关联节点: {len(workflow_node_ids)}个")
        logger.debug(f"   - 关联API: {workflow_api_ids}")
        
        # 2. 硬性过滤：构建候选节点集
        candidate_node_ids = set(workflow_node_ids)
        
        # 添加关联的 API 节点
        for api_id in workflow_api_ids:
            candidate_node_ids.add(api_id)
            # 同时添加 API 的 field 子节点
            api_neighbors = self.graph_structure.get_neighbors(api_id, hops=1)
            for neighbor_id in api_neighbors:
                neighbor_node = self.graph_structure.get_node(neighbor_id)
                if neighbor_node and neighbor_node.get('type') == 'field':
                    candidate_node_ids.add(neighbor_id)
        
        # 如果有当前节点，添加其邻居
        if current_node_id:
            candidate_node_ids.add(current_node_id)
            neighbors = self.graph_structure.get_neighbors(current_node_id, hops=hop)
            # 只添加与当前工作流相关的邻居
            for neighbor_id in neighbors:
                neighbor_node = self.graph_structure.get_node(neighbor_id)
                if neighbor_node:
                    neighbor_type = neighbor_node.get('type', '')
                    # 只保留 field、workflow_node 类型，或者是关联的 API
                    if neighbor_type in ['field', 'workflow_node'] or neighbor_id in workflow_api_ids:
                        candidate_node_ids.add(neighbor_id)
        
        logger.debug(f"候选节点总数: {len(candidate_node_ids)}")
        
        # 3. 检查候选数量，必要时扩展
        if len(candidate_node_ids) < MIN_CANDIDATES:
            logger.warning(f"策略C: 候选节点数({len(candidate_node_ids)}) < {MIN_CANDIDATES}，扩展到域级别")
            # 扩展：添加当前工作流节点本身
            workflow_node = self.graph_structure.get_node(workflow_id)
            if workflow_node:
                candidate_node_ids.add(workflow_id)
                # 添加工作流的直接邻居
                wf_neighbors = self.graph_structure.get_neighbors(workflow_id, hops=1)
                candidate_node_ids.update(wf_neighbors)
        
        # 4. 构建核心节点列表（用于返回）
        core_nodes = []
        scores = {}
        
        # 优先添加关联的 API
        for api_id in workflow_api_ids:
            if api_id in candidate_node_ids:
                core_nodes.append(api_id)
                scores[api_id] = 1.0  # 关联 API 给最高分
        
        # 如果有 user_query，在候选集中进行语义搜索
        if user_query and self.vector_index.is_built:
            query_embedding = self.embedding_service.encode_query(user_query, normalize=True)
            
            # 在候选节点中搜索
            candidate_nodes_data = [
                self.graph_structure.get_node(nid) 
                for nid in candidate_node_ids 
                if self.graph_structure.get_node(nid)
            ]
            
            # 只对 API 和 workflow_node 类型进行语义搜索
            searchable_nodes = [
                n for n in candidate_nodes_data 
                if n.get('type') in ['api', 'workflow_node', 'workflow']
            ]
            
            if searchable_nodes:
                # 构建临时向量索引
                texts = []
                node_ids_for_search = []
                for node in searchable_nodes:
                    node_id = node.get('id', '')
                    desc_parts = [
                        node.get('desc', ''),
                        node.get('name', ''),
                        node.get('path', '')
                    ]
                    text = ' '.join(filter(None, desc_parts))
                    if text.strip():
                        texts.append(text)
                        node_ids_for_search.append(node_id)
                
                if texts:
                    embeddings = self.embedding_service.encode(texts, normalize=True)
                    search_scores = np.dot(embeddings, query_embedding.T).flatten()
                    
                    # 按分数排序
                    sorted_indices = np.argsort(search_scores)[::-1]
                    for idx in sorted_indices[:top_k]:
                        node_id = node_ids_for_search[idx]
                        score = float(search_scores[idx])
                        if node_id not in core_nodes:
                            core_nodes.append(node_id)
                            scores[node_id] = score
        
        # 如果没有 user_query，直接使用候选节点
        if not core_nodes:
            # 优先添加 workflow_node 类型
            for nid in candidate_node_ids:
                node = self.graph_structure.get_node(nid)
                if node and node.get('type') == 'workflow_node':
                    core_nodes.append(nid)
                    scores[nid] = 0.5
            # 再添加其他类型
            for nid in candidate_node_ids:
                if nid not in core_nodes:
                    core_nodes.append(nid)
                    scores[nid] = 0.3
        
        # 5. 提取子图
        subgraph = self.graph_structure.get_subgraph(candidate_node_ids)
        subgraph["strategy"] = "C"
        subgraph["core_nodes"] = core_nodes[:top_k]
        subgraph["scores"] = scores
        subgraph["workflow_id"] = workflow_id
        subgraph["workflow_apis"] = list(workflow_api_ids)
        
        # 统计信息
        api_count = len([n for n in subgraph['nodes'] if n.get('type') == 'api'])
        wf_node_count = len([n for n in subgraph['nodes'] if n.get('type') == 'workflow_node'])
        field_count = len([n for n in subgraph['nodes'] if n.get('type') == 'field'])
        
        logger.info(f"策略 C 结果: {len(subgraph['nodes'])} 节点 ({api_count} API + {wf_node_count} WorkflowNode + {field_count} Field)")
        logger.debug(f"核心节点: {core_nodes[:5]}...")
        
        # ========================================
        # DEBUG: 输出裁剪后的完整子图
        # ========================================
        logger.debug("=" * 80)
        logger.debug("策略 C 裁剪后的 Ego-Graph (工作流内约束)")
        logger.debug("=" * 80)
        logger.debug(f"工作流 ID: {workflow_id}")
        logger.debug(f"关联 API: {workflow_api_ids}")
        logger.debug(f"节点总数: {len(subgraph.get('nodes', []))}")
        # 详细节点信息只在极低日志级别显示
        if logger.isEnabledFor(5):
            for i, node in enumerate(subgraph.get('nodes', [])):
                node_id = node.get('id', '')
                node_type = node.get('type', '')
                node_desc = node.get('desc', '')[:50]
                is_api = '🔥' if node_id in workflow_api_ids else ''
                logger.debug(f"  节点[{i}]: {is_api} id={node_id}, type={node_type}, desc={node_desc}")
            logger.debug(f"边: {subgraph.get('edges', [])}")
        logger.debug("=" * 80)
        
        return subgraph
    
    def get_relevant_nodes_for_command(
        self,
        full_graph_data: Dict[str, Any],
        command: str,
        current_workflow_node_id: str = None,
        workflow_id: str = None,
        current_state: str = None,
        top_k: int = None
    ) -> Dict[str, Any]:
        """
        为用户命令获取相关节点（便捷方法）
        
        自动判断使用哪种策略：
        - 如果 current_state == 'Workflow_Execute' 且 workflow_id 已知 -> 策略 C
        - 如果有当前工作流节点 -> 策略 B
        - 否则 -> 策略 A
        
        Args:
            full_graph_data: 全量图谱
            command: 用户命令
            current_workflow_node_id: 当前工作流节点 ID
            workflow_id: 当前工作流 ID
            current_state: 当前状态
            top_k: Top-K 数量
        
        Returns:
            裁剪后的子图
        """
        return self.get_ego_graph(
            full_graph_data=full_graph_data,
            user_query=command if not current_workflow_node_id else None,
            current_node_id=current_workflow_node_id,
            workflow_id=workflow_id,
            current_state=current_state,
            top_k=top_k
        )


# ============================================================================
# 6. 全局单例实例
# ============================================================================

ego_graph_service = EgoGraphService()
