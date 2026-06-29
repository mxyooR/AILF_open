"""
AI核心模块
V9 纯 LLM 两轮对话架构
- 移除 GNN 图谱编码
- 保留 BGE 召回（扩大 topk）
- 两轮对话：选择 + 生成
"""

# V9 纯 LLM 模型服务
from .pure_llm_model_service import (
    PureLLMModelService,
    EndpointValidator,
    pure_llm_model_service,
    init_pure_llm_model
)

# 图裁剪服务（BGE 召回）
from .ego_graph_service import (
    EgoGraphService,
    EmbeddingService,
    VectorIndex,
    GraphStructure,
    ego_graph_service
)

# 保留旧的异常类以保持兼容性
class BailianAPIError(Exception):
    """描述 API 错误（保持兼容性，已废弃）"""
    pass


__all__ = [
    # V9 纯 LLM 模型
    "PureLLMModelService",
    "EndpointValidator",
    "pure_llm_model_service",
    "init_pure_llm_model",
    # BGE 召回服务
    "EgoGraphService",
    "EmbeddingService",
    "VectorIndex",
    "GraphStructure",
    "ego_graph_service",
    # 兼容性
    "BailianAPIError"
]
