"""
公共工具函数模块
提供全局通用的工具函数，避免代码重复
"""
import time
import random
import re
import hashlib
from datetime import datetime
from typing import Optional


# 中文到英文的映射表（常用业务词汇）
CHINESE_TO_ENGLISH = {
    # 工作流相关
    "购票": "book_ticket",
    "退票": "refund_ticket",
    "改签": "change_ticket",
    "订单": "order",
    "支付": "payment",
    "流程": "flow",
    "处理": "process",
    
    # 医疗相关
    "挂号": "register",
    "就诊": "visit",
    "患者": "patient",
    "医生": "doctor",
    "预约": "appointment",
    "诊疗": "treatment",
    
    # 电商相关
    "下单": "place_order",
    "购物": "shopping",
    "商品": "product",
    "购买": "purchase",
    
    # 酒店相关
    "入住": "check_in",
    "退房": "check_out",
    "预订": "booking",
    "房间": "room",
    
    # 通用动作
    "查询": "query",
    "添加": "add",
    "删除": "delete",
    "修改": "update",
    "创建": "create",
    "提交": "submit",
    "确认": "confirm",
    "取消": "cancel",
    "审核": "review",
    "审批": "approve",
    
    # 通用名词
    "用户": "user",
    "客户": "customer",
    "员工": "employee",
    "管理": "manage",
    "系统": "system",
    "信息": "info",
    "数据": "data",
    "列表": "list",
    "详情": "detail",
}


def format_datetime(dt: Optional[datetime]) -> str:
    """
    格式化datetime为ISO 8601格式
    
    Args:
        dt: datetime对象，可以为None
        
    Returns:
        格式化后的字符串，如 "2024-01-20T10:00:00.000Z"
    """
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def generate_id(prefix: str) -> str:
    """
    生成唯一ID（时间戳格式，用于需要唯一性的场景）
    
    Args:
        prefix: ID前缀，如 "role", "entity", "workflow" 等
        
    Returns:
        格式为 "{prefix}_{timestamp}_{random}" 的唯一ID
    """
    timestamp = int(time.time() * 1000)
    random_suffix = random.randint(1000, 9999)
    return f"{prefix}_{timestamp}_{random_suffix}"


def generate_semantic_id(prefix: str, name: str, ensure_unique: bool = True) -> str:
    """
    生成语义化ID（基于名称，便于理解和调试）
    
    Args:
        prefix: ID前缀，如 "workflow", "node" 等
        name: 名称（中文或英文）
        ensure_unique: 是否添加短哈希确保唯一性
        
    Returns:
        格式为 "{prefix}_{english_slug}" 或 "{prefix}_{english_slug}_{hash}" 的ID
        
    Examples:
        generate_semantic_id("workflow", "购票流程") -> "workflow_book_ticket_flow"
        generate_semantic_id("workflow", "购票流程", True) -> "workflow_book_ticket_flow_a1b2"
    """
    # 1. 尝试将中文转换为英文
    slug = _chinese_to_slug(name)
    
    # 2. 清理和规范化
    slug = _normalize_slug(slug)
    
    # 3. 如果需要唯一性，添加短哈希
    if ensure_unique:
        # 使用时间戳和随机数生成短哈希
        unique_str = f"{time.time()}_{random.randint(0, 9999)}"
        short_hash = hashlib.md5(unique_str.encode()).hexdigest()[:4]
        return f"{prefix}_{slug}_{short_hash}"
    
    return f"{prefix}_{slug}"


def _chinese_to_slug(text: str) -> str:
    """将中文文本转换为英文 slug"""
    result = text
    
    # 按长度降序排列，优先匹配长词
    sorted_mappings = sorted(CHINESE_TO_ENGLISH.items(), key=lambda x: len(x[0]), reverse=True)
    
    for chinese, english in sorted_mappings:
        result = result.replace(chinese, f"_{english}_")
    
    return result


def _normalize_slug(text: str) -> str:
    """规范化 slug：只保留字母、数字、下划线"""
    # 移除非字母数字字符（保留下划线）
    slug = re.sub(r'[^a-zA-Z0-9_]', '_', text)
    
    # 合并多个下划线
    slug = re.sub(r'_+', '_', slug)
    
    # 移除首尾下划线
    slug = slug.strip('_')
    
    # 转小写
    slug = slug.lower()
    
    # 如果为空，返回默认值
    if not slug:
        slug = "unnamed"
    
    return slug
