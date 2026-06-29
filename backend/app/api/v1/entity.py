"""
实体建模模块API路由
严格按照API文档实现实体建模的13个接口
"""
from fastapi import APIRouter, HTTPException, Header, Query, Path, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from decimal import Decimal
from app.schemas.entity import (
    EntityCreateRequest, EntityUpdateRequest, EntityRelationshipCreateRequest,
    EntityResponse, EntityErrorResponse, EntityErrorData
)
from app.services.entity_service import entity_service
from app.core.auth import verify_developer_token
from app.core.response import UnifiedResponse


def serialize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    序列化记录数据，将不可JSON序列化的类型转换为字符串
    """
    serialized = {}
    for key, value in record.items():
        if isinstance(value, date):
            serialized[key] = value.isoformat()
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()
        elif isinstance(value, Decimal):
            serialized[key] = float(value)
        elif isinstance(value, dict):
            serialized[key] = serialize_record(value)
        elif isinstance(value, list):
            serialized[key] = [serialize_record(item) if isinstance(item, dict) else item for item in value]
        else:
            serialized[key] = value
    return serialized


def serialize_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    序列化记录列表
    """
    return [serialize_record(record) for record in records]

router = APIRouter(prefix="/entities", tags=["实体建模模块"])


@router.get(
    "",
    summary="获取实体列表",
    description="获取所有实体定义列表"
)
async def get_entities_list(
    include_fields: bool = Query(True, description="是否包含字段信息"),
    status: Optional[str] = Query(None, description="实体状态筛选"),
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """
    获取实体列表接口
    
    - **include_fields**: 是否包含字段信息，默认true
    - **status**: 实体状态筛选（可选）
    
    返回实体列表和总数
    """
    # 调用实体服务
    result = entity_service.get_entities_list(
        include_fields=include_fields,
        status=status
    )
    
    if result["success"]:
        # 查询成功
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "获取实体列表成功",
                "data": {
                    "entities": [entity.model_dump() for entity in result["data"]["entities"]],
                    "total": result["data"]["total"]
                }
            }
        )
    else:
        # 查询失败
        raise UnifiedResponse.internal_error(
            message="获取实体列表失败",
            error_type=result["error"],
            details=result["details"]
        )


@router.post(
    "",
    summary="创建实体定义",
    description="创建新的实体定义，包括字段配置"
)
async def create_entity(
    request: EntityCreateRequest,
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """
    创建实体定义接口
    
    - **request**: 实体创建请求数据
    
    返回创建的实体详情
    """
    # 调用实体服务
    result = await entity_service.create_entity(request)
    
    if result["success"]:
        # 创建成功
        return JSONResponse(
            status_code=201,
            content={
                "code": 201,
                "message": "创建实体成功",
                "data": {
                    "entity": result["data"]["entity"].model_dump()
                }
            }
        )
    else:
        # 创建失败
        if result["error"] == "duplicate_entity_name":
            status_code = 409
            message = "实体名称已存在"
        else:
            status_code = 500
            message = "创建实体失败"
        
        if status_code == 409:
            raise UnifiedResponse.conflict(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )


@router.get(
    "/{entity_id}",
    summary="获取实体详情",
    description="获取指定实体的详细信息，包括字段、关系和统计信息"
)
async def get_entity_detail(
    entity_id: str = Path(..., description="实体唯一标识符"),
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """
    获取实体详情接口
    
    - **entity_id**: 实体唯一标识符
    
    返回实体的详细信息
    """
    # 调用实体服务
    result = entity_service.get_entity_by_id(entity_id)
    
    if result["success"]:
        # 查询成功
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "获取实体详情成功",
                "data": {
                    "entity": result["data"]["entity"].model_dump()
                }
            }
        )
    else:
        # 查询失败
        if result["error"] == "entity_not_found":
            status_code = 404
            message = "实体不存在"
        else:
            status_code = 500
            message = "获取实体详情失败"
        
        if status_code == 404:
            raise UnifiedResponse.not_found(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )


@router.put(
    "/{entity_id}",
    summary="更新实体定义",
    description="更新指定实体的定义信息，包括字段配置"
)
async def update_entity(
    entity_id: str = Path(..., description="实体唯一标识符"),
    request: EntityUpdateRequest = ...,
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """
    更新实体定义接口
    
    - **entity_id**: 实体唯一标识符
    - **request**: 实体更新请求数据
    
    返回更新后的实体详情
    """
    # 调用实体服务
    result = await entity_service.update_entity(entity_id, request)
    
    if result["success"]:
        # 更新成功
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "更新实体成功",
                "data": {
                    "entity": result["data"]["entity"].model_dump()
                }
            }
        )
    else:
        # 更新失败
        if result["error"] == "entity_not_found":
            status_code = 404
            message = "实体不存在"
        else:
            status_code = 500
            message = "更新实体失败"
        
        if status_code == 404:
            raise UnifiedResponse.not_found(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )


@router.delete(
    "/{entity_id}",
    summary="删除实体定义",
    description="删除指定的实体定义，支持强制删除和数据备份"
)
async def delete_entity(
    entity_id: str = Path(..., description="实体唯一标识符"),
    force: bool = Query(False, description="是否强制删除"),
    backup: bool = Query(True, description="是否备份数据"),
    authorization: Optional[str] = Header(None)
):
    """
    删除实体定义接口
    
    - **entity_id**: 实体唯一标识符
    - **force**: 是否强制删除，默认false
    - **backup**: 是否备份数据，默认true
    
    返回删除结果和影响的数据统计
    """
    # 调用实体服务
    result = entity_service.delete_entity(entity_id, force, backup)
    
    if result["success"]:
        # 删除成功
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "删除实体成功",
                "data": result["data"]
            }
        )
    else:
        # 删除失败
        if result["error"] == "entity_not_found":
            status_code = 404
            message = "实体不存在"
        else:
            status_code = 500
            message = "删除实体失败"
        
        if status_code == 404:
            raise UnifiedResponse.not_found(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )


@router.get(
    "/{entity_id}/data",
    summary="获取实体数据记录",
    description="获取指定实体的数据记录列表，支持分页、筛选和排序"
)
async def get_entity_records(
    entity_id: str = Path(..., description="实体唯一标识符"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    limit: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    sort_by: Optional[str] = Query(None, description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    authorization: Optional[str] = Header(None)
):
    """
    获取实体数据记录接口

    - **entity_id**: 实体唯一标识符
    - **page**: 页码，从1开始
    - **limit**: 每页数量，最大100
    - **sort_by**: 排序字段（可选）
    - **sort_order**: 排序方向，asc或desc

    返回分页的数据记录列表
    """
    # 调用实体服务
    result = entity_service.get_entity_records(
        entity_id=entity_id,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )

    if result["success"]:
        # 查询成功 - 序列化记录以处理date/datetime类型
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "获取实体记录成功",
                "data": {
                    "records": serialize_records(result["data"]["records"]),
                    "pagination": result["data"]["pagination"].model_dump()
                }
            }
        )
    else:
        # 查询失败
        if result["error"] == "entity_not_found":
            status_code = 404
            message = "实体不存在"
        else:
            status_code = 500
            message = "获取实体记录失败"

        if status_code == 404:
            raise UnifiedResponse.not_found(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )


@router.post(
    "/{entity_id}/data",
    summary="创建实体数据记录",
    description="为指定实体创建新的数据记录"
)
async def create_entity_record(
    entity_id: str = Path(..., description="实体唯一标识符"),
    data: Dict[str, Any] = ...,
    authorization: Optional[str] = Header(None)
):
    """
    创建实体数据记录接口

    - **entity_id**: 实体唯一标识符
    - **data**: 记录数据，键值对格式

    返回创建的记录数据
    """
    # 调用实体服务
    result = entity_service.create_entity_record(entity_id, data)

    if result["success"]:
        # 创建成功 - 序列化记录以处理date/datetime类型
        return JSONResponse(
            status_code=201,
            content={
                "code": 201,
                "message": "创建记录成功",
                "data": {
                    "record": serialize_record(result["data"]["record"])
                }
            }
        )
    else:
        # 创建失败
        if result["error"] == "entity_not_found":
            raise UnifiedResponse.not_found(
                message="实体不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] == "validation_failed":
            raise UnifiedResponse.bad_request(
                message="数据验证失败",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="创建记录失败",
                error_type=result["error"],
                details=result["details"]
            )


@router.put(
    "/{entity_id}/data/{record_id}",
    summary="更新实体数据记录",
    description="更新指定实体的特定数据记录"
)
async def update_entity_record(
    entity_id: str = Path(..., description="实体唯一标识符"),
    record_id: str = Path(..., description="记录唯一标识符"),
    data: Dict[str, Any] = ...,
    authorization: Optional[str] = Header(None)
):
    """
    更新实体数据记录接口

    - **entity_id**: 实体唯一标识符
    - **record_id**: 记录唯一标识符
    - **data**: 更新的记录数据

    返回更新后的记录数据
    """
    # 调用实体服务
    result = entity_service.update_entity_record(entity_id, record_id, data)

    if result["success"]:
        # 更新成功 - 序列化记录以处理date/datetime类型
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "更新记录成功",
                "data": {
                    "record": serialize_record(result["data"]["record"])
                }
            }
        )
    else:
        # 更新失败
        if result["error"] == "record_not_found":
            raise UnifiedResponse.not_found(
                message="记录不存在",
                error_type=result["error"],
                details=result["details"]
            )
        elif result["error"] == "validation_failed":
            raise UnifiedResponse.bad_request(
                message="数据验证失败",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="更新记录失败",
                error_type=result["error"],
                details=result["details"]
            )


@router.delete(
    "/{entity_id}/data/{record_id}",
    summary="删除实体数据记录",
    description="删除指定实体的特定数据记录"
)
async def delete_entity_record(
    entity_id: str = Path(..., description="实体唯一标识符"),
    record_id: str = Path(..., description="记录唯一标识符"),
    authorization: Optional[str] = Header(None)
):
    """
    删除实体数据记录接口

    - **entity_id**: 实体唯一标识符
    - **record_id**: 记录唯一标识符

    返回删除结果
    """
    # 调用实体服务
    result = entity_service.delete_entity_record(entity_id, record_id)

    if result["success"]:
        # 删除成功
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "删除记录成功",
                "data": result["data"]
            }
        )
    else:
        # 删除失败
        if result["error"] == "record_not_found":
            status_code = 404
            message = "记录不存在"
        else:
            status_code = 500
            message = "删除记录失败"

        if status_code == 404:
            raise UnifiedResponse.not_found(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )


@router.get(
    "/{entity_id}/relationships",
    summary="获取实体关系",
    description="获取指定实体的所有关系定义"
)
async def get_entity_relationships(
    entity_id: str = Path(..., description="实体唯一标识符"),
    authorization: Optional[str] = Header(None)
):
    """
    获取实体关系接口

    - **entity_id**: 实体唯一标识符

    返回实体的所有关系列表
    """
    # 调用实体服务
    result = entity_service.get_entity_relationships(entity_id)

    if result["success"]:
        # 查询成功
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "获取实体关系成功",
                "data": {
                    "relationships": [rel.model_dump() for rel in result["data"]["relationships"]],
                    "total": result["data"]["total"]
                }
            }
        )
    else:
        # 查询失败
        if result["error"] == "entity_not_found":
            status_code = 404
            message = "实体不存在"
        else:
            status_code = 500
            message = "获取实体关系失败"

        if status_code == 404:
            raise UnifiedResponse.not_found(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )


@router.post(
    "/{entity_id}/relationships",
    summary="创建实体关系",
    description="为指定实体创建新的关系定义"
)
async def create_entity_relationship(
    entity_id: str = Path(..., description="实体唯一标识符"),
    request: EntityRelationshipCreateRequest = ...,
    authorization: Optional[str] = Header(None)
):
    """
    创建实体关系接口

    - **entity_id**: 实体唯一标识符
    - **request**: 关系创建请求数据

    返回创建的关系详情
    """
    # 调用实体服务
    result = await entity_service.create_entity_relationship(entity_id, request)

    if result["success"]:
        # 创建成功
        return JSONResponse(
            status_code=201,
            content={
                "code": 201,
                "message": "创建关系成功",
                "data": {
                    "relationship": result["data"]["relationship"].model_dump()
                }
            }
        )
    else:
        # 创建失败
        if result["error"] == "source_entity_not_found":
            status_code = 404
            message = "源实体不存在"
        elif result["error"] == "target_entity_not_found":
            status_code = 404
            message = "目标实体不存在"
        elif result["error"] == "relationship_exists":
            raise UnifiedResponse.conflict(
                message="关系已存在",
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="创建关系失败",
                error_type=result["error"],
                details=result["details"]
            )


@router.delete(
    "/{entity_id}/relationships/{relationship_id}",
    summary="删除实体关系",
    description="删除指定实体的特定关系定义"
)
async def delete_entity_relationship(
    entity_id: str = Path(..., description="实体唯一标识符"),
    relationship_id: str = Path(..., description="关系唯一标识符"),
    authorization: Optional[str] = Header(None)
):
    """
    删除实体关系接口

    - **entity_id**: 实体唯一标识符
    - **relationship_id**: 关系唯一标识符

    返回删除结果
    """
    # 调用实体服务
    result = entity_service.delete_entity_relationship(entity_id, relationship_id)

    if result["success"]:
        # 删除成功
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "删除关系成功",
                "data": result["data"]
            }
        )
    else:
        # 删除失败
        if result["error"] == "relationship_not_found":
            status_code = 404
            message = "关系不存在"
        else:
            status_code = 500
            message = "删除关系失败"

        if status_code == 404:
            raise UnifiedResponse.not_found(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )


@router.put(
    "/relationships/{relationship_id}",
    summary="更新实体关系",
    description="更新指定的实体关系定义"
)
async def update_entity_relationship_by_id(
    relationship_id: str = Path(..., description="关系唯一标识符"),
    request: EntityRelationshipCreateRequest = ...,
    authorization: Optional[str] = Header(None)
):
    """
    更新实体关系接口

    - **relationship_id**: 关系唯一标识符
    - **request**: 关系更新请求数据

    返回更新的关系详情
    """
    # 调用实体服务
    result = entity_service.update_entity_relationship_by_id(relationship_id, request)

    if result["success"]:
        # 更新成功
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "更新关系成功",
                "data": {
                    "relationship": result["data"]["relationship"].model_dump()
                }
            }
        )
    else:
        # 更新失败
        if result["error"] == "relationship_not_found":
            status_code = 404
            message = "关系不存在"
        elif result["error"] == "target_entity_not_found":
            status_code = 404
            message = "目标实体不存在"
        else:
            status_code = 500
            message = "更新关系失败"

        if status_code == 404:
            raise UnifiedResponse.not_found(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message=message,
                error_type=result["error"],
                details=result["details"]
            )


@router.get(
    "/crud-options",
    summary="获取CRUD可用实体列表",
    description="获取可用于CRUD操作的实体列表，用于API路由创建时的实体选择"
)
async def get_crud_entity_options(
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """
    获取CRUD可用实体列表
    
    返回可用于CRUD操作的实体选项列表
    """
    # 获取所有活跃的实体
    result = entity_service.get_entities_list(include_fields=False, status="active")
    
    if result["success"]:
        entities = result["data"]["entities"]
        
        # 转换为选项格式
        options = []
        for entity in entities:
            # 检查是否有对应的数据库表
            table_name = f"entity_{entity.name.lower()}"
            
            options.append({
                "value": entity.name,
                "label": entity.displayName,
                "description": entity.description,
                "table_name": table_name,
                "field_count": entity.field_count,
                "record_count": entity.record_count,
                "created_at": entity.created_at
            })
        
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "获取CRUD实体选项成功",
                "data": {
                    "options": options,
                    "total": len(options)
                }
            }
        )
    else:
        # 查询失败
        raise UnifiedResponse.internal_error(
            message="获取CRUD实体选项失败",
            error_type=result["error"],
            details=result["details"]
        )
