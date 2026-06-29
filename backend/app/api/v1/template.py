"""
模板管理模块API路由
严格按照API文档实现模板管理的2个接口，并添加模板应用功能

注意：路由顺序很重要！静态路径必须在动态路径 /{template_key} 之前定义
"""
from fastapi import APIRouter, HTTPException, Header, Query, Depends, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import json
import os
from pathlib import Path
from app.schemas.template import (
    TemplateListResponse,
    TemplateDetailResponse,
    TemplateErrorResponse,
    TemplateErrorData
)
from app.services.template_service import template_service
from app.core.auth import verify_developer_token
from app.core.response import UnifiedResponse

router = APIRouter(prefix="/templates", tags=["模板管理模块"])


# 模板应用请求模型
class TemplateApplyRequest(BaseModel):
    """模板应用请求"""
    scenario_name: str = Field(..., description="场景名称")
    description: Optional[str] = Field(None, description="场景描述")
    customizations: Optional[Dict[str, Any]] = Field(None, description="自定义配置")
    import_sample_data: bool = Field(default=False, description="是否导入示例数据")


# 模板应用响应模型
class TemplateApplyResponse(BaseModel):
    """模板应用响应"""
    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="应用模板成功", description="响应消息")
    data: Dict[str, Any] = Field(..., description="应用结果数据")


# 保存当前配置为模板请求模型
class SaveCurrentTemplateRequest(BaseModel):
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    category: str = Field(..., description="模板分类")
    difficulty: str = Field(default="intermediate", description="难度等级")
    tags: Optional[List[str]] = Field(default=[], description="标签")
    save_location: str = Field(default="system", description="保存位置：system(系统模板目录) 或 custom(自定义目录)")
    custom_path: Optional[str] = Field(default=None, description="自定义保存路径")
    includeEntities: bool = Field(default=True, description="包含实体")
    includeWorkflows: bool = Field(default=True, description="包含工作流")
    includeAPIs: bool = Field(default=True, description="包含API")
    includeRoles: bool = Field(default=True, description="包含角色")


# ============================================================
# 静态路由（必须在动态路由 /{template_key} 之前定义）
# ============================================================

@router.get(
    "",
    response_model=TemplateListResponse,
    summary="获取所有可用模板",
    description="获取系统中所有可用的业务场景模板列表"
)
async def get_templates_list(
    category: Optional[str] = Query(None, description="模板分类筛选"),
    include_preview: bool = Query(False, description="是否包含预览信息，默认false"),
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """获取所有可用模板接口"""
    valid_categories = [
        "business", "healthcare", "education", "hospitality", 
        "finance", "logistics", "government", "custom"
    ]
    
    if category and category not in valid_categories:
        raise UnifiedResponse.bad_request(
            message="无效的分类参数",
            error_type="invalid_category",
            details=f"分类参数必须是以下值之一: {', '.join(valid_categories)}"
        )
    
    result = template_service.get_templates_list(
        category=category,
        include_preview=include_preview
    )
    
    if result["success"]:
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "获取模板列表成功",
                "data": {
                    "templates": [template.model_dump() for template in result["data"]["templates"]],
                    "total": result["data"]["total"],
                    "categories": [category.model_dump() for category in result["data"]["categories"]]
                }
            }
        )
    else:
        raise UnifiedResponse.internal_error(
            message="获取模板列表失败",
            error_type=result["error"],
            details=result["details"]
        )


@router.post(
    "/reload",
    summary="重新加载模板",
    description="重新加载所有模板文件"
)
async def reload_templates():
    """重新加载模板"""
    try:
        template_service.reload_templates()
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "模板重新加载成功",
                "data": {}
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "模板重新加载失败",
                "data": {
                    "error": "reload_failed",
                    "details": str(e)
                }
            }
        )


