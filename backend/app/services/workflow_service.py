"""工作流定义与节点维护，以及基于会话快照的执行实例管理。"""
from collections import Counter
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import re
import uuid

from sqlalchemy import func, or_
from app.core.database import get_db_session
from app.core.logging_config import get_logger
from app.core.utils import format_datetime
from app.models.workflow import WorkflowDBModel
from app.schemas.workflow import WorkflowCreateRequest, WorkflowUpdateRequest, WorkflowNodeUpdateRequest
from app.services.workflow_graph import normalize_nodes, relationships

logger = get_logger(__name__)


def normalize_status(value):
    normalized = str(getattr(value, "value", value) or "DRAFT").strip().upper()
    if normalized not in {"DRAFT", "ACTIVE", "INACTIVE", "ARCHIVED"}:
        raise ValueError("无效的工作流状态")
    return normalized


def _dump(value):
    return value.model_dump(mode="json", exclude_none=True) if hasattr(value, "model_dump") else deepcopy(value)


def _failure(error, details):
    return {"success": False, "error": error, "details": str(details)}


class WorkflowService:
    def __init__(self):
        self._session_service = None

    @property
    def sessions(self):
        if self._session_service is None:
            from app.services.workflow_session_service import workflow_session_service
            self._session_service = workflow_session_service
        return self._session_service

    def _generate_id(self, name="unnamed"):
        """短名称可作为稳定 ID；长显示名称用 UUID，避免超出数据库主键长度。"""
        if len(name) <= 50 and re.fullmatch(r"[\w-]+", name):
            return name
        return "wf_" + uuid.uuid4().hex

    def create_workflow(self, request: WorkflowCreateRequest) -> Dict[str, Any]:
        """先检查节点和连线，再以草稿状态保存定义。"""
        try:
            name = request.name.strip()
            if not name:
                raise ValueError("工作流名称不能为空")
            nodes = normalize_nodes([_dump(item) for item in request.nodes])
            with get_db_session() as db:
                workflow_id = self._generate_id(name)
                if db.query(WorkflowDBModel).filter(or_(
                    WorkflowDBModel.id == workflow_id, WorkflowDBModel.name == name
                )).first():
                    return _failure("workflow_exists", "工作流名称已存在")
                record = WorkflowDBModel(
                    id=workflow_id, name=name, description=request.description,
                    business_scenario=request.business_scenario, status="DRAFT",
                    user_intents=request.user_intents, trigger_keywords=request.trigger_keywords,
                    inputs=[_dump(item) for item in request.inputs], nodes=nodes,
                    workflow_metadata=_dump(request.metadata) or {}, created_by="developer",
                )
                db.add(record)
                db.flush()
                return {"success": True, "data": {"workflow": self._build_workflow_response(record)}}
        except ValueError as exc:
            return _failure("validation_failed", exc)
        except Exception as exc:
            logger.exception("创建工作流失败")
            return _failure("creation_failed", exc)

    def get_workflows_list(self, page=1, limit=50, status=None, business_scenario=None,
                           search=None, sort_by="created_at", sort_order="desc"):
        """分页读取定义，状态兼容历史大小写，每页只统计一次实例。"""
        try:
            if page < 1 or not 1 <= limit <= 100:
                raise ValueError("无效的分页参数")
            with get_db_session() as db:
                query = db.query(WorkflowDBModel)
                if status:
                    query = query.filter(func.upper(WorkflowDBModel.status) == normalize_status(status))
                if business_scenario:
                    query = query.filter(WorkflowDBModel.business_scenario == business_scenario)
                if search:
                    query = query.filter(or_(
                        WorkflowDBModel.name.like(f"%{search}%"),
                        WorkflowDBModel.description.like(f"%{search}%"),
                    ))
                total = query.count()
                if sort_by == "node_count":
                    length = func.json_array_length if db.bind.dialect.name == "sqlite" else func.json_length
                    column = length(WorkflowDBModel.nodes)
                else:
                    column = getattr(WorkflowDBModel, sort_by, WorkflowDBModel.created_at)
                    if sort_by not in {"name", "created_at", "updated_at"}:
                        column = WorkflowDBModel.created_at
                query = query.order_by(
                    column.asc() if sort_order == "asc" else column.desc(), WorkflowDBModel.id
                )
                records = query.offset((page - 1) * limit).limit(limit).all()
                # 每页只读取一次实例快照，避免每个工作流都全量扫描 Redis。
                counts = Counter(item.workflow_id for item in self.sessions.list_sessions()) if records else {}
                items = [self._build_workflow_response(item, counts) for item in records]
                pages = (total + limit - 1) // limit
                return {"success": True, "data": {"workflows": items, "pagination": {
                    "current_page": page, "per_page": limit, "total_count": total,
                    "total_pages": pages, "has_next": page < pages, "has_prev": page > 1,
                }}}
        except ValueError as exc:
            return _failure("validation_failed", exc)
        except Exception as exc:
            logger.exception("查询工作流列表失败")
            return _failure("query_failed", exc)

    def get_workflow_detail(self, workflow_id):
        """返回编辑器需要的完整定义和派生关系。"""
        try:
            with get_db_session() as db:
                record = db.get(WorkflowDBModel, workflow_id)
                if record is None:
                    return _failure("workflow_not_found", "工作流不存在")
                return {"success": True, "data": {"workflow": self._build_workflow_response(record)}}
        except Exception as exc:
            logger.exception("查询工作流详情失败")
            return _failure("query_failed", exc)

    def update_workflow(self, workflow_id, request: WorkflowUpdateRequest):
        """锁定定义行，先验证整张图再替换，校验失败时旧定义保持有效。"""
        try:
            with get_db_session() as db:
                record = db.query(WorkflowDBModel).filter(
                    WorkflowDBModel.id == workflow_id
                ).with_for_update().first()
                if record is None:
                    return _failure("workflow_not_found", "工作流不存在")
                changes = request.model_dump(mode="json", exclude_unset=True)
                status = normalize_status(changes.get("status") or record.status)
                nodes = [_dump(item) for item in request.nodes] if request.nodes is not None else record.nodes
                normalized = normalize_nodes(nodes, executable=status == "ACTIVE")
                if "name" in changes and changes["name"] is not None:
                    name = changes["name"].strip()
                    if not name:
                        raise ValueError("工作流名称不能为空")
                    if db.query(WorkflowDBModel).filter(
                        WorkflowDBModel.name == name, WorkflowDBModel.id != workflow_id
                    ).first():
                        return _failure("workflow_exists", "工作流名称已存在")
                    record.name = name
                for key in ("description", "business_scenario", "user_intents", "trigger_keywords", "inputs"):
                    if key in changes:
                        if changes[key] is None and key not in {"description"}:
                            raise ValueError(f"{key} 不能为 null")
                        setattr(record, key, changes[key])
                record.nodes = normalized
                record.status = status
                if "metadata" in changes:
                    record.workflow_metadata = changes["metadata"] or {}
                db.flush()
                return {"success": True, "data": {"workflow": self._build_workflow_response(record)}}
        except ValueError as exc:
            return _failure("validation_failed", exc)
        except Exception as exc:
            logger.exception("更新工作流失败")
            return _failure("update_failed", exc)

    def _edit_nodes(self, workflow_id, mutate):
        """节点增删改共用的事务入口，任何改动都重新校验并重建关系。"""
        try:
            with get_db_session() as db:
                record = db.query(WorkflowDBModel).filter(
                    WorkflowDBModel.id == workflow_id
                ).with_for_update().first()
                if record is None:
                    return _failure("workflow_not_found", "工作流不存在")
                nodes = deepcopy(record.nodes or [])
                outcome = mutate(nodes)
                if not outcome["success"]:
                    return outcome
                record.nodes = normalize_nodes(nodes, executable=normalize_status(record.status) == "ACTIVE")
                db.flush()
                return outcome
        except ValueError as exc:
            return _failure("validation_failed", exc)
        except Exception as exc:
            logger.exception("更新工作流节点失败")
            return _failure("update_failed", exc)

    def get_workflow_nodes(self, workflow_id):
        """读取规范化后的节点，供节点管理接口使用。"""
        result = self.get_workflow_detail(workflow_id)
        if not result["success"]:
            return result
        flow = result["data"]["workflow"]
        return {"success": True, "data": {
            "workflow_id": workflow_id, "nodes": flow["nodes"], "node_relationships": flow["node_relationships"],
        }}

    def add_workflow_node(self, workflow_id, request):
        """新增节点时拒绝重复 ID，并更新整张图的父子关系。"""
        def add(nodes):
            item = _dump(request)
            if any(node["id"] == item["id"] for node in nodes):
                return _failure("node_exists", "节点 ID 已存在")
            nodes.append(item)
            return {"success": True, "data": {"workflow_id": workflow_id, "node": item}}
        return self._edit_nodes(workflow_id, add)

    def update_workflow_node(self, workflow_id, node_id, request: WorkflowNodeUpdateRequest):
        """保留节点 ID；同类型节点局部配置更新时保留未修改的键。"""
        def update(nodes):
            target = next((node for node in nodes if node["id"] == node_id), None)
            if target is None:
                return _failure("node_not_found", "节点不存在")
            changes = request.model_dump(mode="json", exclude_unset=True)
            if "id" in changes and changes["id"] != node_id:
                return _failure("validation_failed", "节点 ID 不可修改")
            same_type = changes.get("type", target.get("type")) == target.get("type")
            for key in ("config", "ai_instructions"):
                if same_type and isinstance(changes.get(key), dict):
                    changes[key] = {**(target.get(key) or {}), **changes[key]}
            target.update(changes)
            target["id"] = node_id
            return {"success": True, "data": {"workflow_id": workflow_id, "node": target}}
        return self._edit_nodes(workflow_id, update)

    def delete_workflow_node(self, workflow_id, node_id):
        """删除节点时同步清理所有指向它的出边。"""
        def delete(nodes):
            if not any(node["id"] == node_id for node in nodes):
                return _failure("node_not_found", "节点不存在")
            nodes[:] = [node for node in nodes if node["id"] != node_id]
            for node in nodes:
                node["child_nodes"] = [
                    edge for edge in node.get("child_nodes") or []
                    if (edge if isinstance(edge, str) else edge.get("node_id")) != node_id
                ]
                if "nextSteps" in node:
                    node["nextSteps"] = [item for item in node["nextSteps"] if item != node_id]
            return {"success": True, "data": {"workflow_id": workflow_id, "deleted_node_id": node_id}}
        return self._edit_nodes(workflow_id, delete)

    def delete_workflow(self, workflow_id, force=False):
        """有运行实例时拒绝普通删除；显式 force 时取消实例后删除定义。"""
        try:
            with get_db_session() as db:
                record = db.get(WorkflowDBModel, workflow_id)
                if record is None:
                    return _failure("workflow_not_found", "工作流不存在")
                active = [item for item in self.sessions.list_sessions()
                          if item.workflow_id == workflow_id and item.status == "active"]
                if active and not force:
                    return _failure("has_running_instances", "工作流有正在运行的实例")
                for session in active:
                    self.sessions.end_session(session.user_id, "cancelled")
                count = len(record.nodes or [])
                db.delete(record)
                db.flush()
                return {"success": True, "data": {
                    "deleted_workflow_id": workflow_id, "deleted_nodes_count": count,
                }}
        except Exception as exc:
            logger.exception("删除工作流失败")
            return _failure("deletion_failed", exc)

    def _build_workflow_response(self, record, instance_counts=None):
        """兼容可修复的旧配置，并输出图关系、统计和校验提示。"""
        nodes = record.nodes or []
        if isinstance(nodes, str):
            nodes = json.loads(nodes)
        warnings = []
        try:
            nodes = normalize_nodes(nodes)
        except ValueError as exc:
            # 旧配置即使连线有误也尽量返回，便于从编辑器打开并修复。
            warnings.append(str(exc))
            nodes = deepcopy(nodes)
            for item in nodes:
                item["child_nodes"] = [
                    {"node_id": edge, "condition": None} if isinstance(edge, str) else edge
                    for edge in item.get("child_nodes") or []
                ]
        metadata = record.workflow_metadata or {}
        return {
            "id": record.id, "name": record.name, "description": record.description,
            "business_scenario": record.business_scenario, "status": normalize_status(record.status),
            "user_intents": record.user_intents or [], "trigger_keywords": record.trigger_keywords or [],
            "inputs": record.inputs or [], "nodes": nodes, "node_relationships": relationships(nodes),
            "metadata": metadata, "version": metadata.get("version", "1.0.0"), "node_count": len(nodes),
            "instance_count": (instance_counts.get(record.id, 0) if instance_counts is not None else
                               sum(item.workflow_id == record.id for item in self.sessions.list_sessions())),
            "created_at": format_datetime(record.created_at), "updated_at": format_datetime(record.updated_at),
            "created_by": record.created_by, "validation_errors": warnings,
        }

    def get_active_workflows_for_ai(self):
        """AI 检索只读取已启用的定义，避免分页和 Redis 实例统计拖慢召回。"""
        # AI 只需要定义，不读取实例统计，也不受编辑器分页大小限制。
        try:
            with get_db_session() as db:
                records = db.query(WorkflowDBModel).filter(
                    func.upper(WorkflowDBModel.status) == "ACTIVE"
                ).order_by(WorkflowDBModel.id).all()
                return [{
                    "workflow_id": item.id, "id": item.id, "name": item.name,
                    "description": item.description or "", "business_scenario": item.business_scenario or "",
                    "user_intents": item.user_intents or [], "inputs": item.inputs or [], "nodes": item.nodes or [],
                } for item in records]
        except Exception:
            logger.exception("查询活跃工作流失败")
            return []

    def get_workflows_for_amis(self):
        """返回已启用工作流及 AMIS 下拉选项。"""
        flows = self.get_active_workflows_for_ai()
        return {"success": True, "data": {
            "workflows": flows, "options": [{"label": flow["name"], "value": flow["id"]} for flow in flows],
        }}

    def get_amis_configuration_info(self):
        """提供表单配置需要的 API、工作流和数量摘要。"""
        from app.services.api_route_service import api_route_service
        routes = api_route_service.get_all_routes()
        flows = self.get_active_workflows_for_ai()
        return {"success": True, "data": {
            "apis": routes, "workflows": flows,
            "summary": {"api_count": len(routes), "workflow_count": len(flows)},
        }}

    @staticmethod
    def _instance_response(session):
        """把有期限的会话快照转换为实例展示数据；分支结束时完成度为 100%。"""
        steps = [item["id"] for item in session.workflow_data.get("nodes", [])
                 if item.get("type") not in {"start", "end"}]
        completed = len(set(steps) & set(session.completed_steps))
        public_data = {key: value for key, value in session.step_data.items() if not key.startswith("__")}
        return {
            "id": session.id, "workflow_id": session.workflow_id,
            "workflow_name": session.workflow_data.get("name", session.workflow_id),
            "status": "waiting" if session.status == "active" else session.status,
            "current_step": session.current_step if session.status == "active" else None,
            "progress": {"completed_steps": completed, "total_steps": len(steps),
                         "percentage": (100 if session.status == "completed" or not steps else
                                        round(100 * completed / len(steps), 2))},
            "input_data": session.input_data, "context": public_data,
            "output_data": public_data if session.status == "completed" else None,
            "started_by": session.user_id, "priority": session.priority,
            "started_at": format_datetime(session.created_at), "updated_at": format_datetime(session.updated_at),
            "completed_at": format_datetime(session.updated_at) if session.status != "active" else None,
            "execution_history": deepcopy(session.execution_history),
        }

    def get_workflow_instances(self, workflow_id=None, status=None, user_id=None, page=1, limit=20, sort="created_at"):
        """按工作流、用户和状态过滤快照，再分页返回。"""
        sessions = self.sessions.list_sessions()
        items = [self._instance_response(item) for item in sessions
                 if (workflow_id is None or item.workflow_id == workflow_id)
                 and (user_id is None or str(item.user_id) == str(user_id))]
        if status:
            wanted = "waiting" if status in {"active", "running"} else status
            items = [item for item in items if item["status"] == wanted]
        key = sort.lstrip("-")
        key = key if key in {"started_at", "updated_at", "status"} else "started_at"
        items.sort(key=lambda item: item.get(key) or "", reverse=True)
        total = len(items)
        return {"success": True, "data": {
            "instances": items[(page - 1) * limit:page * limit],
            "pagination": {"current_page": page, "per_page": limit, "total_count": total,
                           "total_pages": (total + limit - 1) // limit},
        }}

    def get_workflow_instance_detail(self, instance_id):
        """读取指定实例；TTL 过期后明确返回不存在。"""
        session = self.sessions.get_instance(instance_id)
        if session is None:
            return _failure("instance_not_found", "工作流实例不存在或已过期")
        return {"success": True, "data": {"instance": self._instance_response(session)}}

    async def execute_workflow(self, workflow_id, request, started_by):
        """创建新实例并进入实际开始节点，自动步骤推进到等待表单或结束。"""
        from app.services.workflow_execution_service import workflow_execution_service
        detail = self.get_workflow_detail(workflow_id)
        if not detail["success"]:
            return detail
        flow = detail["data"]["workflow"]
        if normalize_status(flow["status"]) != "ACTIVE":
            return _failure("workflow_inactive", "请先启用工作流")
        try:
            flow["nodes"] = normalize_nodes(flow["nodes"], executable=True)
        except ValueError as exc:
            return _failure("no_start_step", exc)
        try:
            # 会话重建与旧表单的执行互斥；后续执行再次校验实例 ID。
            async with self.sessions.execution_lock(started_by):
                session = self.sessions.create_session(started_by, workflow_id, flow)
                session.input_data = deepcopy(request.input_data or {})
                session.priority = request.priority or "normal"
                session.step_data.update(session.input_data)
                self.sessions._touch(session)
                self.sessions._save_session(session)
        except (ValueError, RuntimeError) as exc:
            return _failure("execution_failed", exc)
        context = {**(request.context or {}), "user_id": started_by, "action": "next", "instance_id": session.id}
        result = await workflow_execution_service.execute_step(
            started_by, workflow_id, session.current_step, session.input_data, context
        )
        if not result.success:
            return _failure("execution_failed", result.error)
        return {"success": True, "data": {
            "instance": self._instance_response(self.sessions.get_instance(session.id)),
            "amis_schema": result.amis_schema,
        }}

    async def continue_workflow_instance(self, instance_id, action="continue", data=None, comment="", context=None):
        """只继续仍属于该用户当前会话的实例，防止旧实例提交到新流程。"""
        from app.services.workflow_execution_service import workflow_execution_service
        session = self.sessions.get_instance(instance_id)
        if session is None:
            return _failure("instance_not_found", "工作流实例不存在或已过期")
        active = self.sessions.get_active_session(session.user_id)
        if session.status != "active" or active is None or active.id != session.id:
            return _failure("instance_not_waiting", "工作流实例不在等待状态")
        node = next((item for item in session.workflow_data["nodes"] if item["id"] == session.current_step), {})
        if action == "continue":
            action = "submit" if (node.get("config") or {}).get("method", "GET").upper() != "GET" else "next"
        if action not in {"next", "submit"}:
            return _failure("validation_failed", "不支持的工作流操作")
        result = await workflow_execution_service.execute_step(
            session.user_id, session.workflow_id, session.current_step, data or {},
            {**(context or {}), "action": action, "user_id": session.user_id, "instance_id": session.id},
        )
        if not result.success:
            return _failure("execution_failed", result.error)
        return {"success": True, "data": {
            "instance": self._instance_response(self.sessions.get_instance(session.id)),
            "amis_schema": result.amis_schema,
        }}

    def cancel_workflow_instance(self, instance_id, reason="用户取消"):
        """只取消指定的当前实例，已经结束的实例不能取消后来创建的实例。"""
        session = self.sessions.get_instance(instance_id)
        if session is None:
            return _failure("instance_not_found", "工作流实例不存在或已过期")
        active = self.sessions.get_active_session(session.user_id)
        if session.status != "active" or active is None or active.id != instance_id:
            return _failure("instance_already_finished", "工作流实例已结束")
        if not self.sessions.end_session(session.user_id, "cancelled"):
            return _failure("instance_already_finished", "工作流实例已结束")
        return {"success": True, "data": {"instance": self._instance_response(self.sessions.get_instance(instance_id))}}


workflow_service = WorkflowService()
