"""
工作流设计模块API路由 (AI指导版)
实现工作流定义、节点管理的9个API端点
专门为AI提供业务流程指导和API调用指南
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any

from app.core.auth import verify_developer_token
from app.api.v1.user_auth import get_current_user
from app.schemas.workflow import (
    WorkflowCreateRequest, WorkflowUpdateRequest, WorkflowExecuteRequest,
    WorkflowNodeCreateRequest, WorkflowNodeUpdateRequest
)
from app.services.workflow_service import workflow_service
from app.core.response import UnifiedResponse

router = APIRouter(tags=["工作流设计模块"])


# 工作流管理 (5个API端点)

@router.post("/workflow", status_code=status.HTTP_201_CREATED)
async def create_workflow(
    request: WorkflowCreateRequest,
    _: dict = Depends(verify_developer_token)
):
    """
    创建工作流定义 (AI指导版)

    创建新的工作流定义，包括节点配置、父子关系和AI执行指令。
    """
    result = workflow_service.create_workflow(request)

    if not result["success"]:
        if result["error"] == "creation_failed":
            raise UnifiedResponse.bad_request(
                message="创建工作流失败",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="创建工作流失败",
                error_type=result["error"],
                details=result["details"]
            )

    return UnifiedResponse.created(
        message="工作流创建成功",
        data=result["data"]
    )


@router.get("/workflow")
async def get_workflows_list(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    limit: int = Query(50, ge=1, le=100, description="每页数量，最大100"),
    status: Optional[str] = Query(None, description="工作流状态筛选：active, draft, inactive"),
    business_scenario: Optional[str] = Query(None, description="业务场景筛选"),
    search: Optional[str] = Query(None, description="搜索关键词（匹配名称和描述）"),
    sort_by: str = Query("created_at", description="排序字段：name, created_at, updated_at, node_count"),
    sort_order: str = Query("desc", description="排序方向：asc, desc"),
    _: dict = Depends(verify_developer_token)
):
    """
    获取工作流列表

    获取工作流列表，支持分页、筛选和排序。用于在开发者配置面板中显示所有可用的工作流。
    """
    result = workflow_service.get_workflows_list(
        page=page,
        limit=limit,
        status=status,
        business_scenario=business_scenario,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    if not result["success"]:
        raise UnifiedResponse.internal_error(
            message="获取工作流列表失败",
            error_type=result.get("error", "internal_error"),
            details=result["details"]
        )
    
    return UnifiedResponse.success(
        message="获取工作流列表成功",
        data=result["data"]
    )


# 工作流执行管理 (5个API端点) - 需要在{workflow_id}路由之前定义

@router.get("/workflow/instances")
async def get_workflow_instances(
    workflow_id: Optional[str] = Query(None, description="筛选特定工作流的实例"),
    status: Optional[str] = Query(None, description="筛选实例状态"),
    user_id: Optional[str] = Query(None, description="筛选特定用户的实例"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    sort: str = Query("created_at", description="排序字段"),
    _: dict = Depends(verify_developer_token)
):
    """
    获取工作流实例列表

    获取工作流实例列表，支持按状态、时间等条件筛选。
    """
    result = workflow_service.get_workflow_instances(workflow_id, status, user_id, page, limit, sort)

    if not result["success"]:
        raise UnifiedResponse.internal_error(
            message="获取工作流实例列表失败",
            error_type=result.get("error", "internal_error"),
            details=result["details"]
        )

    return UnifiedResponse.success(
        message="获取工作流实例列表成功",
        data=result["data"]
    )


@router.get("/workflow/instances/{instance_id}")
async def get_workflow_instance_detail(
    instance_id: str,
    _: dict = Depends(verify_developer_token)
):
    """
    获取工作流实例详情

    获取特定工作流实例的详细信息，包括执行历史和当前状态。
    """
    result = workflow_service.get_workflow_instance_detail(instance_id)

    if not result["success"]:
        if result["error"] == "instance_not_found":
            raise UnifiedResponse.not_found(
                message="工作流实例不存在",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="获取工作流实例详情失败",
                error_type=result["error"],
                details=result["details"]
            )

    return UnifiedResponse.success(
        message="获取工作流实例详情成功",
        data=result["data"]
    )


@router.get("/workflow/{workflow_id}")
async def get_workflow_detail(
    workflow_id: str,
    _: dict = Depends(verify_developer_token)
):
    """
    获取特定工作流详情

    获取指定工作流的详细信息，包括完整的步骤配置。
    """
    result = workflow_service.get_workflow_detail(workflow_id)

    if not result["success"]:
        if result["error"] == "workflow_not_found":
            raise UnifiedResponse.not_found(
                message="工作流不存在",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="获取工作流详情失败",
                error_type=result["error"],
                details=result["details"]
            )

    return UnifiedResponse.success(
        message="获取工作流详情成功",
        data=result["data"]
    )


@router.put("/workflow/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    request: WorkflowUpdateRequest,
    _: dict = Depends(verify_developer_token)
):
    """
    更新工作流定义

    更新指定工作流的配置信息，包括步骤和条件。
    """
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)
    
    try:
        logger.info(f"🔍 收到工作流更新请求: workflow_id={workflow_id}")
        logger.debug(f"📝 请求数据: {request.model_dump()}")

        # 检查节点数据
        if hasattr(request, 'nodes') and request.nodes:
            logger.info(f"📊 接收到 {len(request.nodes)} 个节点")
            for i, node in enumerate(request.nodes):
                node_data = node.model_dump() if hasattr(node, 'model_dump') else node
                logger.debug(f"📊 节点{i+1}: {node_data.get('name', 'Unknown')} ({node_data.get('id', 'Unknown')})")
        else:
            logger.debug(f"⚠️ 没有节点数据或nodes为空")

        result = workflow_service.update_workflow(workflow_id, request)

        if not result["success"]:
            logger.error(f"❌ 工作流更新失败: {result}")
            if result["error"] == "workflow_not_found":
                raise UnifiedResponse.not_found(
                    message="工作流不存在",
                    error_type=result["error"],
                    details=result["details"]
                )
            elif result["error"] == "update_failed":
                raise UnifiedResponse.bad_request(
                    message="工作流更新失败",
                    error_type=result["error"],
                    details=result["details"]
                )
            else:
                raise UnifiedResponse.internal_error(
                    message="工作流更新失败",
                    error_type=result["error"],
                    details=result["details"]
                )

        logger.info(f"✅ 工作流更新成功: {result['data']}")
        return UnifiedResponse.success(
            message="工作流更新成功",
            data=result["data"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 工作流更新异常: {str(e)}")
        raise


@router.delete("/workflow/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    force: bool = Query(False, description="是否强制删除"),
    _: dict = Depends(verify_developer_token)
):
    """
    删除工作流定义

    删除指定的工作流定义及其相关数据。
    """
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)
    
    logger.info(f"🌐 收到删除工作流请求: {workflow_id}, force={force}")

    try:
        result = workflow_service.delete_workflow(workflow_id, force)
        logger.debug(f"📋 Service返回结果: {result}")

        if not result["success"]:
            logger.error(f"❌ 删除失败: {result['error']} - {result['details']}")
            if result["error"] == "workflow_not_found":
                raise UnifiedResponse.not_found(
                    message="工作流不存在",
                    error_type=result["error"],
                    details=result["details"]
                )
            elif result["error"] == "has_running_instances":
                raise UnifiedResponse.conflict(
                    message="工作流有正在运行的实例,无法删除",
                    error_type=result["error"],
                    details=result["details"]
                )
            else:
                raise UnifiedResponse.internal_error(
                    message="删除工作流失败",
                    error_type=result["error"],
                    details=result["details"]
                )

        logger.info(f"✅ 删除成功")
        return UnifiedResponse.success(
            message="工作流删除成功",
            data=result["data"]
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"❌ API异常: {str(e)}")
        import traceback
        logger.error(f"📋 错误堆栈: {traceback.format_exc()}")
        raise UnifiedResponse.internal_error(
            message="删除工作流时发生异常",
            error_type="delete_exception",
            details=str(e)
        )


# 节点管理 (4个API端点)

@router.get("/workflow/{workflow_id}/nodes")
async def get_workflow_nodes(
    workflow_id: str,
    _: dict = Depends(verify_developer_token)
):
    """
    获取工作流节点列表

    获取指定工作流的所有节点信息。
    """
    result = workflow_service.get_workflow_nodes(workflow_id)

    if not result["success"]:
        if result["error"] == "workflow_not_found":
            raise UnifiedResponse.not_found(
                message="工作流不存在",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="获取工作流节点列表失败",
                error_type=result["error"],
                details=result["details"]
            )

    return UnifiedResponse.success(
        message="获取工作流节点列表成功",
        data=result["data"]
    )


@router.post("/workflow/{workflow_id}/nodes", status_code=status.HTTP_201_CREATED)
async def add_workflow_node(
    workflow_id: str,
    request: WorkflowNodeCreateRequest,
    _: dict = Depends(verify_developer_token)
):
    """
    添加工作流节点

    向指定工作流添加新节点，包括父子关系和转换条件。
    """
    result = workflow_service.add_workflow_node(workflow_id, request)

    if not result["success"]:
        if result["error"] == "workflow_not_found":
            raise UnifiedResponse.not_found(
                message="工作流不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] == "node_exists":
            raise UnifiedResponse.bad_request(
                message="节点已存在",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="添加节点失败",
                error_type=result["error"],
                details=result["details"]
            )

    return UnifiedResponse.created(
        message="节点添加成功",
        data=result["data"]
    )


@router.put("/workflow/{workflow_id}/nodes/{node_id}")
async def update_workflow_node(
    workflow_id: str,
    node_id: str,
    request: WorkflowNodeUpdateRequest,
    _: dict = Depends(verify_developer_token)
):
    """
    更新工作流节点

    更新指定工作流中的节点配置。
    """
    result = workflow_service.update_workflow_node(workflow_id, node_id, request)

    if not result["success"]:
        if result["error"] == "workflow_not_found":
            raise UnifiedResponse.not_found(
                message="工作流不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] == "node_not_found":
            raise UnifiedResponse.not_found(
                message="节点不存在",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="更新节点失败",
                error_type=result["error"],
                details=result["details"]
            )

    return UnifiedResponse.success(
        message="节点更新成功",
        data=result["data"]
    )


@router.delete("/workflow/{workflow_id}/nodes/{node_id}")
async def delete_workflow_node(
    workflow_id: str,
    node_id: str,
    _: dict = Depends(verify_developer_token)
):
    """
    删除工作流节点

    从指定工作流中删除节点。
    """
    result = workflow_service.delete_workflow_node(workflow_id, node_id)

    if not result["success"]:
        if result["error"] == "workflow_not_found":
            raise UnifiedResponse.not_found(
                message="工作流不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] == "node_not_found":
            raise UnifiedResponse.not_found(
                message="节点不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] == "cannot_delete_critical_node":
            raise UnifiedResponse.bad_request(
                message="无法删除关键节点",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="删除节点失败",
                error_type=result["error"],
                details=result["details"]
            )

    return UnifiedResponse.success(
        message="节点删除成功",
        data=result["data"]
    )


# amis schema生成器专用接口

@router.get("/workflow/for-amis")
async def get_workflows_for_amis(
    _: dict = Depends(verify_developer_token)
):
    """
    为amis schema生成器提供工作流选项

    返回所有可用的工作流列表，供amis schema生成器选择使用。
    """
    result = workflow_service.get_workflows_for_amis()

    if not result["success"]:
        raise UnifiedResponse.internal_error(
            message="获取工作流选项失败",
            error_type=result.get("error", "internal_error"),
            details=result["details"]
        )

    return UnifiedResponse.success(
        message="获取工作流选项成功",
        data=result["data"]
    )


@router.get("/configuration/for-amis")
async def get_configuration_for_amis(
    _: dict = Depends(verify_developer_token)
):
    """
    为amis schema生成器提供完整的配置信息

    返回当前应用配置的所有API和工作流信息，供amis schema生成器使用。
    包括：
    - 所有可用的API接口及其配置
    - 所有可用的工作流及其节点配置
    - 配置摘要信息
    """
    result = workflow_service.get_amis_configuration_info()

    if not result["success"]:
        raise UnifiedResponse.internal_error(
            message="获取配置信息失败",
            error_type=result.get("error", "internal_error"),
            details=result["details"]
        )

    return UnifiedResponse.success(
        message="获取配置信息成功",
        data=result["data"]
    )


# 工作流执行管理 (保留原有功能)

@router.post("/workflow/{workflow_id}/execute", status_code=status.HTTP_201_CREATED)
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    token_data: dict = Depends(verify_developer_token)
):
    """
    执行工作流

    启动指定工作流的新实例并开始执行。
    """
    started_by = token_data.get("user_id", "developer")
    result = workflow_service.execute_workflow(workflow_id, request, started_by)

    if not result["success"]:
        if result["error"] == "workflow_not_found":
            raise UnifiedResponse.not_found(
                message="工作流不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] in ["workflow_inactive", "no_start_step"]:
            raise UnifiedResponse.bad_request(
                message="工作流无法执行",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="执行工作流失败",
                error_type=result["error"],
                details=result["details"]
            )

    return UnifiedResponse.created(
        message="工作流执行启动成功",
        data=result["data"]
    )




@router.post("/workflow/instances/{instance_id}/continue")
async def continue_workflow_instance(
    instance_id: str,
    request: dict = None,
    _: dict = Depends(verify_developer_token)
):
    """
    继续执行工作流实例

    继续执行处于等待状态的工作流实例，通常用于用户操作后的流程继续。
    """
    # 处理请求数据，支持action、data、comment字段
    action = request.get("action", "continue") if request else "continue"
    data = request.get("data", {}) if request else {}
    comment = request.get("comment", "") if request else ""

    result = workflow_service.continue_workflow_instance(instance_id, action, data, comment)
    
    if not result["success"]:
        if result["error"] == "instance_not_found":
            raise UnifiedResponse.not_found(
                message="工作流实例不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] == "instance_not_waiting":
            raise UnifiedResponse.bad_request(
                message="工作流实例不在等待状态",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="继续执行工作流实例失败",
                error_type=result["error"],
                details=result["details"]
            )
    
    return UnifiedResponse.success(
        message="工作流实例继续执行成功",
        data=result["data"]
    )


@router.post("/workflow/instances/{instance_id}/cancel")
async def cancel_workflow_instance(
    instance_id: str,
    reason: str = Query("用户取消", description="取消原因"),
    _: dict = Depends(verify_developer_token)
):
    """
    取消工作流实例
    
    取消正在执行或等待中的工作流实例。
    """
    result = workflow_service.cancel_workflow_instance(instance_id, reason)
    
    if not result["success"]:
        if result["error"] == "instance_not_found":
            raise UnifiedResponse.not_found(
                message="工作流实例不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] == "instance_already_finished":
            raise UnifiedResponse.bad_request(
                message="工作流实例已完成",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="取消工作流实例失败",
                error_type=result["error"],
                details=result["details"]
            )
    
    return UnifiedResponse.success(
        message="工作流实例取消成功",
        data=result["data"]
    )


# ============================================================================
# 工作流状态机 API（与数据集格式一致）
# ============================================================================

from pydantic import BaseModel
from typing import Any

class WorkflowStateRequest(BaseModel):
    """工作流状态转换请求（数据集格式）"""
    workflow_id: str
    node_id: str
    action: str = "next"  # "next" 或 "submit"
    # 其他字段为表单数据，动态处理


from fastapi import Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User

# 可选认证：支持开发者和普通用户
security = HTTPBearer(auto_error=False)

async def get_user_or_developer(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取当前用户（支持开发者token和普通用户token）"""
    if not credentials:
        return {"user_id": "anonymous", "username": "anonymous"}
    
    try:
        from app.core.auth.jwt_handler import verify_token
        token = credentials.credentials
        
        # 尝试验证 token
        payload = verify_token(token)
        
        if payload.get("user_type") == "developer":
            return {"user_id": "developer", "username": "developer"}
        
        # 普通用户 token
        user_id = payload.get("user_id")
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return {"user_id": user.id, "username": user.username, "user": user}
        
        return {"user_id": "anonymous", "username": "anonymous"}
    except Exception as e:
        return {"user_id": "anonymous", "username": "anonymous"}