@router.post(
    "/save-current",
    summary="保存当前配置为模板",
    description="将当前系统的配置保存为可复用的模板"
)
async def save_current_as_template(
    request: SaveCurrentTemplateRequest,
    _: dict = Depends(verify_developer_token)
):
    """保存当前配置为模板"""
    try:
        from app.core.database import get_db_session
        from app.models.entity import EntityDBModel
        from app.models.api_route import APIRouteDBModel
        from app.models.role import RoleDBModel
        from app.models.workflow import WorkflowDBModel
        from datetime import datetime
        
        template_key = request.name.lower().replace(" ", "_").replace("-", "_")
        
        template_data = {
            "template_info": {
                "key": template_key,
                "name": request.name,
                "description": request.description,
                "category": request.category.upper(),
                "difficulty": request.difficulty.upper(),
                "estimated_setup_time": "30分钟",
                "version": "1.0.0",
                "author": "Custom",
                "license": "MIT",
                "features": [],
                "tags": request.tags or [],
                "created_at": datetime.now().isoformat() + "Z",
                "updated_at": datetime.now().isoformat() + "Z",
                "preview": {
                    "entities": 0,
                    "workflows": 0,
                    "forms": 0,
                    "apis": 0
                }
            }
        }
        
        with get_db_session() as db:
            if request.includeEntities:
                entities = db.query(EntityDBModel).all()
                template_data["entities"] = []
                for entity in entities:
                    fields_data = []
                    if entity.fields:
                        for field in entity.fields:
                            if isinstance(field, dict):
                                fields_data.append(field)
                            elif hasattr(field, '__dict__'):
                                field_dict = {
                                    "name": getattr(field, 'name', ''),
                                    "type": getattr(field, 'type', 'string'),
                                    "display_name": getattr(field, 'display_name', ''),
                                    "description": getattr(field, 'description', ''),
                                    "required": getattr(field, 'required', False),
                                    "unique": getattr(field, 'unique', False),
                                    "validation": getattr(field, 'validation', {})
                                }
                                fields_data.append(field_dict)
                    
                    entity_data = {
                        "name": entity.name,
                        "display_name": entity.display_name or entity.name,
                        "description": entity.description or "",
                        "fields": fields_data
                    }
                    template_data["entities"].append(entity_data)
                template_data["template_info"]["preview"]["entities"] = len(entities)
            
            if request.includeAPIs:
                apis = db.query(APIRouteDBModel).all()
                template_data["apis"] = []
                for api in apis:
                    api_data = {
                        "api_id": api.api_id,
                        "name": api.name,
                        "endpoint": api.endpoint,
                        "method": api.method,
                        "description": api.description or "",
                        "handler_type": api.handler_type,
                        "handler_config": api.handler_config or {},
                        "auth_required": api.auth_required
                    }
                    template_data["apis"].append(api_data)
                template_data["template_info"]["preview"]["apis"] = len(apis)
            
            if request.includeRoles:
                roles = db.query(RoleDBModel).all()
                template_data["roles"] = []
                for role in roles:
                    role_data = {
                        "name": role.name,
                        "code": role.code,
                        "description": role.description or "",
                        "permissions": [p.name for p in role.permissions]
                    }
                    template_data["roles"].append(role_data)
            
            if request.includeWorkflows:
                workflows = db.query(WorkflowDBModel).all()
                template_data["workflows"] = []
                for workflow in workflows:
                    workflow_data = {
                        "name": workflow.name,
                        "description": workflow.description or "",
                        "business_scenario": workflow.business_scenario or "",
                        "user_intents": workflow.user_intents or [],
                        "trigger_keywords": workflow.trigger_keywords or [],
                        "inputs": workflow.inputs or [],
                        "nodes": workflow.nodes or []
                    }
                    template_data["workflows"].append(workflow_data)
                template_data["template_info"]["preview"]["workflows"] = len(workflows)
            
            template_data["forms"] = []
        
        if request.save_location == "custom" and request.custom_path:
            save_dir = Path(request.custom_path)
        else:
            save_dir = Path(__file__).parent.parent.parent / "templates"
        
        save_dir.mkdir(parents=True, exist_ok=True)
        
        template_file = save_dir / f"{template_key}.json"
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)
        
        template_service.reload_templates()
        
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "保存模板成功",
                "data": {
                    "template_key": template_key,
                    "name": request.name,
                    "file_path": str(template_file),
                    "preview": template_data["template_info"]["preview"]
                }
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "保存模板失败",
                "data": {
                    "error": "save_failed",
                    "details": str(e)
                }
            }
        )


