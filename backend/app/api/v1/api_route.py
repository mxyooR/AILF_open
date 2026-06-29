"""
API路由管理模块API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional
import time
from datetime import datetime

from app.core.auth import verify_developer_token
from app.services.api_route_service import APIRouteService
from app.schemas.api_route import (
    APIRouteRegisterRequest, APIRouteUpdateRequest, APIRouteStatusRequest,
    APIRouteRegisterResponse, APIRouteListResponse, APIRouteDetailResponse,
    APIRouteHealthResponse, StandardResponse, ErrorResponse, ErrorDetails,
    ResponseMeta, PaginationInfo, RouteSummary
)
from app.core.response import UnifiedResponse

router = APIRouter(tags=["API路由管理"])

# 创建服务实例
api_route_service = APIRouteService()


def create_standard_response(
    code: int,
    message: str,
    data: any = None,
    execution_time: Optional[int] = None
) -> StandardResponse:
    """创建标准响应"""
    meta = ResponseMeta()
    if execution_time:
        meta.execution_time = execution_time
    
    return StandardResponse(
        code=code,
        message=message,
        data=data,
        meta=meta
    )


@router.post("/test-debug", response_model=StandardResponse)
async def test_debug():
    """测试调试路由"""
    print("🔧 测试调试路由被调用")
    return create_standard_response(
        code=200,
        message="调试成功",
        data={"test": "success"}
    )


@router.post("/register-raw", response_model=StandardResponse, status_code=201)
async def register_route_raw(
    request: Request,
    _: dict = Depends(verify_developer_token)
):
    """
    动态注册新的API路由（原始JSON版本，用于调试）
    """
    try:
        print("🔧 原始注册路由被调用")
        
        # 获取原始JSON数据
        raw_data = await request.json()
        print(f"📝 原始JSON数据: {raw_data}")
        
        # 尝试手动创建APIRouteRegisterRequest对象
        api_route_request = APIRouteRegisterRequest(**raw_data)
        print(f"✅ Pydantic验证成功")
        
        # 继续正常流程
        result = api_route_service.register_route(api_route_request)
        print(f"📊 服务层返回结果: {result}")
        
        if not result.get("success", False):
            print(f"❌ 服务层注册失败: {result}")
            raise UnifiedResponse.internal_error(
                message="注册API路由失败",
                error_type="registration_failed",
                details=f"err_{int(datetime.utcnow().timestamp())}"
            )
        
        return create_standard_response(
            code=201,
            message="API路由注册成功",
            data=result["data"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 原始注册路由异常: {e}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")
        
        raise UnifiedResponse.internal_error(
            message="服务器内部错误",
            error_type="internal_server_error",
            details=str(e)
        )


@router.post("/register", response_model=StandardResponse, status_code=201)
async def register_route(
    request: APIRouteRegisterRequest,
    _: dict = Depends(verify_developer_token)
):
    """
    动态注册新的API路由
    
    支持多种处理器类型和业务逻辑。注册成功后，新的API端点立即可用，并自动生成对应的数据录入表单。
    
    - **api_id**: API标识符，全局唯一
    - **name**: 路由名称
    - **endpoint**: API端点路径
    - **method**: HTTP方法
    - **description**: 路由描述
    - **auth_required**: 是否需要认证
    - **handler**: 处理器配置
    - **parameters**: 参数列表
    - **responses**: 响应配置
    - **form_config**: 表单配置
    """
    start_time = time.time()
    
    try:
        print(f"🔧 API路由注册请求开始: {request.api_id}")
        print(f"📝 请求数据: endpoint={request.endpoint}, method={request.method}")
        
        # 检查参数列表
        if request.parameters:
            print(f"🔍 参数数量: {len(request.parameters)}")
            for i, param in enumerate(request.parameters):
                print(f"  参数 {i+1}: {param.name} ({param.type}, {param.location})")
        
        print(f"🚀 调用服务层方法")
        result = api_route_service.register_route(request)
        print(f"📊 服务层返回结果: {result.get('success', False)}")
        
        if not result["success"]:
            if result["error"] == "route_conflict":
                raise UnifiedResponse.conflict(
                    message="API路由已存在",
                    error_type="route_conflict",
                    details={
                        "existing_route": result.get("existing_route")
                    },
                    suggestion="请使用不同的端点路径或HTTP方法，或者更新现有路由",
                    error_code="ROUTE_CONFLICT"
                )
            elif result["error"] == "validation_error":
                raise UnifiedResponse.bad_request(
                    message="请求参数验证失败",
                    error_type="validation_error",
                    details={
                        "field_errors": result.get("details", {}).get("field_errors", {}),
                        "global_errors": result.get("details", {}).get("global_errors", [])
                    },
                    suggestion="请检查输入参数格式并重试"
                )
            else:
                raise UnifiedResponse.internal_error(
                    message="注册API路由失败",
                    error_type="internal_server_error",
                    details=f"err_{int(datetime.utcnow().timestamp())}"
                )
        
        execution_time = int((time.time() - start_time) * 1000)
        return create_standard_response(
            code=201,
            message="API路由注册成功",
            data=result["data"],
            execution_time=execution_time
        )
        
    except HTTPException:
        print(f"❌ HTTP异常")
        raise
    except Exception as e:
        print(f"❌ 未知异常: {e}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")
        
        raise UnifiedResponse.internal_error(
            message="服务器内部错误",
            error_type="internal_server_error",
            details=str(e)
        )


@router.get("", response_model=StandardResponse)
async def get_routes(
    status: Optional[str] = Query(None, description="筛选路由状态 (active/inactive/maintenance)"),
    method: Optional[str] = Query(None, description="筛选HTTP方法"),
    handler_type: Optional[str] = Query(None, description="筛选处理器类型"),
    entity: Optional[str] = Query(None, description="筛选关联实体"),
    search: Optional[str] = Query(None, description="搜索路由名称或描述"),
    page: int = Query(1, ge=1, description="页码，默认1"),
    limit: int = Query(20, ge=1, le=100, description="每页数量，默认20，最大100"),
    sort: Optional[str] = Query("created_at", description="排序字段"),
    order: Optional[str] = Query("desc", description="排序方向 (asc/desc)"),
    include_stats: bool = Query(True, description="是否包含统计信息"),
    include_forms: bool = Query(True, description="是否包含关联表单"),
    _: dict = Depends(verify_developer_token)
):
    """
    获取当前已注册的所有API路由
    
    支持多维度筛选、排序和分页。提供路由的基本信息、状态统计和性能指标。
    """
    start_time = time.time()
    
    try:
        result = api_route_service.get_routes_list(
            status=status,
            method=method,
            handler_type=handler_type,
            entity=entity,
            search=search,
            page=page,
            limit=limit,
            sort=sort,
            order=order,
            include_stats=include_stats,
            include_forms=include_forms
        )
        
        if not result["success"]:
            raise UnifiedResponse.internal_error(
                message="获取API路由列表失败",
                error_type="internal_server_error",
                details=f"err_{int(datetime.utcnow().timestamp())}"
            )
        
        execution_time = int((time.time() - start_time) * 1000)
        return create_standard_response(
            code=200,
            message="获取API路由列表成功",
            data=result["data"],
            execution_time=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="服务器内部错误",
            error_type="internal_server_error",
            details=f"err_{int(datetime.utcnow().timestamp())}"
        )


@router.get("/health", response_model=StandardResponse)
async def check_routes_health(
    detailed: bool = Query(False, description="是否返回详细信息"),
    include_inactive: bool = Query(False, description="是否包含非活跃路由"),
    format: str = Query("json", description="响应格式"),
    _: dict = Depends(verify_developer_token)
):
    """
    检查所有API路由的健康状态

    提供系统整体运行情况概览和性能监控dashboard。
    """
    start_time = time.time()

    try:
        result = api_route_service.check_routes_health(detailed, include_inactive, format)

        if not result["success"]:
            raise UnifiedResponse.internal_error(
                message="API路由健康检查失败",
                error_type="internal_server_error",
                details=f"err_{int(datetime.utcnow().timestamp())}"
            )

        execution_time = int((time.time() - start_time) * 1000)
        return create_standard_response(
            code=200,
            message="API路由健康检查完成",
            data=result["data"],
            execution_time=execution_time
        )

    except HTTPException:
        raise
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="服务器内部错误",
            error_type="internal_server_error",
            details=f"err_{int(datetime.utcnow().timestamp())}"
        )


@router.get("/{route_id}", response_model=StandardResponse)
async def get_route_detail(
    route_id: str,
    _: dict = Depends(verify_developer_token)
):
    """
    获取指定API路由的详细信息
    """
    start_time = time.time()
    
    try:
        result = api_route_service.get_route_detail(route_id)
        
        if not result["success"]:
            if result["error"] == "route_not_found":
                raise UnifiedResponse.not_found(
                    message="请求的资源不存在",
                    error_type="resource_not_found",
                    details={
                        "resource_type": "api_route",
                        "resource_id": route_id
                    }
                )
            else:
                raise UnifiedResponse.internal_error(
                    message="获取API路由详情失败",
                    error_type="internal_server_error",
                    details=f"err_{int(datetime.utcnow().timestamp())}"
                )
        
        execution_time = int((time.time() - start_time) * 1000)
        return create_standard_response(
            code=200,
            message="获取API路由详情成功",
            data=result["data"],
            execution_time=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="服务器内部错误",
            error_type="internal_server_error",
            details=f"err_{int(datetime.utcnow().timestamp())}"
        )


@router.put("/{route_id}", response_model=StandardResponse)
async def update_route(
    route_id: str,
    request: APIRouteUpdateRequest,
    _: dict = Depends(verify_developer_token)
):
    """
    更新已注册的API路由配置
    
    支持部分更新，不影响路由的调用统计和历史数据。
    """
    start_time = time.time()
    
    try:
        result = api_route_service.update_route(route_id, request)
        
        if not result["success"]:
            if result["error"] == "route_not_found":
                raise UnifiedResponse.not_found(
                    message="请求的资源不存在",
                    error_type="resource_not_found",
                    details={
                        "resource_type": "api_route",
                        "resource_id": route_id
                    }
                )
            elif result["error"] == "validation_error":
                raise UnifiedResponse.bad_request(
                    message="请求参数验证失败",
                    error_type="validation_error",
                    details={
                        "field_errors": result.get("details", {}).get("field_errors", {}),
                        "global_errors": result.get("details", {}).get("global_errors", [])
                    },
                    suggestion="请检查输入参数格式并重试"
                )
            else:
                raise UnifiedResponse.internal_error(
                    message="更新API路由失败",
                    error_type="internal_server_error",
                    details=f"err_{int(datetime.utcnow().timestamp())}"
                )
        
        execution_time = int((time.time() - start_time) * 1000)
        return create_standard_response(
            code=200,
            message="API路由更新成功",
            data=result["data"],
            execution_time=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="服务器内部错误",
            error_type="internal_server_error",
            details=f"err_{int(datetime.utcnow().timestamp())}"
        )


@router.delete("/{route_id}", response_model=StandardResponse)
async def delete_route(
    route_id: str,
    force: bool = Query(False, description="是否强制删除"),
    backup: bool = Query(True, description="是否备份配置"),
    cascade: bool = Query(False, description="是否级联删除关联对象"),
    _: dict = Depends(verify_developer_token)
):
    """
    删除指定的API路由注册
    
    删除前会检查路由的使用情况，支持强制删除和安全删除两种模式。
    """
    start_time = time.time()
    
    try:
        result = api_route_service.delete_route(route_id, force, backup, cascade)
        
        if not result["success"]:
            if result["error"] == "route_not_found":
                raise UnifiedResponse.not_found(
                    message="请求的资源不存在",
                    error_type="resource_not_found",
                    details={
                        "resource_type": "api_route",
                        "resource_id": route_id
                    }
                )
            elif result["error"] == "route_in_use":
                raise UnifiedResponse.conflict(
                    message="无法删除正在使用的API路由",
                    error_type="route_in_use",
                    details=result.get("details", {}),
                    suggestion="先停用路由或使用force=true参数强制删除",
                    error_code="ROUTE_IN_USE"
                )
            else:
                raise UnifiedResponse.internal_error(
                    message="删除API路由失败",
                    error_type="internal_server_error",
                    details=f"err_{int(datetime.utcnow().timestamp())}"
                )
        
        execution_time = int((time.time() - start_time) * 1000)
        return create_standard_response(
            code=200,
            message="API路由删除成功",
            data=result["data"],
            execution_time=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="服务器内部错误",
            error_type="internal_server_error",
            details=f"err_{int(datetime.utcnow().timestamp())}"
        )


@router.post("/{route_id}/activate", response_model=StandardResponse)
async def activate_route(
    route_id: str,
    health_check: bool = Query(True, description="是否执行健康检查"),
    warm_up: bool = Query(True, description="是否执行预热"),
    _: dict = Depends(verify_developer_token)
):
    """
    激活指定的API路由
    
    使其可以接收和处理请求。激活过程包括健康检查、依赖验证和性能预热。
    """
    start_time = time.time()
    
    try:
        result = api_route_service.activate_route(route_id, health_check, warm_up)
        
        if not result["success"]:
            if result["error"] == "route_not_found":
                raise UnifiedResponse.not_found(
                    message="请求的资源不存在",
                    error_type="resource_not_found",
                    details={
                        "resource_type": "api_route",
                        "resource_id": route_id
                    }
                )
            else:
                raise UnifiedResponse.internal_error(
                    message="激活API路由失败",
                    error_type="internal_server_error",
                    details=f"err_{int(datetime.utcnow().timestamp())}"
                )
        
        execution_time = int((time.time() - start_time) * 1000)
        return create_standard_response(
            code=200,
            message="API路由激活成功",
            data=result["data"],
            execution_time=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="服务器内部错误",
            error_type="internal_server_error",
            details=f"err_{int(datetime.utcnow().timestamp())}"
        )


@router.post("/{route_id}/deactivate", response_model=StandardResponse)
async def deactivate_route(
    route_id: str,
    graceful: bool = Query(True, description="是否优雅停用"),
    timeout: int = Query(30, description="等待超时时间(秒)"),
    _: dict = Depends(verify_developer_token)
):
    """
    停用指定的API路由
    
    使其不再接收新的请求。支持优雅停用和立即停用两种模式。
    """
    start_time = time.time()
    
    try:
        result = api_route_service.deactivate_route(route_id, graceful, timeout)
        
        if not result["success"]:
            if result["error"] == "route_not_found":
                raise UnifiedResponse.not_found(
                    message="请求的资源不存在",
                    error_type="resource_not_found",
                    details={
                        "resource_type": "api_route",
                        "resource_id": route_id
                    }
                )
            else:
                raise UnifiedResponse.internal_error(
                    message="停用API路由失败",
                    error_type="internal_server_error",
                    details=f"err_{int(datetime.utcnow().timestamp())}"
                )
        
        execution_time = int((time.time() - start_time) * 1000)
        return create_standard_response(
            code=200,
            message="API路由停用成功",
            data=result["data"],
            execution_time=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="服务器内部错误",
            error_type="internal_server_error",
            details=f"err_{int(datetime.utcnow().timestamp())}"
        )


@router.get("/{route_id}/status", response_model=StandardResponse)
async def get_route_status(
    route_id: str,
    period: str = Query("24h", description="统计周期 (1h/24h/7d/30d)"),
    include_trends: bool = Query(True, description="是否包含趋势分析"),
    include_errors: bool = Query(True, description="是否包含错误详情"),
    _: dict = Depends(verify_developer_token)
):
    """
    获取指定API路由的详细状态信息
    
    包括调用统计、性能指标、健康状态和实时监控数据。
    """
    start_time = time.time()
    
    try:
        result = api_route_service.get_route_status(route_id, period, include_trends, include_errors)
        
        if not result["success"]:
            if result["error"] == "route_not_found":
                raise UnifiedResponse.not_found(
                    message="请求的资源不存在",
                    error_type="resource_not_found",
                    details={
                        "resource_type": "api_route",
                        "resource_id": route_id
                    }
                )
            else:
                raise UnifiedResponse.internal_error(
                    message="获取API路由状态失败",
                    error_type="internal_server_error",
                    details=f"err_{int(datetime.utcnow().timestamp())}"
                )
        
        execution_time = int((time.time() - start_time) * 1000)
        return create_standard_response(
            code=200,
            message="获取API路由状态成功",
            data=result["data"],
            execution_time=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="服务器内部错误",
            error_type="internal_server_error",
            details=f"err_{int(datetime.utcnow().timestamp())}"
        )


@router.post("/clear", response_model=StandardResponse, status_code=200)
async def clear_all_routes(
    _: dict = Depends(verify_developer_token)
):
    """
    清空所有API路由

    需要开发者权限
    """
    start_time = time.time()

    try:
        result = api_route_service.clear_all_routes()

        if not result["success"]:
            raise UnifiedResponse.bad_request(
                message=result.get("details", "清空API路由失败"),
                error_type=result.get("error", "clear_failed")
            )

        execution_time = int((time.time() - start_time) * 1000)
        return create_standard_response(
            code=200,
            message=result["message"],
            data=result["data"],
            execution_time=execution_time
        )

    except HTTPException:
        raise
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="服务器内部错误",
            error_type="internal_server_error",
            details=f"err_{int(datetime.utcnow().timestamp())}"
        )


