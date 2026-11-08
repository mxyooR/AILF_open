"""统一校验工作流连线，并以有序出边为唯一来源重建父子关系。"""
from copy import deepcopy
from typing import Any, Dict, List


def normalize_nodes(nodes: List[Dict[str, Any]], *, executable: bool = False) -> List[Dict[str, Any]]:
    """草稿允许未完成的图；启用时还必须校验入口、终点和所有分支的可达性。"""
    result = deepcopy(nodes or [])
    by_id = {}
    for node in result:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not node["id"].strip():
            raise ValueError("节点必须有非空 ID")
        if node["id"] in by_id:
            raise ValueError(f"节点 ID 重复: {node['id']}")
        by_id[node["id"]] = node
        # 父节点由后面统一重建，避免前端传入的两套关系互相矛盾。
        node["parent_nodes"] = []
        node["config"] = node.get("config") or {}
        node["ai_instructions"] = node.get("ai_instructions") or {}

    for node in result:
        edges = (node.get("child_nodes") if "child_nodes" in node else node.get("nextSteps")) or []
        # 保留原始出边顺序：执行器会选择第一条满足条件的连线。
        normalized = []
        targets = set()
        for edge in edges:
            if isinstance(edge, str):
                edge = {"node_id": edge, "condition": {"type": "always", "description": ""}}
            if not isinstance(edge, dict) or edge.get("node_id") not in by_id:
                raise ValueError(f"节点 {node['id']} 的连线指向不存在的节点")
            target = edge["node_id"]
            if target in targets:
                raise ValueError(f"节点 {node['id']} 存在重复连线: {target}")
            targets.add(target)
            normalized.append(deepcopy(edge))
            by_id[target]["parent_nodes"].append(node["id"])
        node["child_nodes"] = normalized

    if executable:
        starts = [n["id"] for n in result if n.get("type") == "start"]
        ends = {n["id"] for n in result if n.get("type") == "end"}
        if len(starts) != 1 or not ends:
            raise ValueError("可执行工作流需要一个开始节点和至少一个结束节点")
        for node in result:
            if node.get("type") == "end" and node["child_nodes"]:
                raise ValueError("结束节点不能有出边")
            if node.get("type") != "end" and not node["child_nodes"]:
                raise ValueError(f"节点 {node['id']} 没有后续步骤")

        reachable, pending = set(), [starts[0]]
        while pending:
            current = pending.pop()
            if current not in reachable:
                reachable.add(current)
                pending.extend(edge["node_id"] for edge in by_id[current]["child_nodes"])
        if reachable != set(by_id):
            raise ValueError("工作流存在无法从开始节点到达的节点")

        # 再从终点反向遍历，拒绝只能循环、永远到不了终点的分支。
        can_end, pending = set(), list(ends)
        while pending:
            current = pending.pop()
            if current not in can_end:
                can_end.add(current)
                pending.extend(by_id[current]["parent_nodes"])
        if can_end != set(by_id):
            raise ValueError("工作流存在无法到达结束节点的分支")
    return result


def relationships(nodes):
    """为编辑器导出关系视图，内容完全由已规范化的节点推导。"""
    return {
        node["id"]: {
            "parents": list(node.get("parent_nodes") or []),
            "children": [edge["node_id"] for edge in node.get("child_nodes") or []],
            "conditions": [edge.get("condition") for edge in node.get("child_nodes") or []],
        }
        for node in nodes
    }