@router.post(
    "/import",
    summary="导入模板",
    description="从 JSON文件导入模板"
)
async def import_template(
    file: UploadFile = File(...),
    _: dict = Depends(verify_developer_token)
):
    """导入模板从 JSON文件"""
    try:
        if not file.filename.endswith('.json'):
            raise UnifiedResponse.bad_request(
                message="仅支持JSON文件",
                error_type="invalid_file_type"
            )
        
        content = await file.read()
        template_data = json.loads(content)
        
        if "template_info" not in template_data:
            raise UnifiedResponse.bad_request(
                message="无效的模板文件",
                error_type="invalid_template_structure"
            )
        
        template_key = template_data["template_info"].get("key", file.filename.replace(".json", ""))
        templates_dir = Path(__file__).parent.parent.parent / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        template_file = templates_dir / f"{template_key}.json"
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)
        
        template_service.reload_templates()
        
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "导入模板成功",
                "data": {
                    "template_key": template_key,
                    "name": template_data["template_info"].get("name", template_key)
                }
            }
        )
    except json.JSONDecodeError:
        raise UnifiedResponse.bad_request(
            message="JSON格式错误",
            error_type="invalid_json"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="导入模板失败",
            error_type="import_failed",
            details=str(e)
        )


@router.get(
    "/download-example",
    summary="下载模板示例文档",
    description="下载模板结构示例文档，用于参考和自定义模板"
)
async def download_template_example(
    _: dict = Depends(verify_developer_token)
):
    """下载模板示例文档"""
    try:
        example_template = {
            "template_info": {
                "key": "example_template",
                "name": "示例模板",
                "description": "这是一个模板示例，展示了完整的模板结构",
                "category": "CUSTOM",
                "difficulty": "BEGINNER",
                "estimated_setup_time": "30分钟",
                "version": "1.0.0",
                "author": "Your Name",
                "license": "MIT",
                "features": ["功能1", "功能2", "功能3"],
                "tags": ["标签1", "标签2"],
                "created_at": "2024-01-01T00:00:00.000Z",
                "updated_at": "2024-01-01T00:00:00.000Z",
                "preview": {"entities": 2, "workflows": 1, "forms": 1, "apis": 3}
            },
            "entities": [
                {
                    "name": "product",
                    "display_name": "产品",
                    "description": "产品实体",
                    "fields": [
                        {"name": "name", "type": "string", "display_name": "产品名称", "required": True},
                        {"name": "price", "type": "number", "display_name": "价格", "required": True}
                    ]
                }
            ],
            "apis": [],
            "roles": [],
            "workflows": [],
            "forms": []
        }
        
        json_str = json.dumps(example_template, ensure_ascii=False, indent=2)
        json_bytes = json_str.encode('utf-8')
        
        from fastapi.responses import Response
        return Response(
            content=json_bytes,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=template_example.json"}
        )
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="下载示例文档失败",
            error_type="download_failed",
            details=str(e)
        )


# ============================================================
# 动态路由（/{template_key} 相关的路由）
# ============================================================