@router.post("/workflow/state")
async def workflow_state_transition(
    request: dict = Body(...),  # 接收完整的请求体，包含动态字段
    http_request: Request = None,
    current_user: Dict[str, Any] = Depends(get_user_or_developer),
    db: Session = Depends(get_db)
):
    """
    工作流状态转换 - 委托给 WorkflowExecutionService
    
    职责：
    1. 提取请求参数
    2. 委托给 WorkflowExecutionService.execute_step
    3. 返回标准化响应
    
    所有核心逻辑都在 WorkflowExecutionService 中，确保 DRY 原则。
    """
    from app.services.workflow_execution_service import workflow_execution_service
    from app.services.permission_service import permission_service
    from app.core.logging_config import get_logger
    
    logger = get_logger(__name__)
    
    try:
        # 1. 提取请求字段
        workflow_id = request.get("workflow_id")
        node_id = request.get("node_id")
        action = request.get("action", "next")  # 🔥 提取 action 字段
        
        if not workflow_id or not node_id:
            # 兼容某些 AMIS Wizard 第二步未回传 workflow_id/node_id 的场景：
            # 从当前用户活跃会话兜底补齐，避免前端进入下一步时报 400。
            fallback_user_id = current_user.get("user_id", "anonymous")
            active_session = workflow_execution_service.session_service.get_active_session(fallback_user_id)
            if active_session:
                workflow_id = workflow_id or active_session.workflow_id
                node_id = node_id or active_session.current_step
                logger.warning(
                    f"[Workflow] 使用活跃会话兜底补齐参数: "
                    f"user={fallback_user_id}, workflow={workflow_id}, node={node_id}"
                )
            else:
                raise UnifiedResponse.bad_request(
                    message="缺少必要参数",
                    error_type="missing_parameters",
                    details="缺少 workflow_id 或 node_id"
                )
        
        # 提取表单数据（排除控制字段）
        control_fields = {"workflow_id", "node_id", "action", "&"}
        form_data = {k: v for k, v in request.items() if k not in control_fields}
        
        # 🔥 处理嵌套的 params 字段（AI 生成的表单可能将数据放在 params 中）
        if "params" in form_data and isinstance(form_data.get("params"), dict):
            params_data = form_data.pop("params")
            # 将 params 中的数据展开到 form_data
            for k, v in params_data.items():
                if k not in control_fields and v is not None and v != "":
                    form_data[k] = v
        
        user_id = current_user.get("user_id", "anonymous")
        logger.info(f"[Workflow] 工作流状态转换: user={user_id}, workflow={workflow_id}, node={node_id}, action={action}")
        logger.info(f"[Workflow] 提取的表单数据: {form_data}")
        
        # 2. 获取用户可访问的 API
        user = current_user.get("user")
        if user:
            accessible_apis = permission_service.get_user_accessible_apis(user, db)
        else:
            accessible_apis = []
        
        # 3. 提取用户 token（用于内部 API 调用）
        user_token = None
        if http_request:
            auth_header = http_request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                user_token = auth_header[7:]
        
        # 4. 构建上下文
        context = {
            "accessible_apis": accessible_apis,
            "user_id": user_id,
            "user_token": user_token,
            "action": action  # 🔥 传递 action 到上下文
        }
        
        # 5. 委托给 WorkflowExecutionService 执行
        result = await workflow_execution_service.execute_step(
            user_id=user_id,
            workflow_id=workflow_id,
            node_id=node_id,
            form_data=form_data,
            context=context
        )
        
        # 6. 返回 API 响应格式
        return result.to_api_response()
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"❌ 工作流状态转换失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise UnifiedResponse.internal_error(
            message="工作流状态转换失败",
            error_type="state_transition_error",
            details=str(e)
        )

