"""
实体关系管理API路由
独立的关系管理端点，按照API文档规范实现
"""
from fastapi import APIRouter, HTTPException, Header, Path, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from app.schemas.entity import EntityRelationshipCreateRequest
from app.services.entity_service import entity_service
from app.core.auth import verify_developer_token
from app.core.response import UnifiedResponse

router = APIRouter(prefix="/relationships", tags=["实体关系管理"])


@router.post(
    "",
    summary="创建实体关系",
    description="创建新的实体关系定义"
)
async def create_relationship(
    request: EntityRelationshipCreateRequest = ...,
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """
    创建实体关系接口
    
    - **request**: 关系创建请求数据
    
    返回创建的关系详情
    """
    # 调用实体服务创建关系
    result = entity_service.create_relationship(request)
    
    if result["success"]:
        # 创建成功
        return UnifiedResponse.created(
            message="创建关系成功",
            data={
                "relationship": result["data"]["relationship"].model_dump()
            }
        )
    else:
        # 创建失败
        if result["error"] == "source_entity_not_found":
            raise UnifiedResponse.not_found(
                message="源实体不存在",
                error_type="source_entity_not_found",
                details=result["details"]
            )
        elif result["error"] == "target_entity_not_found":
            raise UnifiedResponse.not_found(
                message="目标实体不存在",
                error_type="target_entity_not_found",
                details=result["details"]
            )
        elif result["error"] == "relationship_already_exists":
            raise UnifiedResponse.conflict(
                message="关系已存在",
                error_type="relationship_already_exists",
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="创建关系失败",
                error_type=result["error"],
                details=result["details"]
            )


@router.put(
    "/{relationship_id}",
    summary="更新实体关系",
    description="更新指定的实体关系定义"
)
async def update_relationship(
    relationship_id: str = Path(..., description="关系唯一标识符"),
    request: EntityRelationshipCreateRequest = ...,
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """
    更新实体关系接口
    
    - **relationship_id**: 关系唯一标识符
    - **request**: 关系更新请求数据
    
    返回更新后的关系详情
    """
    # 调用实体服务更新关系
    result = entity_service.update_entity_relationship_by_id(relationship_id, request)
    
    if result["success"]:
        # 更新成功
        return UnifiedResponse.success(
            message="更新关系成功",
            data={
                "relationship": result["data"]["relationship"].model_dump()
            }
        )
    else:
        # 更新失败
        if result["error"] == "relationship_not_found":
            raise UnifiedResponse.not_found(
                message="关系不存在",
                error_type="relationship_not_found",
                details=result["details"]
            )
        elif result["error"] == "target_entity_not_found":
            raise UnifiedResponse.not_found(
                message="目标实体不存在",
                error_type="target_entity_not_found",
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="更新关系失败",
                error_type=result["error"],
                details=result["details"]
            )


@router.delete(
    "/{relationship_id}",
    summary="删除实体关系",
    description="删除指定的实体关系定义"
)
async def delete_relationship_by_id(
    relationship_id: str = Path(..., description="关系唯一标识符"),
    authorization: Optional[str] = Header(None)
):
    """
    删除实体关系接口
    
    - **relationship_id**: 关系唯一标识符
    
    返回删除结果
    """
    # 调用实体服务删除关系
    result = entity_service.delete_entity_relationship_by_id(relationship_id)
    
    if result["success"]:
        # 删除成功
        return UnifiedResponse.success(
            message="删除关系成功",
            data=result["data"]
        )
    else:
        # 删除失败
        if result["error"] == "relationship_not_found":
            raise UnifiedResponse.not_found(
                message="关系不存在",
                error_type="relationship_not_found",
                details=result["details"]
            )
        else:
            raise UnifiedResponse.internal_error(
                message="删除关系失败",
                error_type=result["error"],
                details=result["details"]
            )