@router.get(
    "/{template_key}/sample-data",
    summary="获取模板示例数据信息",
    description="获取指定模板的示例数据统计信息"
)
async def get_template_sample_data_info(
    template_key: str,
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """获取模板示例数据信息接口"""
    print(f"🔍 [sample-data] 收到请求: template_key={template_key}")
    result = template_service.has_sample_data(template_key)
    print(f"🔍 [sample-data] 返回结果: {result}")

    if result["success"]:
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "获取示例数据信息成功",
                "data": result["data"]
            }
        )
    else:
        if result["error"] == "template_not_found":
            status_code = 404
            message = "模板不存在"
        else:
            status_code = 500
            message = "获取示例数据信息失败"

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
    "/{template_key}/sample-data/import",
    summary="导入模板示例数据",
    description="将模板的示例数据导入到数据库中"
)
async def import_template_sample_data(
    template_key: str,
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """导入模板示例数据接口"""
    result = template_service.import_sample_data(template_key)

    if result["success"]:
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "导入示例数据成功",
                "data": result["data"]
            }
        )
    else:
        if result["error"] == "template_not_found":
            status_code = 404
            message = "模板不存在"
        else:
            status_code = 500
            message = "导入示例数据失败"

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
    "/{template_key}/data",
    summary="获取模板数据",
    description="获取指定模板的实体、API、角色等数据，用于后续配置步骤"
)
async def get_template_data(
    template_key: str,
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """获取模板数据接口"""
    result = template_service.get_applied_template_data(template_key)

    if result["success"]:
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "获取模板数据成功",
                "data": result["data"]
            }
        )
    else:
        if result["error"] == "template_not_found":
            status_code = 404
            message = "模板不存在"
        else:
            status_code = 500
            message = "获取模板数据失败"

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
    "/{template_key}/export",
    summary="导出模板",
    description="导出模板为JSON文件"
)
async def export_template(
    template_key: str,
    _: dict = Depends(verify_developer_token)
):
    """导出模板为JSON文件"""
    try:
        templates_dir = Path(__file__).parent.parent.parent / "templates"
        template_file = templates_dir / f"{template_key}.json"
        
        if not template_file.exists():
            raise UnifiedResponse.not_found(
                message="模板不存在",
                error_type="template_not_found"
            )
        
        return FileResponse(
            path=str(template_file),
            filename=f"{template_key}.json",
            media_type="application/json"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="导出模板失败",
            error_type="export_failed",
            details=str(e)
        )


@router.post(
    "/{template_key}/apply",
    response_model=TemplateApplyResponse,
    summary="应用模板到系统",
    description="将指定模板的配置应用到系统中，创建相应的实体、API、角色等"
)
async def apply_template(
    template_key: str,
    request: TemplateApplyRequest,
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """应用模板接口"""
    result = template_service.apply_template(
        template_key=template_key,
        scenario_name=request.scenario_name,
        description=request.description,
        customizations=request.customizations
    )

    if result["success"]:
        response_data = result["data"]
        
        if request.import_sample_data:
            sample_result = template_service.import_sample_data(template_key)
            response_data["sample_data_import"] = sample_result.get("data") if sample_result.get("success") else {
                "error": sample_result.get("error"),
                "details": sample_result.get("details")
            }
        
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "应用模板成功",
                "data": response_data
            }
        )
    else:
        if result["error"] == "template_not_found":
            status_code = 404
            message = "模板不存在"
        else:
            status_code = 500
            message = "应用模板失败"

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
    "/{template_key}",
    summary="删除模板",
    description="删除自定义模板（系统模板不可删除）"
)
async def delete_template(
    template_key: str,
    _: dict = Depends(verify_developer_token)
):
    """删除自定义模板"""
    try:
        SYSTEM_TEMPLATES = ['ecommerce_basic', 'hospital_management', 'railway_ticketing']
        
        if template_key in SYSTEM_TEMPLATES:
            raise UnifiedResponse.forbidden(
                message="系统模板不可删除",
                error_type="system_template_protected",
                details=f"模板 '{template_key}' 是系统预设模板，不允许删除"
            )
        
        templates_dir = Path(__file__).parent.parent.parent / "templates"
        template_file = templates_dir / f"{template_key}.json"
        
        if not template_file.exists():
            raise UnifiedResponse.not_found(
                message="模板不存在",
                error_type="template_not_found"
            )
        
        os.remove(template_file)
        template_service.reload_templates()
        
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "删除模板成功",
                "data": {}
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise UnifiedResponse.internal_error(
            message="删除模板失败",
            error_type="delete_failed",
            details=str(e)
        )


@router.get(
    "/{template_key}",
    response_model=TemplateDetailResponse,
    summary="获取特定模板详细配置",
    description="获取指定模板的详细配置信息，包括完整的实体、工作流、表单等配置"
)
async def get_template_detail(
    template_key: str,
    authorization: Optional[str] = Header(None),
    _: dict = Depends(verify_developer_token)
):
    """获取特定模板详细配置接口"""
    result = template_service.get_template_detail(template_key)
    
    if result["success"]:
        template_detail = result["data"]["template"]
        
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "获取模板详情成功",
                "data": {
                    "template": template_detail.model_dump()
                }
            }
        )
    else:
        if result["error"] == "template_not_found":
            status_code = 404
            message = "模板不存在"
        else:
            status_code = 500
            message = "获取模板详情失败"
        
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
