"""
工作流设计模块服务 (简化版)
实现工作流定义的增删改查功能
基于API文档，只处理工作流配置，不包含执行功能
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.core.database import get_db_session
from app.core.utils import format_datetime, generate_id
from app.core.logging_config import get_logger
from app.models.workflow import WorkflowDBModel, WorkflowStatus
from app.schemas.workflow import WorkflowCreateRequest, WorkflowUpdateRequest, WorkflowNodeUpdateRequest

logger = get_logger(__name__)


def normalize_status(status_value):
    """标准化状态值，将旧的小写值转换为大写"""
    if isinstance(status_value, str):
        status_mapping = {
            'draft': 'DRAFT',
            'active': 'ACTIVE',
            'inactive': 'INACTIVE',
            'archived': 'ARCHIVED'
        }
        return status_mapping.get(status_value.lower(), status_value.upper())
    return status_value


class WorkflowService:
    """工作流服务 (简化版)"""
    
    def _generate_id(self, name: str = "unnamed") -> str:
        """直接使用工作流名称作为ID（语义化，与数据集一致）"""
        return name
    
    def create_workflow(self, request: WorkflowCreateRequest) -> Dict[str, Any]:
        """创建工作流定义"""
        try:
            logger.info(f"开始创建工作流: {request.name}")
            
            with get_db_session() as db:
                # 🔥 直接使用 name 作为 workflow_id（语义化）
                workflow_id = request.name
                logger.debug(f"工作流ID: {workflow_id}")
                
                # 检查是否已存在
                existing = db.query(WorkflowDBModel).filter(WorkflowDBModel.id == workflow_id).first()
                if existing:
                    return {
                        "success": False,
                        "error": "workflow_exists",
                        "details": f"工作流 '{workflow_id}' 已存在"
                    }
                
                # 创建工作流记录
                db_workflow = WorkflowDBModel(
                    id=workflow_id,
                    name=request.name,
                    description=request.description,
                    business_scenario=request.business_scenario,
                    status="DRAFT",
                    user_intents=request.user_intents or [],
                    trigger_keywords=request.trigger_keywords or [],
                    inputs=[input_item.model_dump() if hasattr(input_item, 'model_dump') else input_item for input_item in (request.inputs or [])],
                    nodes=[node.model_dump() if hasattr(node, 'model_dump') else node for node in (request.nodes or [])],
                    workflow_metadata=request.metadata.model_dump() if hasattr(request.metadata, 'model_dump') else (request.metadata or {}),
                    created_by="developer"
                )
                
                db.add(db_workflow)
                db.commit()
                
                logger.info(f"✅ 工作流创建成功: {workflow_id}")
                
                return {
                    "success": True,
                    "data": {
                        "workflow": {
                            "id": workflow_id,
                            "name": request.name,
                            "status": "DRAFT",
                            "created_at": format_datetime(datetime.now()),
                            "node_count": len(request.nodes or []),
                            "complexity": "medium"
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ 创建工作流失败: {str(e)}")
            import traceback
            logger.debug(f"错误堆栈: {traceback.format_exc()}")
            return {
                "success": False,
                "error": "creation_failed",
                "details": f"创建工作流失败: {str(e)}"
            }
    
    def get_workflows_list(self, page: int = 1, limit: int = 50, status: Optional[str] = None,
                          business_scenario: Optional[str] = None, search: Optional[str] = None,
                          sort_by: str = "created_at", sort_order: str = "desc") -> Dict[str, Any]:
        """获取工作流列表"""
        try:
            logger.debug(f"查询工作流列表: page={page}, limit={limit}")
            
            with get_db_session() as db:
                # 构建查询
                query = db.query(WorkflowDBModel)
                
                # 应用筛选条件
                if status:
                    normalized_status = normalize_status(status)
                    query = query.filter(WorkflowDBModel.status == normalized_status)
                if business_scenario:
                    query = query.filter(WorkflowDBModel.business_scenario == business_scenario)
                if search:
                    search_pattern = f"%{search}%"
                    query = query.filter(
                        or_(
                            WorkflowDBModel.name.like(search_pattern),
                            WorkflowDBModel.description.like(search_pattern)
                        )
                    )
                
                # 计算总数
                total_count = query.count()
                logger.debug(f"总工作流数量: {total_count}")
                
                # 应用排序
                if sort_by == "name":
                    order_column = WorkflowDBModel.name
                elif sort_by == "updated_at":
                    order_column = WorkflowDBModel.updated_at
                else:
                    order_column = WorkflowDBModel.created_at
                
                if sort_order == "asc":
                    query = query.order_by(order_column.asc())
                else:
                    query = query.order_by(order_column.desc())
                
                # 应用分页
                offset = (page - 1) * limit

                # 使用原始SQL查询避免枚举值解析问题
                try:
                    workflows = query.offset(offset).limit(limit).all()
                except Exception as query_error:
                    logger.warning(f"⚠️ ORM查询失败，尝试原始SQL查询: {query_error}")
                    # 使用原始SQL查询
                    from sqlalchemy import text
                    sql = text("""
                        SELECT id, name, description, business_scenario, status,
                               user_intents, trigger_keywords, inputs, nodes,
                               workflow_metadata, created_by, created_at, updated_at
                        FROM workflows
                        ORDER BY created_at DESC
                        LIMIT :limit OFFSET :offset
                    """)
                    result = db.execute(sql, {"limit": limit, "offset": offset})
                    rows = result.fetchall()

                    # 手动构建工作流对象
                    workflows = []
                    for row in rows:
                        workflow_dict = {
                            'id': row[0],
                            'name': row[1],
                            'description': row[2],
                            'business_scenario': row[3],
                            'status': normalize_status(row[4]),  # 标准化状态值
                            'user_intents': row[5],
                            'trigger_keywords': row[6],
                            'inputs': row[7],
                            'nodes': row[8],
                            'workflow_metadata': row[9],
                            'created_by': row[10],
                            'created_at': row[11],
                            'updated_at': row[12]
                        }
                        workflows.append(type('Workflow', (), workflow_dict)())
                
                logger.debug(f"查询到 {len(workflows)} 个工作流")
                
                # 构建响应
                workflow_list = []
                for workflow in workflows:
                    try:
                        node_count = 0
                        if workflow.nodes:
                            node_count = len(workflow.nodes)

                        # 标准化状态值
                        status_value = normalize_status(workflow.status) if workflow.status else "DRAFT"

                        workflow_item = {
                            "id": workflow.id,
                            "name": workflow.name,
                            "description": workflow.description,
                            "business_scenario": workflow.business_scenario,
                            "status": status_value,
                            "node_count": node_count,
                            "trigger_keywords": workflow.trigger_keywords or [],
                            "user_intents": workflow.user_intents or [],
                            "created_at": format_datetime(workflow.created_at),
                            "updated_at": format_datetime(workflow.updated_at)
                        }
                        workflow_list.append(workflow_item)
                    except Exception as item_error:
                        logger.warning(f"⚠️ 跳过有问题的工作流记录 {workflow.id}: {item_error}")
                        continue
                
                # 计算分页信息
                total_pages = (total_count + limit - 1) // limit
                
                pagination = {
                    "current_page": page,
                    "per_page": limit,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
                
                return {
                    "success": True,
                    "data": {
                        "workflows": workflow_list,
                        "pagination": pagination
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ 查询工作流列表失败: {str(e)}")
            import traceback
            logger.debug(f"错误堆栈: {traceback.format_exc()}")
            return {
                "success": False,
                "error": "query_failed",
                "details": f"查询工作流列表失败: {str(e)}"
            }
    
    def get_workflow_detail(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流详情"""
        try:
            with get_db_session() as db:
                # 查询工作流
                logger.debug(f"查询工作流详情: {workflow_id}")
                db_workflow = db.query(WorkflowDBModel).filter(WorkflowDBModel.id == workflow_id).first()

                if not db_workflow:
                    logger.warning(f"⚠️ 工作流不存在: {workflow_id}")
                    return {
                        "success": False,
                        "error": "workflow_not_found",
                        "details": "工作流不存在"
                    }

                logger.debug(f"找到工作流: {db_workflow.name}")
                logger.debug(f"工作流状态: {db_workflow.status}")
                
                # 计算节点数量
                node_count = 0
                if db_workflow.nodes:
                    node_count = len(db_workflow.nodes)
                logger.debug(f"节点数量: {node_count}")

                # 构建响应
                logger.debug("开始构建工作流响应...")
                workflow = self._build_workflow_response(db_workflow)
                logger.debug("工作流响应构建成功")

                return {
                    "success": True,
                    "data": {"workflow": workflow}
                }

        except Exception as e:
            import traceback
            logger.error(f"❌ 查询工作流详情失败: {str(e)}")
            logger.debug(f"错误堆栈: {traceback.format_exc()}")
            return {
                "success": False,
                "error": "query_failed",
                "details": f"查询工作流详情失败: {str(e)}"
            }
    
    def update_workflow(self, workflow_id: str, request: WorkflowUpdateRequest) -> Dict[str, Any]:
        """更新工作流定义"""
        try:
            with get_db_session() as db:
                # 查询工作流
                db_workflow = db.query(WorkflowDBModel).filter(WorkflowDBModel.id == workflow_id).first()
                
                if not db_workflow:
                    return {
                        "success": False,
                        "error": "workflow_not_found",
                        "details": "工作流不存在"
                    }
                
                # 更新基本信息
                if request.name is not None:
                    db_workflow.name = request.name
                if request.description is not None:
                    db_workflow.description = request.description
                if request.business_scenario is not None:
                    db_workflow.business_scenario = request.business_scenario
                if request.status is not None:
                    db_workflow.status = request.status
                if request.user_intents is not None:
                    db_workflow.user_intents = request.user_intents
                if request.trigger_keywords is not None:
                    db_workflow.trigger_keywords = request.trigger_keywords
                if request.inputs is not None:
                    db_workflow.inputs = [input_item.model_dump() if hasattr(input_item, 'model_dump') else input_item for input_item in request.inputs]
                if request.nodes is not None:
                    import sys
                    logger.debug(f"[BACKEND UPDATE] 接收到节点数据，节点数: {len(request.nodes)}")
                    sys.stdout.flush()

                    # 详细检查每个节点的连线关系
                    processed_nodes = []
                    for i, node in enumerate(request.nodes):
                        node_data = node.model_dump() if hasattr(node, 'model_dump') else node
                        logger.debug(f"[BACKEND UPDATE] 处理节点{i+1}: {node_data.get('name', 'Unknown')} ({node_data.get('id', 'Unknown')})")
                        child_nodes = node_data.get('child_nodes', [])
                        parent_nodes = node_data.get('parent_nodes', [])
                        logger.debug(f"   [BACKEND UPDATE] child_nodes: {len(child_nodes)} 个 - {child_nodes}")
                        logger.debug(f"   [BACKEND UPDATE] parent_nodes: {len(parent_nodes)} 个 - {parent_nodes}")
                        processed_nodes.append(node_data)
                        sys.stdout.flush()

                    db_workflow.nodes = processed_nodes
                    logger.debug(f"[BACKEND UPDATE] 节点数据已保存到数据库")
                    sys.stdout.flush()
                if request.metadata is not None:
                    db_workflow.workflow_metadata = request.metadata.model_dump() if hasattr(request.metadata, 'model_dump') else request.metadata
                
                db.commit()
                
                return {
                    "success": True,
                    "data": {
                        "workflow": {
                            "id": workflow_id,
                            "name": db_workflow.name,
                            "status": db_workflow.status,
                            "updated_at": format_datetime(db_workflow.updated_at),
                            "node_count": len(db_workflow.nodes or [])
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ 更新工作流失败: {str(e)}")
            import traceback
            logger.debug(f"错误堆栈: {traceback.format_exc()}")
            return {
                "success": False,
                "error": "update_failed",
                "details": f"更新工作流失败: {str(e)}"
            }

    def update_workflow_node(self, workflow_id: str, node_id: str, request: WorkflowNodeUpdateRequest) -> Dict[str, Any]:
        """更新工作流中的单个节点。"""
        try:
            with get_db_session() as db:
                db_workflow = db.query(WorkflowDBModel).filter(WorkflowDBModel.id == workflow_id).first()

                if not db_workflow:
                    return {
                        "success": False,
                        "error": "workflow_not_found",
                        "details": "工作流不存在"
                    }

                nodes = db_workflow.nodes or []
                if not isinstance(nodes, list):
                    nodes = list(nodes) if nodes else []
                else:
                    nodes = list(nodes)

                target_index = None
                for idx, node in enumerate(nodes):
                    node_data = node.model_dump() if hasattr(node, "model_dump") else node
                    if isinstance(node_data, dict) and node_data.get("id") == node_id:
                        target_index = idx
                        break

                if target_index is None:
                    return {
                        "success": False,
                        "error": "node_not_found",
                        "details": "节点不存在"
                    }

                if hasattr(request, "model_dump"):
                    update_data = request.model_dump(exclude_none=True)
                else:
                    update_data = {k: v for k, v in request.__dict__.items() if v is not None}

                def _normalize_value(value: Any) -> Any:
                    if hasattr(value, "model_dump"):
                        return value.model_dump()
                    if isinstance(value, list):
                        return [
                            item.model_dump() if hasattr(item, "model_dump") else item
                            for item in value
                        ]
                    return value

                normalized_updates = {k: _normalize_value(v) for k, v in update_data.items()}

                target_node = nodes[target_index]
                if hasattr(target_node, "model_dump"):
                    target_node = target_node.model_dump()
                if not isinstance(target_node, dict):
                    target_node = {"id": node_id}

                target_node.update(normalized_updates)
                nodes[target_index] = target_node
                db_workflow.nodes = nodes
                try:
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(db_workflow, "nodes")
                except Exception:
                    pass
                db.commit()

                return {
                    "success": True,
                    "data": {
                        "workflow_id": workflow_id,
                        "node": target_node
                    }
                }

        except Exception as e:
            logger.error(f"❌ 更新节点失败: {str(e)}")
            import traceback
            logger.debug(f"错误堆栈: {traceback.format_exc()}")
            return {
                "success": False,
                "error": "update_failed",
                "details": f"更新节点失败: {str(e)}"
            }
    
    def delete_workflow(self, workflow_id: str, force: bool = False) -> Dict[str, Any]:
        """删除工作流定义"""
        try:
            logger.info(f"开始删除工作流: {workflow_id}, force={force}")

            with get_db_session() as db:
                # 查询工作流
                logger.debug(f"查询工作流: {workflow_id}")
                db_workflow = db.query(WorkflowDBModel).filter(WorkflowDBModel.id == workflow_id).first()

                if not db_workflow:
                    logger.warning(f"⚠️ 工作流不存在: {workflow_id}")
                    return {
                        "success": False,
                        "error": "workflow_not_found",
                        "details": "工作流不存在"
                    }

                logger.debug(f"找到工作流: {db_workflow.name}")

                # 工作流不执行，直接删除（无需检查实例）
                logger.debug("工作流只是配置，无需检查运行实例...")

                # 删除工作流
                workflow_name = db_workflow.name
                logger.info(f"开始删除工作流: {workflow_name}")

                db.delete(db_workflow)
                logger.debug("提交数据库事务...")
                db.commit()
                logger.info(f"✅ 工作流删除成功")

                return {
                    "success": True,
                    "data": {
                        "deleted_workflow_id": workflow_id,
                        "deleted_nodes_count": len(db_workflow.nodes or [])
                    }
                }

        except Exception as e:
            logger.error(f"❌ 删除工作流异常: {str(e)}")
            import traceback
            logger.debug(f"错误堆栈: {traceback.format_exc()}")
            return {
                "success": False,
                "error": "deletion_failed",
                "details": f"删除工作流失败: {str(e)}"
            }
    
    def _build_workflow_response(self, db_workflow: WorkflowDBModel) -> Dict[str, Any]:
        """构建工作流响应对象，完全按照API文档定义"""
        logger.debug(f"构建工作流响应: {db_workflow.id}")

        # 从JSON字段获取节点信息
        nodes = db_workflow.nodes or []
        import sys
        logger.debug(f"[BACKEND LOAD] 从数据库加载 {len(nodes)} 个节点")

        # 详细检查每个节点的连线关系
        for i, node in enumerate(nodes):
            logger.debug(f"[BACKEND LOAD] 节点{i+1}: {node.get('name', 'Unknown')} ({node.get('id', 'Unknown')})")
            child_nodes = node.get('child_nodes', [])
            parent_nodes = node.get('parent_nodes', [])
            logger.debug(f"   [BACKEND LOAD] child_nodes: {len(child_nodes)} 个 - {child_nodes}")
            logger.debug(f"   [BACKEND LOAD] parent_nodes: {len(parent_nodes)} 个 - {parent_nodes}")
        sys.stdout.flush()

        # 安全地获取状态值，处理字符串状态
        raw_status = str(db_workflow.status) if db_workflow.status else "DRAFT"
        status_mapping = {
            'draft': 'DRAFT',
            'active': 'ACTIVE',
            'inactive': 'INACTIVE',
            'archived': 'ARCHIVED'
        }
        status_value = status_mapping.get(raw_status.lower(), raw_status.upper())

        # 🔥 构建 node_relationships（从节点的 parent_nodes 和 child_nodes 提取）
        node_relationships = {}
        for node in nodes:
            node_id = node.get('id', '')
            if node_id:
                # 提取子节点 ID 列表
                children = []
                child_nodes = node.get('child_nodes', [])
                for child in child_nodes:
                    if isinstance(child, dict):
                        children.append(child.get('node_id', ''))
                    elif isinstance(child, str):
                        children.append(child)
                
                # 提取父节点 ID 列表
                parents = node.get('parent_nodes', [])
                if not isinstance(parents, list):
                    parents = [parents] if parents else []
                
                # 提取条件列表
                conditions = []
                for child in child_nodes:
                    if isinstance(child, dict) and 'condition' in child:
                        conditions.append(child['condition'])
                
                node_relationships[node_id] = {
                    "children": children,
                    "parents": parents,
                    "conditions": conditions
                }

        # 构建工作流响应数据 (基于API文档)
        workflow_data = {
            "id": db_workflow.id,
            "name": db_workflow.name,
            "description": db_workflow.description,
            "business_scenario": db_workflow.business_scenario,
            "status": status_value,
            "user_intents": db_workflow.user_intents or [],
            "trigger_keywords": db_workflow.trigger_keywords or [],
            "inputs": db_workflow.inputs or [],
            "nodes": nodes,
            "node_relationships": node_relationships,  # 🔥 添加节点关系映射
            "metadata": db_workflow.workflow_metadata or {},
            "created_at": format_datetime(db_workflow.created_at),
            "updated_at": format_datetime(db_workflow.updated_at),
            "created_by": db_workflow.created_by
        }
        
        logger.debug(f"工作流响应构建完成: {workflow_data['name']}, 节点关系: {len(node_relationships)} 个")
        return workflow_data


    def get_active_workflows_for_ai(self) -> List[Dict[str, Any]]:
        """
        获取活跃的工作流列表供 AI 图谱使用
        
        返回格式与数据集一致：
        {
            "workflow_id": "workflow_xxx",
            "name": "购票流程",
            "description": "完整的在线购票业务流程",
            "business_scenario": "railway_ticketing",
            "user_intents": ["买票", "订火车票"],
            "inputs": [...],  # 🔥 工作流输入字段定义（包含选项）
            "nodes": [...]  # 🔥 工作流的所有节点
        }
        """
        try:
            with get_db_session() as db:
                query = db.query(WorkflowDBModel).filter(
                    WorkflowDBModel.status == "ACTIVE"
                )
                
                workflows = query.all()
                
                result = []
                for wf in workflows:
                    # 🔥 直接使用 wf.nodes（JSON 字段），而不是 wf.workflow_data
                    nodes = wf.nodes or []
                    inputs = wf.inputs or []  # 🔥 获取工作流输入定义
                    
                    result.append({
                        "workflow_id": wf.id,
                        "id": wf.id,  # 兼容依赖 workflow.id 的旧逻辑
                        "name": wf.name,
                        "description": wf.description or "",
                        "business_scenario": wf.business_scenario or "",
                        "user_intents": wf.user_intents or [],
                        "inputs": inputs,  # 🔥 包含工作流输入字段定义
                        "nodes": nodes  # 🔥 包含工作流的所有节点
                    })
                    
                    logger.debug(f"工作流 {wf.id} ({wf.name}): {len(nodes)} 个节点")
                
                logger.info(f"获取 {len(result)} 个活跃工作流供 AI 使用")
                return result
                
        except Exception as e:
            logger.error(f"❌ 获取活跃工作流失败: {str(e)}")
            import traceback
            logger.debug(f"错误堆栈: {traceback.format_exc()}")
            return []


# 创建全局实例
workflow_service = WorkflowService()
