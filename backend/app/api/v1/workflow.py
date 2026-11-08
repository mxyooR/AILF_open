"""工作流配置、节点维护、实例管理和经过身份验证的表单状态流转接口。"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.auth import verify_developer_token
from app.core.database import get_db
from app.core.response import UnifiedResponse
from app.models.user import User
from app.schemas.workflow import (
    WorkflowCreateRequest, WorkflowUpdateRequest, WorkflowExecuteRequest,
    WorkflowNodeCreateRequest, WorkflowNodeUpdateRequest,
)
from app.services.workflow_service import workflow_service

router = APIRouter(tags=["工作流设计模块"])
security = HTTPBearer(auto_error=False)


def _result(result, message):
    if not result["success"]:
        error = result.get("error", "internal_error")
        if error in {"workflow_not_found", "node_not_found", "instance_not_found"}:
            factory = UnifiedResponse.not_found
        elif error in {"workflow_exists", "node_exists", "has_running_instances"}:
            factory = UnifiedResponse.conflict
        elif error in {
            "validation_failed", "workflow_inactive", "no_start_step",
            "instance_not_waiting", "instance_already_finished", "execution_failed",
        }:
            factory = UnifiedResponse.bad_request
        else:
            factory = UnifiedResponse.internal_error
        raise factory(message=message, error_type=error, details=result.get("details"))
    return result["data"]


def _token(request):
    header = request.headers.get("Authorization", "")
    return header[7:] if header.lower().startswith("bearer ") else None


def _developer_context(request):
    from app.services.api_route_service import api_route_service
    return {"user_token": _token(request), "accessible_apis": api_route_service.get_all_routes()}


@router.post("/workflow", status_code=status.HTTP_201_CREATED)
async def create_workflow(request: WorkflowCreateRequest, _: dict = Depends(verify_developer_token)):
    data = _result(workflow_service.create_workflow(request), "创建工作流失败")
    return UnifiedResponse.created(message="工作流创建成功", data=data)


@router.get("/workflow")
async def get_workflows_list(
    page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None, business_scenario: Optional[str] = None,
    search: Optional[str] = None, sort_by: str = "created_at", sort_order: str = "desc",
    _: dict = Depends(verify_developer_token),
):
    data = _result(workflow_service.get_workflows_list(
        page, limit, status, business_scenario, search, sort_by, sort_order
    ), "获取工作流列表失败")
    return UnifiedResponse.success(message="获取工作流列表成功", data=data)


# 固定路径必须先注册，避免 for-amis、instances 等被误当作工作流 ID。
@router.get("/workflow/for-amis")
async def get_workflows_for_amis(_: dict = Depends(verify_developer_token)):
    return UnifiedResponse.success(
        message="获取工作流选项成功", data=_result(workflow_service.get_workflows_for_amis(), "获取工作流选项失败")
    )


@router.get("/configuration/for-amis")
async def get_configuration_for_amis(_: dict = Depends(verify_developer_token)):
    return UnifiedResponse.success(
        message="获取配置信息成功", data=_result(workflow_service.get_amis_configuration_info(), "获取配置信息失败")
    )


@router.get("/workflow/instances")
async def get_workflow_instances(
    workflow_id: Optional[str] = None, status: Optional[str] = None, user_id: Optional[str] = None,
    page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), sort: str = "created_at",
    _: dict = Depends(verify_developer_token),
):
    return UnifiedResponse.success(message="获取工作流实例列表成功", data=_result(
        workflow_service.get_workflow_instances(workflow_id, status, user_id, page, limit, sort),
        "获取工作流实例列表失败",
    ))


@router.get("/workflow/instances/{instance_id}")
async def get_workflow_instance_detail(instance_id: str, _: dict = Depends(verify_developer_token)):
    return UnifiedResponse.success(message="获取工作流实例详情成功", data=_result(
        workflow_service.get_workflow_instance_detail(instance_id), "获取工作流实例详情失败"
    ))


@router.post("/workflow/instances/{instance_id}/continue")
async def continue_workflow_instance(
    instance_id: str, http_request: Request, request: dict = Body(default=None),
    _: dict = Depends(verify_developer_token),
):
    request = request or {}
    result = await workflow_service.continue_workflow_instance(
        instance_id, request.get("action", "continue"), request.get("data") or {},
        request.get("comment", ""), context=_developer_context(http_request),
    )
    return UnifiedResponse.success(message="工作流实例继续执行成功", data=_result(result, "继续执行工作流实例失败"))


@router.post("/workflow/instances/{instance_id}/cancel")
async def cancel_workflow_instance(
    instance_id: str, reason: str = Query("用户取消"), _: dict = Depends(verify_developer_token),
):
    session = workflow_service.sessions.get_instance(instance_id)
    if session is None:
        _result({"success": False, "error": "instance_not_found", "details": "实例不存在"}, "工作流实例不存在")
    async with workflow_service.sessions.execution_lock(session.user_id):
        result = workflow_service.cancel_workflow_instance(instance_id, reason)
    return UnifiedResponse.success(message="工作流实例取消成功", data=_result(result, "取消工作流实例失败"))


async def get_user_or_developer(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise UnifiedResponse.unauthorized(message="请先登录", error_type="authentication_required")
    from app.core.auth.jwt_handler import jwt_handler
    result = jwt_handler.verify_token(
        credentials.credentials, expected_token_type="access", check_session=True
    )
    if not result.get("valid"):
        raise UnifiedResponse.unauthorized(message="登录已失效", error_type="invalid_token")
    payload = result.get("payload") or {}
    user_type = payload.get("user_type") or result.get("user_type")
    if user_type == "developer":
        return {"user_id": "developer", "username": "developer"}
    user_id = payload.get("user_id") or payload.get("sub")
    user = db.get(User, user_id) if user_id and user_type == "user" else None
    if user is None:
        raise UnifiedResponse.unauthorized(message="用户不存在", error_type="user_not_found")
    # 用户模型用 is_active 标记启用状态，与工作流的 status 字段不同。
    if not user.is_active:
        raise UnifiedResponse.forbidden(message="用户已停用", error_type="user_inactive")
    return {"user_id": user.id, "username": user.username, "user": user}


@router.post("/workflow/state")
async def workflow_state_transition(
    http_request: Request, request: dict = Body(...),
    current_user: Dict[str, Any] = Depends(get_user_or_developer), db: Session = Depends(get_db),
):
    from app.services.workflow_execution_service import workflow_execution_service
    from app.services.permission_service import permission_service
    user_id = current_user["user_id"]
    workflow_id, node_id = request.get("workflow_id"), request.get("node_id")
    if not workflow_id or not node_id:
        session = workflow_execution_service.session_service.get_active_session(user_id)
        if session is not None:
            workflow_id = workflow_id or session.workflow_id
            node_id = node_id or session.current_step
    if not isinstance(workflow_id, str) or not isinstance(node_id, str) or not workflow_id or not node_id:
        raise UnifiedResponse.bad_request(message="缺少必要参数", error_type="missing_parameters",
                                         details="缺少 workflow_id 或 node_id")
    action = request.get("action", "next")
    if action not in {"next", "submit"}:
        raise UnifiedResponse.bad_request(message="不支持的工作流操作", error_type="invalid_action")
    controls = {"workflow_id", "node_id", "action", "&", "instance_id", "user_token", "accessible_apis"}
    form_data = {key: value for key, value in request.items() if key not in controls}
    user = current_user.get("user")
    context = _developer_context(http_request) if user is None else {
        "user_token": _token(http_request),
        "accessible_apis": permission_service.get_user_accessible_apis(user, db),
    }
    context.update({"user_id": user_id, "action": action, "instance_id": request.get("instance_id")})
    result = await workflow_execution_service.execute_step(user_id, workflow_id, node_id, form_data, context)
    return result.to_api_response()


@router.get("/workflow/{workflow_id}")
async def get_workflow_detail(workflow_id: str, _: dict = Depends(verify_developer_token)):
    return UnifiedResponse.success(message="获取工作流详情成功", data=_result(
        workflow_service.get_workflow_detail(workflow_id), "获取工作流详情失败"
    ))


@router.put("/workflow/{workflow_id}")
async def update_workflow(
    workflow_id: str, request: WorkflowUpdateRequest, _: dict = Depends(verify_developer_token),
):
    return UnifiedResponse.success(message="工作流更新成功", data=_result(
        workflow_service.update_workflow(workflow_id, request), "更新工作流失败"
    ))


@router.delete("/workflow/{workflow_id}")
async def delete_workflow(
    workflow_id: str, force: bool = Query(False), _: dict = Depends(verify_developer_token),
):
    return UnifiedResponse.success(message="工作流删除成功", data=_result(
        workflow_service.delete_workflow(workflow_id, force), "删除工作流失败"
    ))


@router.get("/workflow/{workflow_id}/nodes")
async def get_workflow_nodes(workflow_id: str, _: dict = Depends(verify_developer_token)):
    return UnifiedResponse.success(message="获取节点列表成功", data=_result(
        workflow_service.get_workflow_nodes(workflow_id), "获取节点列表失败"
    ))


@router.post("/workflow/{workflow_id}/nodes", status_code=status.HTTP_201_CREATED)
async def add_workflow_node(
    workflow_id: str, request: WorkflowNodeCreateRequest, _: dict = Depends(verify_developer_token),
):
    return UnifiedResponse.created(message="节点添加成功", data=_result(
        workflow_service.add_workflow_node(workflow_id, request), "添加节点失败"
    ))


@router.put("/workflow/{workflow_id}/nodes/{node_id}")
async def update_workflow_node(
    workflow_id: str, node_id: str, request: WorkflowNodeUpdateRequest,
    _: dict = Depends(verify_developer_token),
):
    return UnifiedResponse.success(message="节点更新成功", data=_result(
        workflow_service.update_workflow_node(workflow_id, node_id, request), "更新节点失败"
    ))


@router.delete("/workflow/{workflow_id}/nodes/{node_id}")
async def delete_workflow_node(
    workflow_id: str, node_id: str, _: dict = Depends(verify_developer_token),
):
    return UnifiedResponse.success(message="节点删除成功", data=_result(
        workflow_service.delete_workflow_node(workflow_id, node_id), "删除节点失败"
    ))


@router.post("/workflow/{workflow_id}/execute", status_code=status.HTTP_201_CREATED)
async def execute_workflow(
    workflow_id: str, http_request: Request, request: WorkflowExecuteRequest,
    token_data: dict = Depends(verify_developer_token),
):
    request.context = {**(request.context or {}), **_developer_context(http_request)}
    result = await workflow_service.execute_workflow(workflow_id, request, "developer")
    return UnifiedResponse.created(message="工作流执行启动成功", data=_result(result, "执行工作流失败"))

