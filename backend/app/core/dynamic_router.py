"""
动态路由管理器
支持运行时动态添加和删除API路由
增强动态响应功能
"""
import json
import time
import logging
import re
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, Callable, Optional, List
from pathlib import Path
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.routing import APIRoute
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from PIL import Image, ImageDraw, ImageFont

from app.core.database import get_db_session
from app.models.api_route import APIRouteDBModel, APIRouteCallLogDBModel, RouteStatus, HandlerType
from app.models.user import User as UserDBModel
from app.models.role import RoleDBModel
from app.services.permission_service import PermissionService
from app.core.auth import verify_developer_token
from app.core.auth.jwt_handler import verify_token
from app.core.permissions import extract_user_from_token, PermissionDenied
from app.core.dynamic_response_engine import DynamicResponseEngine

from app.core.logging_config import get_logger
from app.core.utils import generate_id

logger = get_logger(__name__)


class JSONSerializableEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理datetime、date、Decimal等特殊类型"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """安全的JSON序列化，自动处理datetime等特殊类型"""
    kwargs.setdefault('cls', JSONSerializableEncoder)
    kwargs.setdefault('ensure_ascii', False)
    return json.dumps(obj, **kwargs)


class DynamicRouteHandler:
    """动态路由处理器"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.dynamic_routes: Dict[str, APIRoute] = {}
        self.response_engine = DynamicResponseEngine()  # 添加动态响应引擎
        self.permission_service = PermissionService()  # 添加权限服务
        # 启动时加载数据库中已激活的动态路由
        try:
            self._load_active_routes_from_database()
        except Exception:
            # 启动阶段不阻断主流程，后续可通过接口再次注册
            pass

    _sql_identifier_pattern = re.compile(r"^[A-Za-z_\u4e00-\u9fff][A-Za-z0-9_\u4e00-\u9fff]*$")

    def _sanitize_sql_identifier(self, value: str, default: Optional[str] = None) -> str:
        """校验 SQL 标识符（表名/字段名），不允许注入字符。"""
        raw = str(value or "").strip()
        if not raw:
            if default is not None:
                return default
            raise ValueError("SQL 标识符为空")
        if self._sql_identifier_pattern.match(raw):
            return raw

        normalized = re.sub(r"[^A-Za-z0-9_\u4e00-\u9fff]", "_", raw)
        normalized = re.sub(r"_+", "_", normalized).strip("_")
        if normalized and normalized[0].isdigit():
            normalized = f"f_{normalized}"

        if normalized and self._sql_identifier_pattern.match(normalized):
            logger.warning(f"SQL标识符 '{raw}' 已规范化为 '{normalized}'")
            return normalized

        if default is not None:
            logger.warning(f"非法SQL标识符 '{raw}'，回退为 '{default}'")
            return default
        raise ValueError(f"非法SQL标识符: {raw}")

    def _quote_identifier(self, value: str, default: Optional[str] = None) -> str:
        safe = self._sanitize_sql_identifier(value, default=default)
        return f"`{safe}`"

    def _build_entity_table_name(self, entity: str) -> str:
        """构建并清洗动态实体表名。"""
        raw = str(entity or "").strip().lower()
        cleaned = re.sub(r"[^A-Za-z0-9_\u4e00-\u9fff]", "_", raw)
        cleaned = re.sub(r"_+", "_", cleaned).strip("_")
        if not cleaned:
            cleaned = "unknown"
        if not re.match(r"^[A-Za-z_\u4e00-\u9fff]", cleaned):
            cleaned = f"e_{cleaned}"
        return f"entity_{cleaned}"
    
    async def _check_route_permission(self, request: Request, route_config: APIRouteDBModel, user_info: dict, db) -> bool:
        """检查路由权限 - 使用 PermissionService"""
        try:
            logger.info(f"权限检查开始 - 路由: {route_config.endpoint}, 用户信息: {user_info}")
            
            # 开发者token特殊处理
            if user_info.get("user_type") == "developer":
                logger.info("开发者token，允许访问")
                return True
            
            # 获取用户对象
            user = db.query(UserDBModel).filter(UserDBModel.id == user_info["user_id"]).first()
            if not user:
                logger.warning(f"用户不存在: {user_info['user_id']}")
                return False
            
            # 检查用户是否有访问此API的权限
            user_permissions = self.permission_service.get_user_permissions(user, db)
            required_perm = f"{route_config.api_id}:access"
            
            logger.info(f"用户权限: {user_permissions}")
            logger.info(f"需要权限: {required_perm}")
            
            has_permission = (
                required_perm in user_permissions or
                f"{route_config.api_id}:*" in user_permissions or
                "*:*" in user_permissions
            )
            
            logger.info(f"权限检查结果: {has_permission}")
            return has_permission
            
        except Exception as e:
            logger.error(f"权限检查异常: {e}")
            return False
    
    async def _legacy_permission_check(self, request: Request, route_config: APIRouteDBModel, user_info: dict, db) -> bool:
        """旧版权限检查逻辑（向后兼容）"""
        try:
            user = db.query(UserDBModel).filter(UserDBModel.id == user_info["user_id"]).first()
            if not user:
                return False
                
            # 获取用户角色信息
            role = db.query(RoleDBModel).filter(RoleDBModel.id == user.role_id).first() if user.role_id else None
            if not role:
                return False
                
            # 权限验证
            role_permission_names = [p.name for p in getattr(role, 'permissions', [])] if role else []
            required_perm = f"{route_config.api_id}:access" if route_config.api_id else None
            wildcard_for_api = f"{route_config.api_id}:*" if route_config.api_id else None
            has_access = (
                (required_perm and required_perm in role_permission_names) or
                (wildcard_for_api and wildcard_for_api in role_permission_names) or
                ("*:*" in role_permission_names)
            )

            # 如果未通过精确权限，再回退到较宽松的端点级别校验
            if not has_access:
                perm_service = PermissionService()
                user_permissions = perm_service.get_user_permissions(user, db)
                # 简单的端点权限检查
                has_access = "*:*" in user_permissions or "user:*" in user_permissions
            
            return has_access
            
        except Exception as e:
            logger.error(f"旧版权限检查异常: {e}")
            return False
        
    async def handle_entity_crud(self, route_config: Dict[str, Any], request: Request) -> Dict[str, Any]:
        """处理实体CRUD操作 - 增强版，支持真实数据库操作"""
        from app.models.entity import EntityDBModel, EntityFieldDBModel
        import json
        from sqlalchemy import and_, or_, desc, asc, text
        
        handler_config = route_config.get("handler_config", {})
        entity = (
            handler_config.get("entity")
            or handler_config.get("entity_name")
            or handler_config.get("entityName")
            or "unknown"
        )
        operation = handler_config.get("operation", "list")
        
        # 获取路由配置以确定响应格式
        api_id = route_config.get("api_id")
        
        try:
            with get_db_session() as db:
                # 获取实体定义
                entity_model = db.query(EntityDBModel).filter(EntityDBModel.name == entity).first()
                if not entity_model:
                    return {
                        "code": 404,
                        "message": f"实体 '{entity}' 不存在",
                        "data": None
                    }

                # 获取实体字段定义
                entity_fields = db.query(EntityFieldDBModel).filter(
                    EntityFieldDBModel.entity_id == entity_model.id
                ).all()
                field_definitions = {f.name: f for f in entity_fields}
                
                # 根据操作类型处理
                if operation == "list":
                    return await self._handle_entity_list(
                        entity,
                        entity_model,
                        field_definitions,
                        request,
                        db,
                        enable_search=False,
                        handler_config=handler_config,
                        request_data=route_config.get("request_data", {}) if isinstance(route_config, dict) else {},
                    )
                elif operation == "search":
                    # search 操作复用 list 逻辑，但启用搜索功能
                    return await self._handle_entity_list(
                        entity,
                        entity_model,
                        field_definitions,
                        request,
                        db,
                        enable_search=True,
                        handler_config=handler_config,
                        request_data=route_config.get("request_data", {}) if isinstance(route_config, dict) else {},
                    )
                elif operation == "create":
                    return await self._handle_entity_create(entity, entity_model, field_definitions, request, db, api_id)
                elif operation == "get":
                    return await self._handle_entity_get(entity, entity_model, field_definitions, request, db, handler_config)
                elif operation == "update":
                    return await self._handle_entity_update(
                        entity,
                        entity_model,
                        field_definitions,
                        request,
                        db,
                        api_id,
                        handler_config=handler_config,
                    )
                elif operation == "delete":
                    return await self._handle_entity_delete(
                        entity,
                        entity_model,
                        field_definitions,
                        request,
                        db,
                        handler_config=handler_config,
                    )
                else:
                    return {
                        "code": 400,
                        "message": f"不支持的操作: {operation}",
                        "data": None
                    }
        except Exception as e:
            return {
                "code": 500,
                "message": f"处理实体操作失败: {str(e)}",
                "data": None
            }
    
    async def handle_custom_function(self, route_config: Dict[str, Any], request: Request) -> Dict[str, Any]:
        """处理自定义函数"""
        handler_config = route_config.get("handler_config", {})
        service_name = handler_config.get("service")
        method_name = handler_config.get("method")

        # 新模式：service + method 走服务分发器
        if service_name and method_name:
            try:
                from app.services.service_dispatcher import dispatch_service_call
                request_data = route_config.get("request_data", {}) if isinstance(route_config, dict) else {}
                return await dispatch_service_call(
                    service_name,
                    method_name,
                    request_data=request_data,
                    route_config=route_config,
                    request=request,
                )
            except Exception as e:
                return {
                    "code": 500,
                    "message": f"服务调用失败: {service_name}.{method_name}",
                    "data": {"error": str(e)},
                }

        # 兼容旧模式：function
        function_name = handler_config.get("function", "default")
        return {
            "code": 200,
            "message": f"执行自定义函数 {function_name} 成功",
            "data": {
                "function": function_name,
                "executed_at": "2024-01-20T10:00:00.000Z",
                "result": "success"
            }
        }
    
    async def handle_static_data(self, route_config: Dict[str, Any], request: Request) -> Dict[str, Any]:
        """处理静态数据返回"""
        handler_config = route_config.get("handler_config", {})
        static_data = handler_config.get("data", {})
        
        return {
            "code": 200,
            "message": "返回静态数据成功",
            "data": static_data
        }
    
    async def handle_proxy(self, route_config: Dict[str, Any], request: Request) -> Dict[str, Any]:
        """处理代理转发"""
        handler_config = route_config.get("handler_config", {})
        target_url = handler_config.get("target_url", "")
        
        return {
            "code": 200,
            "message": f"代理转发到 {target_url} 成功",
            "data": {
                "proxy_target": target_url,
                "original_path": str(request.url.path),
                "method": request.method
            }
        }
    
    async def handle_script(self, route_config: Dict[str, Any], request: Request) -> Dict[str, Any]:
        """Handle script execution."""
        handler_config = route_config.get("handler_config", {})
        script = handler_config.get("script") or handler_config.get("code") or ""
        language = (handler_config.get("language") or "python").lower()
        if language not in {"python"}:
            return {"code": 400, "message": f"Unsupported script language: {language}", "data": None}
        from app.services.script_executor import execute_script
        request_data = route_config.get("request_data", {}) if isinstance(route_config, dict) else {}
        state_user = getattr(request.state, "user", None)
        state_user_info = getattr(request.state, "user_info", None)

        user_payload: Optional[Dict[str, Any]] = None
        if isinstance(state_user, dict):
            user_payload = dict(state_user)
        elif state_user is not None:
            user_payload = {
                "id": getattr(state_user, "id", None),
                "user_id": getattr(state_user, "id", None),
                "username": getattr(state_user, "username", None),
                "real_name": getattr(state_user, "real_name", None),
                "phone": getattr(state_user, "phone", None),
                "email": getattr(state_user, "email", None),
                "role_id": getattr(state_user, "role_id", None),
                "status": getattr(state_user, "status", None),
            }
        elif isinstance(state_user_info, dict):
            user_payload = {
                "id": state_user_info.get("user_id"),
                "user_id": state_user_info.get("user_id"),
                "username": state_user_info.get("username"),
                "user_type": state_user_info.get("user_type"),
            }

        user_id = getattr(request.state, "user_id", None)
        if user_payload and user_id is not None and user_payload.get("user_id") is None:
            user_payload["user_id"] = user_id

        context = {
            "request": request_data,
            "path": request_data.get("path"),
            "query": request_data.get("query"),
            "body": request_data.get("body"),
            "headers": request_data.get("header"),
            "user_id": user_id,
            "user_info": state_user_info if isinstance(state_user_info, dict) else None,
            "user": user_payload,
        }
        return execute_script(script, context)


    async def handle_workflow(self, route_config: Dict[str, Any], request: Request) -> Dict[str, Any]:
        """处理工作流触发"""
        handler_config = route_config.get("handler_config", {})
        workflow_id = handler_config.get("workflow_id", "")
        
        return {
            "code": 200,
            "message": f"触发工作流 {workflow_id} 成功",
            "data": {
                "workflow_id": workflow_id,
                "instance_id": f"instance_{int(time.time())}",
                "status": "running"
            }
        }
    
    async def handle_file_upload(self, route_config: Dict[str, Any], request: Request) -> Dict[str, Any]:
        """处理文件上传"""
        from fastapi import UploadFile, File
        import os
        import uuid
        from pathlib import Path
        
        handler_config = route_config.get("handler_config", {})
        upload_path = handler_config.get("upload_path", "")
        max_file_size = handler_config.get("max_file_size", "10MB")
        allowed_extensions = handler_config.get("allowed_extensions", [".jpg", ".png", ".pdf", ".doc"])
        auto_rename = handler_config.get("auto_rename", True)
        
        try:
            # 创建上传目录（规范化，避免出现 uploads/uploads）
            upload_subdir = str(upload_path or "").strip()
            upload_subdir = upload_subdir.replace("\\", "/")
            if upload_subdir in ("uploads", "/uploads") or upload_subdir.startswith("uploads/") or upload_subdir.startswith("/uploads/"):
                upload_subdir = upload_subdir.replace("/uploads", "", 1)
                if not upload_subdir:
                    upload_subdir = ""
            if upload_subdir and not upload_subdir.startswith("/"):
                upload_subdir = "/" + upload_subdir
            upload_dir = Path(f"uploads{upload_subdir}")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取表单数据
            form = await request.form()
            uploaded_files = []
            
            for key, value in form.items():
                if hasattr(value, 'filename') and value.filename:
                    # 这是一个文件
                    file_content = await value.read()
                    file_size = len(file_content)
                    
                    # 检查文件大小
                    max_size_bytes = self._parse_file_size(max_file_size)
                    if file_size > max_size_bytes:
                        raise HTTPException(status_code=413, detail=f"文件大小超过限制 {max_file_size}")
                    
                    # 检查文件扩展名
                    file_ext = Path(value.filename).suffix.lower()
                    if allowed_extensions and file_ext not in allowed_extensions:
                        raise HTTPException(status_code=400, detail=f"不支持的文件类型 {file_ext}")
                    
                    # 生成文件名
                    if auto_rename:
                        filename = f"{uuid.uuid4().hex}_{int(time.time())}{file_ext}"
                    else:
                        filename = value.filename
                    
                    # 保存文件
                    file_path = upload_dir / filename
                    with open(file_path, "wb") as buffer:
                        buffer.write(file_content)
                    
                    uploaded_files.append({
                        "original_name": value.filename,
                        "filename": filename,
                        "size": file_size,
                        "content_type": getattr(value, 'content_type', 'application/octet-stream'),
                        "url": f"/api/v1/files/serve/{filename}"
                    })
            
            return {
                "code": 200,
                "message": f"文件上传成功，共上传 {len(uploaded_files)} 个文件",
                "data": {
                    "files": uploaded_files,
                    "upload_path": upload_subdir or "/",
                    "total_count": len(uploaded_files)
                }
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
    
    async def handle_image_display(self, route_config: Dict[str, Any], request: Request) -> Response:
        """处理图片显示 - 增强版，支持动态调整和多种业务场景"""
        from fastapi.responses import FileResponse, StreamingResponse
        from PIL import Image
        import os
        import io
        
        handler_config = route_config.get("handler_config", {})
        image_source = handler_config.get("image_source", "file")  # file, entity, url
        image_root = handler_config.get("image_root", "/images")
        resize_options = handler_config.get("resize_options", {})
        cache_duration = handler_config.get("cache_duration", 3600)
        watermark_config = handler_config.get("watermark", {})
        default_image_identifier = (
            handler_config.get("image_identifier")
            or handler_config.get("image_id")
            or handler_config.get("default_image")
            or handler_config.get("image_path")
        )
        
        try:
            # 从URL路径中提取图片标识（优先使用路径参数）
            path_params = getattr(request, "path_params", {}) or {}
            query_params = dict(request.query_params)
            image_identifier = path_params.get("image_id") or path_params.get("id")
            if not image_identifier:
                image_identifier = (
                    query_params.get("image_id")
                    or query_params.get("id")
                    or query_params.get("filename")
                    or query_params.get("file")
                )
            if not image_identifier:
                image_identifier = default_image_identifier
            if not image_identifier:
                path_parts = [part for part in request.url.path.split("/") if part]
                candidate = path_parts[-1] if path_parts else ""
                if candidate and candidate not in {"image", "images", "img"}:
                    image_identifier = candidate
            
            # 获取查询参数用于动态调整
            width = query_params.get("w") or query_params.get("width")
            height = query_params.get("h") or query_params.get("height")
            quality = int(query_params.get("q", query_params.get("quality", 85)))
            format_type = query_params.get("f") or query_params.get("format", "").lower()
            
            # 覆盖配置中的调整选项
            if width or height:
                resize_options = {
                    "width": int(width) if width else resize_options.get("width"),
                    "height": int(height) if height else resize_options.get("height"),
                    "quality": quality
                }
            
            image_path = None
            
            # 根据图片源类型获取图片路径
            if image_source == "file":
                # 直接文件访问
                image_dir = Path(f"uploads{image_root}")
                if image_identifier:
                    image_path = image_dir / image_identifier
                else:
                    image_path = self._find_latest_image([image_dir, Path("uploads")])
                    if image_path:
                        image_identifier = image_path.name
            
            elif image_source == "entity":
                # 从实体数据中获取图片
                entity_type = handler_config.get("entity_type", "user")
                entity_id = handler_config.get("entity_id") or path_params.get("entity_id") or path_params.get("id")
                if not entity_id:
                    path_parts = request.url.path.split("/")
                    entity_id = path_parts[-2] if len(path_parts) > 1 else None
                field_name = handler_config.get("field_name", "avatar")
                
                if entity_id:
                    with get_db_session() as db:
                        from sqlalchemy import text
                        table_name = f"entity_{str(entity_type).lower()}"
                        
                        query = text(f"SELECT {field_name} FROM {table_name} WHERE id = :entity_id")
                        result = db.execute(query, {"entity_id": entity_id}).fetchone()
                        
                        if result and result[0]:
                            # 假设字段中存储的是相对路径
                            image_path = Path("uploads") / result[0]
            
            elif image_source == "url":
                # 从URL下载并缓存
                source_url = handler_config.get("source_url", "")
                if source_url:
                    import requests
                    import hashlib
                    
                    # 生成缓存文件名
                    url_hash = hashlib.md5(source_url.encode()).hexdigest()
                    cache_dir = Path("uploads/cache/images")
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    image_path = cache_dir / f"{url_hash}_{image_identifier}"
                    
                    # 如果缓存不存在或过期，下载图片
                    if not image_path.exists() or (time.time() - image_path.stat().st_mtime) > cache_duration:
                        response = requests.get(source_url, timeout=10)
                        if response.status_code == 200:
                            with open(image_path, 'wb') as f:
                                f.write(response.content)
            
            # 检查图片文件是否存在
            if not image_path or not image_path.exists():
                # 返回默认图片或404
                default_image_path = Path("uploads/images/default.jpg")
                if default_image_path.exists():
                    image_path = default_image_path
                else:
                    raise HTTPException(status_code=404, detail="图片不存在")
            
            # 如果需要调整大小或添加水印
            if resize_options or watermark_config or format_type:
                return await self._process_image_with_effects(
                    image_path, resize_options, watermark_config, format_type, cache_duration
                )
            
            # 直接返回原图
            media_type = f"image/{image_path.suffix[1:]}"
            headers = {
                "Cache-Control": f"max-age={cache_duration}",
                "Content-Type": media_type
            }
            
            return FileResponse(
                path=str(image_path),
                headers=headers,
                filename=image_identifier
            )
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=500, detail=f"图片处理失败: {str(e)}")

    async def _process_image_with_effects(self, image_path: Path, resize_options: Dict, watermark_config: Dict, format_type: str, cache_duration: int) -> StreamingResponse:
        """处理图片效果（调整大小、水印等）"""
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        try:
            with Image.open(image_path) as img:
                # 调整大小
                if resize_options:
                    width = resize_options.get("width")
                    height = resize_options.get("height")
                    quality = resize_options.get("quality", 85)
                    
                    if width or height:
                        original_width, original_height = img.size
                        
                        if width and height:
                            # 指定宽高，可能会变形
                            img = img.resize((width, height), Image.Resampling.LANCZOS)
                        elif width:
                            # 只指定宽度，按比例缩放
                            ratio = width / original_width
                            new_height = int(original_height * ratio)
                            img = img.resize((width, new_height), Image.Resampling.LANCZOS)
                        elif height:
                            # 只指定高度，按比例缩放
                            ratio = height / original_height
                            new_width = int(original_width * ratio)
                            img = img.resize((new_width, height), Image.Resampling.LANCZOS)
                
                # 添加水印
                if watermark_config:
                    img = self._add_watermark(img, watermark_config)
                
                # 确定输出格式
                output_format = format_type.upper() if format_type else img.format or "JPEG"
                if output_format not in ["JPEG", "PNG", "WEBP", "GIF"]:
                    output_format = "JPEG"
                
                # 保存到内存
                img_io = io.BytesIO()
                save_kwargs = {}
                
                if output_format == "JPEG":
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    save_kwargs["quality"] = resize_options.get("quality", 85)
                    save_kwargs["optimize"] = True
                elif output_format == "PNG":
                    save_kwargs["optimize"] = True
                elif output_format == "WEBP":
                    save_kwargs["quality"] = resize_options.get("quality", 85)
                    save_kwargs["optimize"] = True
                
                img.save(img_io, format=output_format, **save_kwargs)
                img_io.seek(0)
                
                # 返回流式响应
                media_type = f"image/{output_format.lower()}"
                headers = {
                    "Cache-Control": f"max-age={cache_duration}",
                    "Content-Type": media_type
                }
                
                return StreamingResponse(
                    io.BytesIO(img_io.getvalue()),
                    media_type=media_type,
                    headers=headers
                )
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"图片处理失败: {str(e)}")

    def _find_latest_image(self, search_dirs: List[Path]) -> Optional[Path]:
        """在给定目录中查找最新图片文件"""
        allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
        latest_path = None
        latest_mtime = -1.0
        for dir_path in search_dirs:
            try:
                if not dir_path or not dir_path.exists():
                    continue
                for file_path in dir_path.iterdir():
                    if not file_path.is_file():
                        continue
                    if file_path.suffix.lower() not in allowed_exts:
                        continue
                    mtime = file_path.stat().st_mtime
                    if mtime > latest_mtime:
                        latest_mtime = mtime
                        latest_path = file_path
            except Exception:
                continue
        return latest_path

    def _add_watermark(self, img: Image.Image, watermark_config: Dict) -> Image.Image:
        """添加水印"""
        watermark_text = watermark_config.get("text", "")
        watermark_image = watermark_config.get("image", "")
        position = watermark_config.get("position", "bottom-right")
        opacity = watermark_config.get("opacity", 0.5)
        
        if watermark_text:
            # 文字水印
            draw = ImageDraw.Draw(img)
            font_size = watermark_config.get("font_size", 20)
            font_color = watermark_config.get("font_color", (255, 255, 255))
            
            try:
                # 尝试使用系统字体
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                # 使用默认字体
                font = ImageFont.load_default()
            
            # 计算文字大小
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # 计算位置
            x, y = self._calculate_watermark_position(img.size, (text_width, text_height), position)
            
            # 创建透明图层
            watermark_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
            watermark_draw = ImageDraw.Draw(watermark_layer)
            
            # 添加透明度
            color_with_alpha = font_color + (int(opacity * 255),)
            watermark_draw.text((x, y), watermark_text, font=font, fill=color_with_alpha)
            
            # 合成图片
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img = Image.alpha_composite(img, watermark_layer)
            
        elif watermark_image:
            # 图片水印
            try:
                watermark_path = Path("uploads/watermarks") / watermark_image
                if watermark_path.exists():
                    with Image.open(watermark_path) as wm:
                        # 调整水印大小
                        wm_size = watermark_config.get("size", 0.1)  # 相对于原图的比例
                        if wm_size < 1:
                            new_width = int(img.width * wm_size)
                            new_height = int(wm.height * new_width / wm.width)
                            wm = wm.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        
                        # 计算位置
                        x, y = self._calculate_watermark_position(img.size, wm.size, position)
                        
                        # 处理透明度
                        if wm.mode != 'RGBA':
                            wm = wm.convert('RGBA')
                        
                        # 调整整体透明度
                        if opacity < 1:
                            alpha = wm.split()[-1]
                            alpha = alpha.point(lambda i: int(i * opacity))
                            wm.putalpha(alpha)
                        
                        # 合成图片
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')
                        img.paste(wm, (x, y), wm)
            except Exception as e:
                logger.warning(f"⚠️ 添加图片水印失败: {e}")
        
        return img

    def _calculate_watermark_position(self, img_size: tuple, watermark_size: tuple, position: str) -> tuple:
        """计算水印位置"""
        img_width, img_height = img_size
        wm_width, wm_height = watermark_size
        margin = 10
        
        position_map = {
            "top-left": (margin, margin),
            "top-center": ((img_width - wm_width) // 2, margin),
            "top-right": (img_width - wm_width - margin, margin),
            "center-left": (margin, (img_height - wm_height) // 2),
            "center": ((img_width - wm_width) // 2, (img_height - wm_height) // 2),
            "center-right": (img_width - wm_width - margin, (img_height - wm_height) // 2),
            "bottom-left": (margin, img_height - wm_height - margin),
            "bottom-center": ((img_width - wm_width) // 2, img_height - wm_height - margin),
            "bottom-right": (img_width - wm_width - margin, img_height - wm_height - margin),
        }
        
        return position_map.get(position, position_map["bottom-right"])
    
    async def handle_file_download(self, route_config: Dict[str, Any], request: Request) -> Response:
        """处理文件下载"""
        from fastapi.responses import FileResponse
        
        handler_config = route_config.get("handler_config", {})
        file_root = handler_config.get("file_root", "")
        security_check = handler_config.get("security_check", True)
        disposition = handler_config.get("disposition", "attachment")
        
        try:
            # 从URL路径中提取文件名（优先使用路径参数）
            path_params = getattr(request, "path_params", {}) or {}
            filename = path_params.get("filename") or path_params.get("file") or path_params.get("id")
            if not filename:
                path_parts = request.url.path.split("/")
                filename = path_parts[-1] if path_parts else "download"
            
            # 构建文件路径（规范化，避免出现 uploads/uploads）
            file_subdir = str(file_root or "").strip()
            file_subdir = file_subdir.replace("\\", "/")
            if file_subdir in ("uploads", "/uploads") or file_subdir.startswith("uploads/") or file_subdir.startswith("/uploads/"):
                file_subdir = file_subdir.replace("/uploads", "", 1)
                if not file_subdir:
                    file_subdir = ""
            if file_subdir and not file_subdir.startswith("/"):
                file_subdir = "/" + file_subdir
            file_dir = Path(f"uploads{file_subdir}")
            file_path = file_dir / filename
            
            # 安全检查
            if security_check:
                # 防止路径穿越攻击
                try:
                    file_path.resolve().relative_to(file_dir.resolve())
                except ValueError:
                    raise HTTPException(status_code=400, detail="非法的文件路径")
            
            # 检查文件是否存在
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="文件不存在")
            
            # 返回文件
            headers = {
                "Content-Disposition": f"{disposition}; filename={filename}"
            }
            
            return FileResponse(
                path=str(file_path),
                headers=headers,
                filename=filename
            )
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")
    
    async def handle_media_streaming(self, route_config: Dict[str, Any], request: Request) -> Dict[str, Any]:
        """处理媒体流"""
        handler_config = route_config.get("handler_config", {})
        media_root = handler_config.get("media_root", "/media")
        supported_formats = handler_config.get("supported_formats", ["mp4", "mp3", "wav"])
        
        return {
            "code": 200,
            "message": "媒体流处理成功",
            "data": {
                "media_root": media_root,
                "supported_formats": supported_formats,
                "streaming": True
            }
        }
    
    def _parse_file_size(self, size_str: str) -> int:
        """解析文件大小字符串，返回字节数"""
        size_str = size_str.upper()
        if size_str.endswith('B'):
            size_str = size_str[:-1]
        
        if size_str.endswith('K'):
            return int(size_str[:-1]) * 1024
        elif size_str.endswith('M'):
            return int(size_str[:-1]) * 1024 * 1024
        elif size_str.endswith('G'):
            return int(size_str[:-1]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    async def dynamic_route_handler(self, route_id: str, request: Request) -> Response:
        """动态路由处理函数 - 增强版，支持请求响应映射和新权限系统"""
        start_time = time.time()
        response_status = 500
        response_size = None
        request_data: Dict[str, Any] = {}
        route_config: Optional[APIRouteDBModel] = None
        try:
            # 从数据库获取路由配置
            with get_db_session() as db:
                route_config = db.query(APIRouteDBModel).filter(
                    APIRouteDBModel.id == route_id,
                    APIRouteDBModel.status == RouteStatus.ACTIVE
                ).first()
                
                if not route_config:
                    raise HTTPException(status_code=404, detail="路由不存在或已停用")

                # 添加日志记录
                logger.info(f"[DynamicRouter] 处理请求: {route_config.method} {route_config.endpoint}")
                logger.info(f"[DynamicRouter] API ID: {route_config.api_id}, 处理器类型: {route_config.handler_type}")

                # 详细输出路由配置和scheme信息
                logger.debug(f"[DynamicRouter] 动态路由调试信息:")
                logger.debug(f"[DynamicRouter] 路由ID: {route_id}")
                logger.debug(f"[DynamicRouter] API ID: {route_config.api_id}")
                logger.debug(f"[DynamicRouter] 路径: {route_config.endpoint}")
                logger.debug(f"[DynamicRouter] 方法: {route_config.method}")
                logger.debug(f"[DynamicRouter] 处理器类型: {route_config.handler_type}")
                
                # 输出响应配置的scheme信息
                if route_config.responses_config:
                    logger.debug(f"[DynamicRouter] 响应配置:")
                    for status_code, response_config in route_config.responses_config.items():
                        logger.debug(f"[DynamicRouter]   状态码 {status_code}:")
                        # 检查多种可能的schema键名
                        schema = None
                        if 'schema' in response_config:
                            schema = response_config['schema']
                        elif 'response_schema' in response_config:
                            schema = response_config['response_schema']
                        
                        if schema:
                            logger.debug(f"[DynamicRouter]     Schema类型: {schema.get('type', 'unknown')}")
                            if 'properties' in schema:
                                logger.debug(f"[DynamicRouter]     Schema属性: {list(schema['properties'].keys())}")
                                for prop_name, prop_def in schema['properties'].items():
                                    logger.debug(f"[DynamicRouter]       - {prop_name}: {prop_def.get('type', 'unknown')}")
                        else:
                            logger.debug(f"[DynamicRouter]     无Schema定义")
                else:
                    logger.debug(f"[DynamicRouter] 无响应配置")
                
                # 输出动态规则信息
                if route_config.dynamic_rules_config:
                    logger.debug(f"[DynamicRouter] 动态规则数量: {len(route_config.dynamic_rules_config)}")
                    for i, rule in enumerate(route_config.dynamic_rules_config):
                        logger.debug(f"[DynamicRouter]   规则{i+1}: {rule.get('condition', {}).get('type', 'unknown')}")
                else:
                    logger.debug(f"[DynamicRouter] 无动态规则配置")

                # 认证与权限校验
                if route_config.auth_required:
                    auth_header = request.headers.get("Authorization")
                    if not auth_header or not auth_header.startswith("Bearer "):
                        raise HTTPException(status_code=401, detail="缺少认证令牌")

                    token = auth_header[7:]

                    # 从token提取用户信息
                    try:
                        user_info = extract_user_from_token(token)
                    except HTTPException as e:
                        raise e
                    except Exception as e:
                        raise HTTPException(status_code=401, detail="无效的认证令牌")

                    # 权限检查
                    has_permission = await self._check_route_permission(request, route_config, user_info, db)
                    if not has_permission:
                        raise HTTPException(status_code=403, detail="权限不足，禁止访问该API")

                    # 将用户信息存储在请求状态中供动态响应引擎使用
                    request.state.user_id = user_info["user_id"]
                    request.state.user_info = user_info
                    request.state.user_type = user_info.get("user_type")

                    # 获取详细用户信息（如果需要）
                    if user_info.get("user_type") != "developer":
                        user = db.query(UserDBModel).filter(UserDBModel.id == user_info["user_id"]).first()
                        if user:
                            request.state.user = user
                            role = db.query(RoleDBModel).filter(RoleDBModel.id == user.role_id).first() if user.role_id else None
                            request.state.user_roles = [role.name] if role else []
                        else:
                            request.state.user = None
                            request.state.user_roles = []
                    else:
                        request.state.user = None
                        request.state.user_roles = ["developer"]

                else:
                    # 对于不需要认证的路由，设置默认的用户信息
                    request.state.user_id = None
                    request.state.user_info = None
                    request.state.user_type = "anonymous"
                    request.state.user = None
                    request.state.user_roles = ['guest']

                # 解析请求参数并进行验证
                request_data = await self._parse_and_validate_request(request, route_config)
                
                # 根据处理器类型处理请求
                handler_type = route_config.handler_type
                route_data = {
                    "id": route_config.id,
                    "api_id": route_config.api_id,
                    "handler_config": route_config.handler_config,
                    "request_data": request_data,
                    "responses_config": route_config.responses_config
                }
                
                # 输出处理器配置信息
                logger.debug(f"[DynamicRouter] 处理器执行信息:")
                logger.debug(f"[DynamicRouter] 处理器类型: {handler_type}")
                if route_config.handler_config:
                    logger.debug(f"[DynamicRouter] 处理器配置: {safe_json_dumps(route_config.handler_config, indent=2)}")
                else:
                    logger.debug(f"[DynamicRouter] 无处理器配置")
                
                # 支持新的字符串类型和旧的枚举类型
                handler_type_str = handler_type.value if hasattr(handler_type, 'value') else str(handler_type)
                logger.debug(f"[DynamicRouter] 处理器类型字符串: {handler_type_str}")

                if handler_type_str == "entity_crud":
                    logger.debug(f"[DynamicRouter] handle entity_crud...")
                    result = await self.handle_entity_crud(route_data, request)
                elif handler_type_str == "custom_function":
                    logger.debug(f"[DynamicRouter] handle custom_function...")
                    result = await self.handle_custom_function(route_data, request)
                elif handler_type_str == "static_data":
                    logger.debug(f"[DynamicRouter] handle static_data...")
                    result = await self.handle_static_data(route_data, request)
                elif handler_type_str == "proxy":
                    logger.debug(f"[DynamicRouter] handle proxy...")
                    result = await self.handle_proxy(route_data, request)
                elif handler_type_str == "script":
                    logger.debug(f"[DynamicRouter] handle script...")
                    result = await self.handle_script(route_data, request)
                elif handler_type_str == "workflow":
                    logger.debug(f"[DynamicRouter] handle workflow...")
                    result = await self.handle_workflow(route_data, request)
                elif handler_type_str == "file_upload":
                    logger.debug(f"[DynamicRouter] 处理文件上传...")
                    result = await self.handle_file_upload(route_data, request)
                elif handler_type_str == "image_display":
                    logger.debug(f"[DynamicRouter] 处理图像显示...")
                    response = await self.handle_image_display(route_data, request)
                    response_status = response.status_code or 200
                    response_size = getattr(response, "body", None)
                    if response_size is not None:
                        response_size = len(response_size)
                    self._record_route_call(
                        db,
                        route_config,
                        request,
                        request_data,
                        response_status,
                        int((time.time() - start_time) * 1000),
                        response_size
                    )
                    db.commit()
                    return response
                elif handler_type_str == "file_download":
                    logger.debug(f"[DynamicRouter] 处理文件下载...")
                    response = await self.handle_file_download(route_data, request)
                    response_status = response.status_code or 200
                    response_size = getattr(response, "body", None)
                    if response_size is not None:
                        response_size = len(response_size)
                    self._record_route_call(
                        db,
                        route_config,
                        request,
                        request_data,
                        response_status,
                        int((time.time() - start_time) * 1000),
                        response_size
                    )
                    db.commit()
                    return response
                elif handler_type_str == "media_streaming":
                    logger.debug(f"[DynamicRouter] 处理媒体流...")
                    result = await self.handle_media_streaming(route_data, request)
                else:
                    logger.error(f"❌ [DynamicRouter] 不支持的处理器类型: {handler_type_str}")
                    raise HTTPException(status_code=500, detail=f"不支持的处理器类型: {handler_type_str}")
                
                # 输出原始处理结果
                logger.debug(f"[DynamicRouter] 原始处理结果:")
                logger.debug(f"[DynamicRouter] 结果类型: {type(result)}")
                if isinstance(result, dict):
                    logger.debug(f"[DynamicRouter] 结果键: {list(result.keys())}")
                    if 'data' in result:
                        data = result['data']
                        if isinstance(data, list) and data:
                            logger.debug(f"[DynamicRouter] 数据列表长度: {len(data)}")
                            logger.debug(f"[DynamicRouter] 第一个数据项键: {list(data[0].keys()) if isinstance(data[0], dict) else 'N/A'}")
                        elif isinstance(data, dict):
                            logger.debug(f"[DynamicRouter] 数据对象键: {list(data.keys())}")
                logger.debug(f"[DynamicRouter] 原始结果预览: {safe_json_dumps(result)[:500]}...")
                # 获取动态响应规则
                dynamic_rules = route_config.dynamic_rules_config or []
                
                # 输出动态响应处理信息
                logger.debug(f"[DynamicRouter] 动态响应处理:")
                logger.debug(f"[DynamicRouter] 动态规则数量: {len(dynamic_rules)}")
                
                # 使用动态响应引擎生成响应，传入动态规则
                if dynamic_rules:
                    logger.debug(f"[DynamicRouter] 使用动态响应规则处理...")
                    for i, rule in enumerate(dynamic_rules):
                        logger.debug(f"[DynamicRouter]   规则{i+1}: {safe_json_dumps(rule, indent=4)}")
                    formatted_result = await self.response_engine.generate_response_with_rules(
                        result, route_config, request, request_data, dynamic_rules
                    )
                else:
                    logger.debug(f"[DynamicRouter] 使用标准响应处理...")
                    # 使用原始的响应引擎
                    formatted_result = await self.response_engine.generate_response(
                        result, route_config, request, request_data
                    )
                
                # 输出最终格式化结果
                logger.debug(f"[DynamicRouter] 最终响应结果:")
                logger.debug(f"[DynamicRouter] 格式化后类型: {type(formatted_result)}")
                if isinstance(formatted_result, dict):
                    logger.debug(f"[DynamicRouter] 格式化后键: {list(formatted_result.keys())}")
                    if 'data' in formatted_result:
                        data = formatted_result['data']
                        if isinstance(data, list) and data:
                            logger.debug(f"[DynamicRouter] 格式化数据列表长度: {len(data)}")
                            logger.debug(f"[DynamicRouter] 格式化第一个数据项键: {list(data[0].keys()) if isinstance(data[0], dict) else 'N/A'}")
                        elif isinstance(data, dict):
                            logger.debug(f"[DynamicRouter] 格式化数据对象键: {list(data.keys())}")
                logger.debug(f"[DynamicRouter] 最终结果预览: {safe_json_dumps(formatted_result)[:500]}...")
                
                # 对比原始结果和格式化结果的差异
                if result != formatted_result:
                    logger.debug(f"[DynamicRouter] 原始结果与格式化结果存在差异")
                    if isinstance(result, dict) and isinstance(formatted_result, dict):
                        original_keys = set(result.keys())
                        formatted_keys = set(formatted_result.keys())
                        added_keys = formatted_keys - original_keys
                        removed_keys = original_keys - formatted_keys
                        if added_keys:
                            logger.debug(f"  新增字段: {list(added_keys)}")
                        if removed_keys:
                            logger.debug(f"  移除字段: {list(removed_keys)}")
                else:
                    logger.debug("原始结果与格式化结果一致")
                
                # 添加日志记录响应
                logger.info(f"[DynamicRouter] 响应成功: {route_config.method} {route_config.endpoint}")
                if isinstance(formatted_result, dict):
                    logger.debug(f"[DynamicRouter] 响应数据: {safe_json_dumps(formatted_result)[:500]}")
                
                # 兼容动态响应模板返回的 {status_code, headers, body} 结构
                if isinstance(formatted_result, Response):
                    response_status = formatted_result.status_code or 200
                    response_size = getattr(formatted_result, "body", None)
                    if response_size is not None:
                        response_size = len(response_size)
                    self._record_route_call(
                        db,
                        route_config,
                        request,
                        request_data,
                        response_status,
                        int((time.time() - start_time) * 1000),
                        response_size
                    )
                    db.commit()
                    return formatted_result
                if isinstance(formatted_result, dict) and "status_code" in formatted_result and "body" in formatted_result:
                    status_code = formatted_result.get("status_code", 200)
                    headers = formatted_result.get("headers") or {}
                    body = formatted_result.get("body")
                    if isinstance(body, (dict, list)):
                        content = safe_json_dumps(body)
                        media_type = "application/json"
                    else:
                        content = "" if body is None else str(body)
                        media_type = "text/plain"
                    response_status = status_code
                    response_size = len(content.encode("utf-8")) if isinstance(content, str) else None
                    response = Response(
                        content=content,
                        status_code=status_code,
                        headers=headers,
                        media_type=media_type
                    )
                    self._record_route_call(
                        db,
                        route_config,
                        request,
                        request_data,
                        response_status,
                        int((time.time() - start_time) * 1000),
                        response_size
                    )
                    db.commit()
                    return response
                
                content = safe_json_dumps(formatted_result)
                response_status = 200
                response_size = len(content.encode("utf-8")) if isinstance(content, str) else None
                response = Response(
                    content=content,
                    media_type="application/json"
                )
                self._record_route_call(
                    db,
                    route_config,
                    request,
                    request_data,
                    response_status,
                    int((time.time() - start_time) * 1000),
                    response_size
                )
                db.commit()
                return response
                
        except HTTPException as e:
            response_status = e.status_code
            if route_config:
                try:
                    with get_db_session() as db:
                        db_route = db.query(APIRouteDBModel).filter(APIRouteDBModel.id == route_config.id).first()
                        if db_route:
                            self._record_route_call(
                                db,
                                db_route,
                                request,
                                request_data,
                                response_status,
                                int((time.time() - start_time) * 1000),
                                response_size
                            )
                            db.commit()
                except Exception:
                    pass
            raise
        except Exception as e:
            logger.error(f"[DynamicRouter] 处理失败: {str(e)}")
            if route_config:
                try:
                    with get_db_session() as db:
                        db_route = db.query(APIRouteDBModel).filter(APIRouteDBModel.id == route_config.id).first()
                        if db_route:
                            self._record_route_call(
                                db,
                                db_route,
                                request,
                                request_data,
                                500,
                                int((time.time() - start_time) * 1000),
                                response_size
                            )
                            db.commit()
                except Exception:
                    pass
            raise HTTPException(status_code=500, detail=f"处理动态路由失败: {str(e)}")

    def _record_route_call(
        self,
        db: Session,
        route_config: APIRouteDBModel,
        request: Request,
        request_data: Dict[str, Any],
        response_status: int,
        response_time_ms: int,
        response_size: Optional[int] = None
    ) -> None:
        """记录路由调用日志并更新统计"""
        try:
            previous_count = route_config.call_count or 0
            new_count = previous_count + 1
            route_config.call_count = new_count
            route_config.last_called = datetime.utcnow()

            prev_avg = route_config.avg_response_time or 0
            if new_count > 0:
                route_config.avg_response_time = int(round((prev_avg * previous_count + response_time_ms) / new_count))
            else:
                route_config.avg_response_time = response_time_ms

            try:
                client_ip = request.client.host if request.client else None
            except Exception:
                client_ip = None

            try:
                request_body = request_data.get("body")
                if isinstance(request_body, (dict, list)):
                    request_body = safe_json_dumps(request_body)
                elif request_body is not None:
                    request_body = str(request_body)
            except Exception:
                request_body = None

            call_log = APIRouteCallLogDBModel(
                id=generate_id("call"),
                route_id=route_config.id,
                request_method=request.method,
                request_path=str(request.url.path),
                request_params=request_data,
                request_headers=dict(request.headers),
                request_body=request_body,
                response_status=response_status,
                response_time=response_time_ms,
                response_size=response_size,
                client_ip=client_ip,
                user_agent=request.headers.get("user-agent"),
                user_id=getattr(request.state, "user_id", None)
            )
            db.add(call_log)
        except Exception as e:
            logger.warning(f"⚠️ 记录路由调用统计失败: {e}")

    async def _parse_and_validate_request(self, request: Request, route_config: APIRouteDBModel) -> Dict[str, Any]:
        """解析并验证请求参数"""
        import json
        import re
        from urllib.parse import unquote
        
        parsed_data = {
            "path": {},
            "query": {},
            "header": {},
            "body": {},
            "form": {}
        }
        
        try:
            # 获取参数配置
            parameters_config = route_config.parameters_config or []
            
            # 解析路径参数（优先使用框架提供的 path_params 和 endpoint 模板）
            path_params = getattr(request, "path_params", {}) or {}
            if path_params:
                parsed_data["path"].update(path_params)

            endpoint_template = getattr(route_config, "endpoint", None)
            if endpoint_template and "{" in endpoint_template:
                pattern = re.sub(r"{([^}]+)}", r"(?P<\1>[^/]+)", endpoint_template)
                match = re.match(f"^{pattern}$", request.url.path)
                if match:
                    parsed_data["path"].update({k: unquote(v) for k, v in match.groupdict().items()})

            # 兜底：若未解析到路径参数，则按旧逻辑取最后一段
            path_parts = request.url.path.split("/")
            for param in parameters_config:
                if param.get("location") == "path":
                    param_name = param.get("name")
                    if param_name and param_name not in parsed_data["path"] and len(path_parts) > 0:
                        parsed_data["path"][param_name] = path_parts[-1]
            
            # 解析查询参数
            for key, value in request.query_params.items():
                parsed_data["query"][key] = unquote(value)
            
            # 解析头部参数
            for param in parameters_config:
                if param.get("location") == "header":
                    param_name = param.get("name")
                    if param_name and param_name in request.headers:
                        parsed_data["header"][param_name] = request.headers[param_name]
            
            # 解析请求体
            content_type = request.headers.get("content-type", "")
            
            if "application/json" in content_type:
                body = await request.body()
                if body:
                    try:
                        parsed_data["body"] = json.loads(body)
                    except json.JSONDecodeError:
                        parsed_data["body"] = {}
            elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
                try:
                    form = await request.form()
                    parsed_data["form"] = {key: value for key, value in form.items() if not hasattr(value, 'file')}
                    # 文件上传会在具体的处理器中处理
                except:
                    pass
            
            # 参数验证
            validation_errors = []
            for param in parameters_config:
                param_name = param.get("name")
                param_location = param.get("location", "body")
                param_required = param.get("required", False)
                param_type = param.get("type", "string")
                
                # 获取参数值
                param_value = None
                if param_location == "path":
                    param_value = parsed_data["path"].get(param_name)
                elif param_location == "query":
                    param_value = parsed_data["query"].get(param_name)
                elif param_location == "header":
                    param_value = parsed_data["header"].get(param_name)
                elif param_location == "body":
                    param_value = parsed_data["body"].get(param_name) if isinstance(parsed_data["body"], dict) else None
                
                # 必填验证
                if param_required and (param_value is None or param_value == ""):
                    validation_errors.append(f"参数 '{param_name}' 为必填项")
                    continue
                
                # 类型验证
                if param_value is not None and param_value != "":
                    try:
                        if param_type == "integer":
                            parsed_data[param_location][param_name] = int(param_value)
                        elif param_type == "number":
                            parsed_data[param_location][param_name] = float(param_value)
                        elif param_type == "boolean":
                            if isinstance(param_value, str):
                                parsed_data[param_location][param_name] = param_value.lower() in ['true', '1', 'yes', 'on']
                            else:
                                parsed_data[param_location][param_name] = bool(param_value)
                        # string 类型不需要转换
                    except ValueError:
                        validation_errors.append(f"参数 '{param_name}' 类型错误，期望 {param_type}")
            
            if validation_errors:
                raise HTTPException(
                    status_code=400, 
                    detail={
                        "message": "参数验证失败",
                        "errors": validation_errors,
                        "received_data": parsed_data
                    }
                )
            
            return parsed_data
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"请求解析失败: {str(e)}")

    async def _format_response(self, result: Dict[str, Any], route_config: APIRouteDBModel, request: Request) -> Dict[str, Any]:
        """根据响应配置格式化响应"""
        try:
            # 获取响应配置
            responses_config = route_config.responses_config or {}
            status_code = str(result.get("code", 200))
            
            # 查找匹配的响应配置
            response_config = responses_config.get(status_code)
            if not response_config and status_code != "200":
                # 如果没找到具体状态码配置，尝试使用200的配置
                response_config = responses_config.get("200")
            
            if not response_config:
                # 如果没有响应配置，使用默认格式
                return result
            
            # 获取响应架构
            response_schema = response_config.get("schema", {})
            
            # 根据架构调整响应格式
            if response_schema and isinstance(response_schema, dict):
                formatted_result = self._apply_response_schema(result, response_schema)
                
                # 添加额外的元数据
                if "properties" in response_schema:
                    schema_properties = response_schema["properties"]
                    
                    # 添加时间戳
                    if "timestamp" in schema_properties and "timestamp" not in formatted_result:
                        formatted_result["timestamp"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                    
                    # 添加请求ID（用于调试）
                    if "request_id" in schema_properties and "request_id" not in formatted_result:
                        import uuid
                        formatted_result["request_id"] = str(uuid.uuid4())
                    
                    # 添加API信息
                    if "api_info" in schema_properties and "api_info" not in formatted_result:
                        formatted_result["api_info"] = {
                            "api_id": route_config.api_id,
                            "version": "1.0",
                            "handler_type": route_config.handler_type.value if hasattr(route_config.handler_type, 'value') else str(route_config.handler_type)
                        }
                
                return formatted_result
            
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ 响应格式化失败: {e}")
            return result

    def _apply_response_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """应用响应架构"""
        try:
            if schema.get("type") != "object":
                return data
            
            properties = schema.get("properties", {})
            if not properties:
                return data
            
            formatted_data = {}
            
            # 处理每个定义的属性
            for prop_name, prop_schema in properties.items():
                if prop_name in data:
                    formatted_data[prop_name] = self._format_property_value(data[prop_name], prop_schema)
                elif "default" in prop_schema:
                    formatted_data[prop_name] = prop_schema["default"]
                # 对于必填但缺失的字段，可以添加警告日志
            
            # 保留原数据中未定义但存在的字段（除非schema指定了additionalProperties: false）
            if schema.get("additionalProperties", True):
                for key, value in data.items():
                    if key not in formatted_data:
                        formatted_data[key] = value
            
            return formatted_data
            
        except Exception as e:
            logger.warning(f"⚠️ 应用响应架构失败: {e}")
            return data

    def _format_property_value(self, value: Any, prop_schema: Dict[str, Any]) -> Any:
        """格式化属性值"""
        try:
            prop_type = prop_schema.get("type")
            
            if prop_type == "string":
                return str(value) if value is not None else ""
            elif prop_type == "integer":
                return int(value) if value is not None else 0
            elif prop_type == "number":
                return float(value) if value is not None else 0.0
            elif prop_type == "boolean":
                return bool(value) if value is not None else False
            elif prop_type == "array":
                if isinstance(value, list):
                    items_schema = prop_schema.get("items", {})
                    return [self._format_property_value(item, items_schema) for item in value]
                else:
                    return [value] if value is not None else []
            elif prop_type == "object":
                if isinstance(value, dict):
                    return self._apply_response_schema(value, prop_schema)
                else:
                    return {}
            
            return value
            
        except Exception as e:
            logger.warning(f"⚠️ 格式化属性值失败: {e}")
            return value

    def add_dynamic_route(self, route_config: Dict[str, Any], silent: bool = False) -> bool:
        """
        动态添加路由到FastAPI应用
        
        Args:
            route_config: 路由配置
            silent: 是否静默模式（不输出成功日志）
        """
        try:
            route_id = route_config["id"]
            endpoint = route_config["endpoint"]
            method = route_config["method"].upper()
            
            # 检查路由是否已存在
            route_key = f"{method}:{endpoint}"
            if route_key in self.dynamic_routes:
                logger.debug(f"动态路由已存在: {method} {endpoint}")
                return True
            
            # 创建路由处理函数
            async def route_handler(request: Request):
                return await self.dynamic_route_handler(route_id, request)
            
            # 使用FastAPI的add_api_route方法动态添加路由
            self.app.add_api_route(
                path=endpoint,
                endpoint=route_handler,
                methods=[method],
                include_in_schema=True,
                name=f"dynamic_route_{route_id}"
            )
            self._register_versioned_alias_if_needed(
                route_id,
                endpoint,
                method,
                route_handler,
                auth_required=route_config.get("auth_required", True),
                permission_config=route_config.get("permission_config"),
            )
            
            # 记录动态路由
            self.dynamic_routes[route_key] = {
                "route_id": route_id,
                "endpoint": endpoint,
                "method": method,
                "auth_required": route_config.get("auth_required", True),
                "permission_config": route_config.get("permission_config"),
                "handler": route_handler
            }
            
            # 只在非静默模式下输出日志
            if not silent:
                logger.info(f"✅ 动态路由注册成功: {method} {endpoint}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 添加动态路由失败 {route_config.get('method', '')} {route_config.get('endpoint', '')}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def remove_dynamic_route(self, route_config: Dict[str, Any]) -> bool:
        """从FastAPI应用中移除动态路由"""
        try:
            endpoint = route_config.get("endpoint")
            method = route_config.get("method", "").upper()
            
            route_key = f"{method}:{endpoint}"
            
            if route_key in self.dynamic_routes:
                # 从路由表中移除
                routes_to_remove = []
                for route in self.app.routes:
                    if hasattr(route, 'path') and hasattr(route, 'methods'):
                        if route.path == endpoint and method in route.methods:
                            routes_to_remove.append(route)
                
                for route in routes_to_remove:
                    self.app.routes.remove(route)
                
                # 从记录中移除
                del self.dynamic_routes[route_key]
                logger.info(f"✅ 动态路由移除成功: {method} {endpoint}")
                # 同步移除可能存在的版本别名
                alias = self._build_versioned_alias(endpoint)
                if alias:
                    alias_key = f"{method}:{alias}"
                    routes_to_remove = []
                    for route in self.app.routes:
                        if hasattr(route, 'path') and hasattr(route, 'methods'):
                            if route.path == alias and method in route.methods:
                                routes_to_remove.append(route)
                    for route in routes_to_remove:
                        self.app.routes.remove(route)
                    if alias_key in self.dynamic_routes:
                        del self.dynamic_routes[alias_key]
                        logger.info(f"✅ 动态路由别名移除成功: {method} {alias}")
                return True
            else:
                logger.debug(f"⚠️ 动态路由不存在: {method} {endpoint}")
                return False
            
        except Exception as e:
            logger.error(f"❌ 移除动态路由失败: {e}")
            return False
    
    def get_dynamic_routes(self) -> List[Dict[str, Any]]:
        """获取所有动态路由"""
        return [
            {
                "route_key": key,
                "route_id": info["route_id"],
                "endpoint": info["endpoint"],
                "method": info["method"]
            }
            for key, info in self.dynamic_routes.items()
        ]

    def _build_versioned_alias(self, endpoint: str) -> Optional[str]:
        """构建 /api 与 /api/v1 之间的别名路径"""
        if endpoint.startswith("/api/v1/"):
            return "/api" + endpoint[len("/api/v1"):]
        if endpoint.startswith("/api/") and not endpoint.startswith("/api/v1/"):
            return "/api/v1" + endpoint[len("/api"):]
        return None

    def _register_versioned_alias_if_needed(
        self,
        route_id: str,
        endpoint: str,
        method: str,
        handler: Callable,
        auth_required: bool = True,
        permission_config: Optional[dict] = None
    ) -> None:
        """为动态路由注册版本别名，避免 /api 与 /api/v1 不一致导致 404"""
        alias = self._build_versioned_alias(endpoint)
        if not alias or alias == endpoint:
            return
        alias_key = f"{method}:{alias}"
        if alias_key in self.dynamic_routes:
            return
        self.app.add_api_route(
            path=alias,
            endpoint=handler,
            methods=[method],
            include_in_schema=False,
            name=f"dynamic_route_alias_{route_id}"
        )
        self.dynamic_routes[alias_key] = {
            "route_id": route_id,
            "endpoint": alias,
            "method": method,
            "auth_required": auth_required,
            "permission_config": permission_config,
            "handler": handler,
            "alias_of": endpoint
        }

    def _load_active_routes_from_database(self) -> None:
        """从数据库加载已激活路由并注册到应用（用于服务启动时）"""
        with get_db_session() as db:
            active_routes = db.query(APIRouteDBModel).filter(
                APIRouteDBModel.status == RouteStatus.ACTIVE
            ).all()
            
            if not active_routes:
                return
            
            success_count = 0
            failed_routes = []
            
            for r in active_routes:
                try:
                    # 使用静默模式注册路由
                    if self.add_dynamic_route({
                        "id": r.id,
                        "endpoint": r.endpoint,
                        "method": r.method,
                        "auth_required": r.auth_required,
                        "permission_config": r.permission_config,
                        "handler_config": r.handler_config or {},
                    }, silent=True):
                        success_count += 1
                    else:
                        failed_routes.append(f"{r.method} {r.endpoint}")
                except Exception as e:
                    failed_routes.append(f"{r.method} {r.endpoint}")
                    logger.warning(f"⚠️ 启动加载动态路由失败: {r.method} {r.endpoint}, 错误: {e}")
            
            # 输出汇总日志
            if success_count > 0:
                logger.info(f"✅ 动态路由注册成功: {success_count} 个路由")
            
            if failed_routes:
                logger.warning(f"⚠️ {len(failed_routes)} 个路由注册失败: {', '.join(failed_routes[:5])}" + 
                             (f" 等" if len(failed_routes) > 5 else ""))

    # ====== 增强的实体CRUD处理方法 ======
    
    async def _handle_entity_list(
        self,
        entity: str,
        entity_model,
        field_definitions: Dict,
        request: Request,
        db,
        enable_search: bool = False,
        handler_config: Optional[Dict[str, Any]] = None,
        request_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """处理实体列表查询

        Args:
            entity: 实体名称
            entity_model: 实体模型
            field_definitions: 字段定义
            request: 请求对象
            db: 数据库会话
            enable_search: 是否开启搜索（search 参数）
        """
        from sqlalchemy import text

        try:
            # 实体表名（entity_{name}）
            table_name = self._build_entity_table_name(entity)
            table_name_sql = self._quote_identifier(table_name)

            # 分页参数
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 20))
            search = request.query_params.get("search", "")
            sort_field = request.query_params.get("sort", "created_at")
            sort_order = request.query_params.get("order", "desc")
            sort_order = "desc" if str(sort_order).lower() != "asc" else "asc"

            # 分页偏移
            offset = (page - 1) * limit

            # 查询条件
            where_conditions = []
            where_params: Dict[str, Any] = {}
            valid_fields = {
                name for name in field_definitions.keys()
                if self._sql_identifier_pattern.match(name)
            }

            def _coerce_field_value(field_name: str, value: Any) -> Any:
                if value is None:
                    return None
                field_def = field_definitions.get(field_name)
                if not field_def:
                    return value
                try:
                    if field_def.type == 'integer':
                        return int(value)
                    if field_def.type == 'number':
                        return float(value)
                except Exception:
                    return value
                return value

            def _resolve_template_value(value: Any) -> Any:
                if not isinstance(value, str):
                    return value
                match = re.match(r"^\$\{([^}]+)\}$", value.strip())
                if not match:
                    return value
                var_name = match.group(1)
                data = request_data or {}
                for scope in ("path", "query", "body"):
                    scoped = data.get(scope, {}) if isinstance(data, dict) else {}
                    if isinstance(scoped, dict) and var_name in scoped:
                        return scoped.get(var_name)
                return value

            path_params = {}
            if isinstance(request_data, dict):
                path_params = request_data.get("path") or {}
            if not path_params:
                path_params = getattr(request, "path_params", {}) or {}

            query_params = {}
            if isinstance(request_data, dict):
                query_params = request_data.get("query") or {}
            if not query_params:
                query_params = dict(request.query_params)

            if search and enable_search:
                # 搜索条件（文本字段）
                text_fields = [
                    f.name for f in field_definitions.values()
                    if f.type in ['text', 'email', 'phone'] and f.name in valid_fields
                ]
                if text_fields:
                    safe_search = str(search).replace(" ", "")
                    search_condition = []
                    for idx, field in enumerate(text_fields):
                        param_key = f"search_{idx}"
                        search_condition.append(
                            f"REPLACE(LOWER({self._quote_identifier(field)}), ' ', '') LIKE LOWER(:{param_key})"
                        )
                        where_params[param_key] = f"%{safe_search}%"
                    where_conditions.append(f"({' OR '.join(search_condition)})")

            # ?? handler_config.filter_conditions
            if isinstance(handler_config, dict):
                filter_conditions = handler_config.get("filter_conditions") or {}
                if isinstance(filter_conditions, dict):
                    for key, value in filter_conditions.items():
                        if key in valid_fields:
                            resolved_value = _resolve_template_value(value)
                            resolved_value = _coerce_field_value(key, resolved_value)
                            if resolved_value is not None and resolved_value != "":
                                param_key = f"fc_{key}"
                                where_conditions.append(f"{self._quote_identifier(key)} = :{param_key}")
                                where_params[param_key] = resolved_value

            # path 参数过滤
            if isinstance(path_params, dict):
                for key, value in path_params.items():
                    if key in valid_fields:
                        resolved_value = _coerce_field_value(key, value)
                        if resolved_value is not None and resolved_value != "":
                            param_key = f"path_{key}"
                            if param_key not in where_params:
                                where_conditions.append(f"{self._quote_identifier(key)} = :{param_key}")
                                where_params[param_key] = resolved_value

            # query 参数过滤（排除分页/排序字段）
            reserved_keys = {"page", "limit", "search", "sort", "order"}
            operation = handler_config.get("operation") if isinstance(handler_config, dict) else None
            searchable_fields = []
            if isinstance(handler_config, dict):
                searchable_fields = handler_config.get("searchable_fields") or []
            enable_fuzzy = (operation == "search")

            if isinstance(query_params, dict):
                for key, value in query_params.items():
                    if key in reserved_keys or key not in valid_fields:
                        continue
                    resolved_value = _coerce_field_value(key, value)
                    if resolved_value is None or resolved_value == "":
                        continue
                    param_key = f"qp_{key}"
                    if param_key in where_params:
                        continue
                    if enable_fuzzy and key in searchable_fields and isinstance(resolved_value, str):
                        # Fuzzy match: ignore spaces, case-insensitive
                        cleaned = resolved_value.replace(" ", "")
                        where_conditions.append(
                            f"REPLACE(LOWER({self._quote_identifier(key)}), ' ', '') LIKE LOWER(:{param_key})"
                        )
                        where_params[param_key] = f"%{cleaned}%"
                    else:
                        where_conditions.append(f"{self._quote_identifier(key)} = :{param_key}")
                        where_params[param_key] = resolved_value

            where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

            # 排序
            sortable_fields = set(valid_fields)
            if isinstance(handler_config, dict):
                configured_sort_fields = handler_config.get("sortable_fields") or []
                if isinstance(configured_sort_fields, list) and configured_sort_fields:
                    sortable_fields = {
                        f for f in configured_sort_fields
                        if isinstance(f, str) and f in valid_fields
                    } or sortable_fields
            if "created_at" in valid_fields:
                sortable_fields.add("created_at")
            if "updated_at" in valid_fields:
                sortable_fields.add("updated_at")
            if "id" in valid_fields:
                sortable_fields.add("id")
            safe_sort_field = sort_field if sort_field in sortable_fields else "created_at"
            if safe_sort_field not in valid_fields and valid_fields:
                safe_sort_field = next(iter(valid_fields))
            order_clause = (
                f"ORDER BY {self._quote_identifier(safe_sort_field)} "
                f"{'DESC' if sort_order == 'desc' else 'ASC'}"
            )

            # 检查表是否存在（MySQL）
            check_table_query = text("""
                SELECT TABLE_NAME FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table_name
            """)
            table_exists = db.execute(check_table_query, {"table_name": table_name}).fetchone()

            if not table_exists:
                # 表不存在时直接返回空结果
                return {
                    "code": 404,
                    "message": f"实体表不存在，无法查询 '{entity}'",
                    "data": {
                        "items": [],
                        "total": 0,
                        "page": page,
                        "limit": limit,
                        "has_next": False,
                        "has_prev": page > 1,
                        "table_missing": True,
                        "entity_name": entity,
                        "expected_table": table_name
                    }
                }

            # 统计总数
            count_query = text(f"SELECT COUNT(*) as count FROM {table_name_sql} {where_clause}")
            total_result = db.execute(count_query, where_params).fetchone()
            total = total_result[0] if total_result else 0

            # 查询数据
            data_query = text(f"""
                SELECT * FROM {table_name_sql} 
                {where_clause} 
                {order_clause} 
                LIMIT {limit} OFFSET {offset}
            """)

            rows = db.execute(data_query, where_params).fetchall()

            # 构建返回项
            items = []
            for row in rows:
                item = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)

                # datetime/Decimal 格式化
                for key, value in item.items():
                    if isinstance(value, datetime):
                        item[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                    elif isinstance(value, date):
                        item[key] = value.strftime('%Y-%m-%d')
                    elif isinstance(value, Decimal):
                        item[key] = float(value)

                # 字段类型再处理
                for field_name, field_def in field_definitions.items():
                    if field_name in item and item[field_name]:
                        if field_def.type == 'json' and isinstance(item[field_name], str):
                            try:
                                item[field_name] = json.loads(item[field_name])
                            except Exception:
                                pass
                        elif field_def.type == 'number':
                            try:
                                item[field_name] = float(item[field_name])
                            except Exception:
                                pass
                        elif field_def.type in ['date', 'datetime'] and isinstance(item[field_name], str):
                            # date/datetime 已是字符串时无需处理
                            pass

                items.append(item)

            return {
                "code": 200,
                "message": f"查询{entity_model.display_name}成功",
                "data": {
                    "items": items,
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "has_next": (page * limit) < total,
                    "has_prev": page > 1
                }
            }

        except Exception as e:
            logger.error(f"实体列表查询失败: {e}")
            return {
                "code": 500,
                "message": f"查询{entity}失败: {str(e)}",
                "data": None
            }
    async def _handle_entity_create(self, entity: str, entity_model, field_definitions: Dict, request: Request, db, api_id: str) -> Dict[str, Any]:
        """处理实体创建"""
        from sqlalchemy import text
        import json
        import uuid
        import time
        
        try:
            # 获取请求数据
            if request.method == "POST":
                try:
                    if hasattr(request, '_json'):
                        data = request._json
                    else:
                        body = await request.body()
                        data = json.loads(body) if body else {}
                except:
                    data = {}
            else:
                data = dict(request.query_params)
            
            # 构建实体表名（使用实体服务创建的表）
            table_name = self._build_entity_table_name(entity)
            table_name_sql = self._quote_identifier(table_name)
            
            # 检查表是否存在（不自动创建，依赖实体建模）
            check_table_query = text("""
                SELECT TABLE_NAME FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table_name
            """)
            table_exists = db.execute(check_table_query, {"table_name": table_name}).fetchone()
            
            if not table_exists:
                return {
                    "code": 404,
                    "message": f"实体表不存在，请先在实体建模中创建 '{entity}' 实体",
                    "data": {
                        "table_missing": True,
                        "entity_name": entity,
                        "expected_table": table_name
                    }
                }
            
            # 数据验证和转换
            processed_data = {}
            errors = []
            
            # 添加系统字段
            processed_data['id'] = str(uuid.uuid4())
            processed_data['created_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            processed_data['updated_at'] = processed_data['created_at']
            
            # 处理业务字段
            for field_name, field_def in field_definitions.items():
                value = data.get(field_name)
                
                # 必填字段验证
                if field_def.required and (value is None or value == ""):
                    errors.append(f"字段 '{field_def.display_name}' 为必填项")
                    continue
                
                # 数据类型转换和验证
                if value is not None:
                    try:
                        if field_def.type == 'number':
                            processed_data[field_name] = float(value)
                        elif field_def.type == 'integer':
                            processed_data[field_name] = int(value)
                        elif field_def.type == 'json':
                            if isinstance(value, (dict, list)):
                                processed_data[field_name] = json.dumps(value)
                            else:
                                processed_data[field_name] = str(value)
                        elif field_def.type == 'select' and field_def.options:
                            if str(value) not in field_def.options:
                                errors.append(f"字段 '{field_def.display_name}' 值不在允许范围内")
                            else:
                                processed_data[field_name] = str(value)
                        else:
                            processed_data[field_name] = str(value)
                    except Exception as e:
                        errors.append(f"字段 '{field_def.display_name}' 数据格式错误: {str(e)}")
                else:
                    processed_data[field_name] = None
            
            if errors:
                return {
                    "code": 400,
                    "message": "数据验证失败",
                    "data": {
                        "errors": errors,
                        "input_data": data
                    }
                }
            
            # 构建插入语句
            safe_columns: List[str] = []
            value_placeholders: List[str] = []
            sql_params: Dict[str, Any] = {}
            for idx, (col, val) in enumerate(processed_data.items()):
                safe_col = self._sanitize_sql_identifier(col)
                safe_columns.append(self._quote_identifier(safe_col))
                param_key = f"v_{idx}"
                value_placeholders.append(f":{param_key}")
                sql_params[param_key] = val

            insert_query = text(f"""
                INSERT INTO {table_name_sql} ({', '.join(safe_columns)}) 
                VALUES ({', '.join(value_placeholders)})
            """)
            
            # 执行插入
            db.execute(insert_query, sql_params)
            db.commit()
            
            return {
                "code": 201,
                "message": f"创建{entity_model.display_name}成功",
                "data": {
                    "id": processed_data['id'],
                    "entity": entity,
                    "created_at": processed_data['created_at'],
                    **{k: v for k, v in processed_data.items() if k not in ['created_at', 'updated_at']}
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 创建失败: {e}")
            return {
                "code": 500,
                "message": f"创建{entity}失败: {str(e)}",
                "data": None
            }

    async def _handle_entity_get(self, entity: str, entity_model, field_definitions: Dict, request: Request, db, handler_config: Dict = None) -> Dict[str, Any]:
        """Handle single entity query."""
        from sqlalchemy import text
        import json

        try:
            # Parse entity ID from path/query params
            path_params = getattr(request, "path_params", {}) or {}
            query_params = dict(request.query_params) if hasattr(request, "query_params") else {}
            entity_id = None
            param_name_used = None

            query_field = None
            query_param = None
            query_location = None
            if handler_config:
                query_field = handler_config.get("query_field") or handler_config.get("queryField")
                query_param = handler_config.get("query_param") or handler_config.get("queryParam")
                query_location = handler_config.get("query_location") or handler_config.get("queryLocation")

            candidate_params = []
            if query_param:
                candidate_params.append(query_param)
            candidate_params.extend([f"{entity}_id", f"{entity}_number", "id", "entity_id", "number"])
            if query_field and query_field not in candidate_params:
                candidate_params.append(query_field)

            def _find_in_container(container):
                nonlocal entity_id, param_name_used
                for name in candidate_params:
                    if name in container:
                        value = container.get(name)
                        if value is None or value == "":
                            continue
                        entity_id = value
                        param_name_used = name
                        return True
                return False

            if query_location == "path":
                _find_in_container(path_params)
            elif query_location == "query":
                _find_in_container(query_params)
            elif query_location == "body":
                # GET typically does not use body
                pass
            else:
                if not _find_in_container(path_params):
                    _find_in_container(query_params)

            # Fallback: take tail of URL path
            if not entity_id:
                path_parts = request.url.path.split("/")
                entity_id = path_parts[-1] if path_parts else None
                if entity_id:
                    param_name_used = param_name_used or "path_tail"

            logger.debug(
                f"[EntityGet] entity={entity}, entity_id={entity_id}, param_name={param_name_used}, "
                f"path_params={path_params}, query_params={query_params}, url_path={request.url.path}"
            )

            if not entity_id:
                return {
                    "code": 400,
                    "message": "Missing entity ID",
                    "data": {
                        "hint": "Provide entity ID in path or query parameters",
                        "candidates": candidate_params
                    }
                }

            # Resolve query field
            if not query_field:
                if param_name_used and param_name_used in field_definitions:
                    query_field = param_name_used
                elif param_name_used and param_name_used.endswith("_id"):
                    entity_number_field = f"{entity}_number"
                    param_number_field = f"{param_name_used[:-3]}_number"
                    if entity_number_field in field_definitions:
                        query_field = entity_number_field
                    elif param_number_field in field_definitions:
                        query_field = param_number_field
                    elif "id" in field_definitions:
                        query_field = "id"
                elif "id" in field_definitions:
                    query_field = "id"
                elif f"{entity}_number" in field_definitions:
                    query_field = f"{entity}_number"
                else:
                    query_field = param_name_used or "id"

            if query_field not in field_definitions:
                if param_name_used and param_name_used.endswith("_id"):
                    entity_number_field = f"{entity}_number"
                    param_number_field = f"{param_name_used[:-3]}_number"
                    if entity_number_field in field_definitions:
                        query_field = entity_number_field
                    elif param_number_field in field_definitions:
                        query_field = param_number_field
                if query_field not in field_definitions and "id" in field_definitions:
                    logger.warning(
                        f"[EntityGet] query_field '{query_field}' not in field definitions, fallback to id"
                    )
                    query_field = "id"
                if query_field not in field_definitions:
                    return {
                        "code": 400,
                        "message": f"Query field '{query_field}' not found",
                        "data": {
                            "available_fields": list(field_definitions.keys())
                        }
                    }

            table_name = self._build_entity_table_name(entity)
            table_name_sql = self._quote_identifier(table_name)

            logger.debug(
                f"[EntityGet] Query table: {table_name}, field: {query_field}, value: {entity_id}"
            )

            # Check table exists
            check_table_query = text("""
                SELECT TABLE_NAME FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table_name
            """)
            table_exists = db.execute(check_table_query, {"table_name": table_name}).fetchone()

            if not table_exists:
                return {
                    "code": 404,
                    "message": f"{entity_model.display_name} not found",
                    "data": None
                }

            # Query data
            safe_query_field = self._sanitize_sql_identifier(query_field)
            query = text(
                f"SELECT * FROM {table_name_sql} "
                f"WHERE {self._quote_identifier(safe_query_field)} = :entity_id"
            )
            logger.debug(
                f"[EntityGet] Execute SQL: SELECT * FROM {table_name} WHERE {safe_query_field} = '{entity_id}'"
            )
            result = db.execute(query, {"entity_id": entity_id}).fetchone()

            if not result:
                return {
                    "code": 404,
                    "message": f"{entity_model.display_name} not found",
                    "data": None
                }

            # Convert result
            item = dict(result._mapping) if hasattr(result, '_mapping') else dict(result)

            # Normalize datetime/decimal types
            for key, value in item.items():
                if isinstance(value, datetime):
                    item[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, date):
                    item[key] = value.strftime('%Y-%m-%d')
                elif isinstance(value, Decimal):
                    item[key] = float(value)

            # Convert typed fields
            for field_name, field_def in field_definitions.items():
                if field_name in item and item[field_name]:
                    if field_def.type == 'json' and isinstance(item[field_name], str):
                        try:
                            item[field_name] = json.loads(item[field_name])
                        except:
                            pass
                    elif field_def.type == 'number':
                        try:
                            item[field_name] = float(item[field_name])
                        except:
                            pass

            return {
                "code": 200,
                "message": f"Get {entity_model.display_name} success",
                "data": item
            }

        except Exception as e:
            logger.error(f"EntityGet failed: {e}")
            return {
                "code": 500,
                "message": f"Get {entity} failed: {str(e)}",
                "data": None
            }

    def _resolve_entity_identifier(
        self,
        entity: str,
        field_definitions: Dict[str, Any],
        request: Request,
        handler_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """统一解析实体标识字段和值，供 get/update/delete 复用。"""
        path_params = getattr(request, "path_params", {}) or {}
        query_params = dict(request.query_params) if hasattr(request, "query_params") else {}
        entity_id = None
        param_name_used = None

        query_field = None
        query_param = None
        query_location = None
        if handler_config:
            query_field = handler_config.get("query_field") or handler_config.get("queryField")
            query_param = handler_config.get("query_param") or handler_config.get("queryParam")
            query_location = handler_config.get("query_location") or handler_config.get("queryLocation")

        candidate_params = []
        if query_param:
            candidate_params.append(query_param)
        candidate_params.extend([f"{entity}_id", f"{entity}_number", "id", "entity_id", "number"])
        if query_field and query_field not in candidate_params:
            candidate_params.append(query_field)

        def _find_in_container(container):
            nonlocal entity_id, param_name_used
            for name in candidate_params:
                if name in container:
                    value = container.get(name)
                    if value is None or value == "":
                        continue
                    entity_id = value
                    param_name_used = name
                    return True
            return False

        if query_location == "path":
            _find_in_container(path_params)
        elif query_location == "query":
            _find_in_container(query_params)
        elif query_location == "body":
            pass
        else:
            if not _find_in_container(path_params):
                _find_in_container(query_params)

        if not entity_id:
            path_parts = request.url.path.split("/")
            entity_id = path_parts[-1] if path_parts else None
            if entity_id:
                param_name_used = param_name_used or "path_tail"

        if not entity_id:
            return {
                "ok": False,
                "error": {
                    "code": 400,
                    "message": "缺少实体标识",
                    "data": {
                        "hint": "请在 path 或 query 中传入实体标识",
                        "candidates": candidate_params,
                    },
                },
            }

        if not query_field:
            if param_name_used and param_name_used in field_definitions:
                query_field = param_name_used
            elif param_name_used and param_name_used.endswith("_id"):
                entity_number_field = f"{entity}_number"
                param_number_field = f"{param_name_used[:-3]}_number"
                if entity_number_field in field_definitions:
                    query_field = entity_number_field
                elif param_number_field in field_definitions:
                    query_field = param_number_field
                elif "id" in field_definitions:
                    query_field = "id"
            elif "id" in field_definitions:
                query_field = "id"
            elif f"{entity}_number" in field_definitions:
                query_field = f"{entity}_number"
            else:
                query_field = param_name_used or "id"

        if query_field not in field_definitions:
            if param_name_used and param_name_used.endswith("_id"):
                entity_number_field = f"{entity}_number"
                param_number_field = f"{param_name_used[:-3]}_number"
                if entity_number_field in field_definitions:
                    query_field = entity_number_field
                elif param_number_field in field_definitions:
                    query_field = param_number_field
            if query_field not in field_definitions and "id" in field_definitions:
                logger.warning(
                    f"[EntityLookup] query_field '{query_field}' 不存在，回退到 id"
                )
                query_field = "id"
            if query_field not in field_definitions:
                return {
                    "ok": False,
                    "error": {
                        "code": 400,
                        "message": f"查询字段 '{query_field}' 不存在",
                        "data": {"available_fields": list(field_definitions.keys())},
                    },
                }

        return {
            "ok": True,
            "entity_id": entity_id,
            "query_field": query_field,
            "param_name_used": param_name_used,
            "path_params": path_params,
            "query_params": query_params,
        }

    async def _handle_entity_update(
        self,
        entity: str,
        entity_model,
        field_definitions: Dict,
        request: Request,
        db,
        api_id: str,
        handler_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """处理实体更新"""
        from sqlalchemy import text
        import json
        import time
        
        try:
            lookup = self._resolve_entity_identifier(
                entity=entity,
                field_definitions=field_definitions,
                request=request,
                handler_config=handler_config,
            )
            if not lookup.get("ok"):
                return lookup["error"]

            entity_id = lookup["entity_id"]
            query_field = lookup["query_field"]
            
            # 获取更新数据
            try:
                if hasattr(request, '_json'):
                    data = request._json
                else:
                    body = await request.body()
                    data = json.loads(body) if body else {}
            except:
                data = {}
            
            table_name = self._build_entity_table_name(entity)
            table_name_sql = self._quote_identifier(table_name)
            safe_query_field = self._sanitize_sql_identifier(query_field)
            
            # 检查记录是否存在
            check_query = text(
                f"SELECT COUNT(*) as count FROM {table_name_sql} "
                f"WHERE {self._quote_identifier(safe_query_field)} = :entity_id"
            )
            exists = db.execute(check_query, {"entity_id": entity_id}).fetchone()
            
            if not exists or exists[0] == 0:
                return {
                    "code": 404,
                    "message": f"{entity_model.display_name}不存在",
                    "data": None
                }
            
            # 数据验证和转换
            processed_data = {}
            errors = []
            
            # 更新时间
            processed_data['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # 处理业务字段
            for field_name, field_def in field_definitions.items():
                if field_name not in data:
                    continue  # 跳过未提供的字段
                
                value = data[field_name]
                
                # 数据类型转换和验证
                if value is not None:
                    try:
                        if field_def.type == 'number':
                            processed_data[field_name] = float(value)
                        elif field_def.type == 'integer':
                            processed_data[field_name] = int(value)
                        elif field_def.type == 'json':
                            if isinstance(value, (dict, list)):
                                processed_data[field_name] = json.dumps(value)
                            else:
                                processed_data[field_name] = str(value)
                        elif field_def.type == 'select' and field_def.options:
                            if str(value) not in field_def.options:
                                errors.append(f"字段 '{field_def.display_name}' 值不在允许范围内")
                            else:
                                processed_data[field_name] = str(value)
                        else:
                            processed_data[field_name] = str(value)
                    except Exception as e:
                        errors.append(f"字段 '{field_def.display_name}' 数据格式错误: {str(e)}")
                else:
                    processed_data[field_name] = None
            
            if errors:
                return {
                    "code": 400,
                    "message": "数据验证失败",
                    "data": {
                        "errors": errors,
                        "input_data": data
                    }
                }
            
            if not processed_data or processed_data == {'updated_at': processed_data['updated_at']}:
                return {
                    "code": 400,
                    "message": "没有提供需要更新的字段",
                    "data": None
                }
            
            # 构建更新语句
            set_clauses: List[str] = []
            sql_params: Dict[str, Any] = {"entity_id": entity_id}
            for idx, (col, val) in enumerate(processed_data.items()):
                safe_col = self._sanitize_sql_identifier(col)
                param_key = f"u_{idx}"
                set_clauses.append(f"{self._quote_identifier(safe_col)} = :{param_key}")
                sql_params[param_key] = val
            
            update_query = text(f"""
                UPDATE {table_name_sql} 
                SET {', '.join(set_clauses)} 
                WHERE {self._quote_identifier(safe_query_field)} = :entity_id
            """)
            
            # 执行更新
            db.execute(update_query, sql_params)
            db.commit()
            
            return {
                "code": 200,
                "message": f"更新{entity_model.display_name}成功",
                "data": {
                    "id": entity_id,
                    "query_field": query_field,
                    "entity": entity,
                    "updated_at": processed_data['updated_at'],
                    "updated_fields": list(processed_data.keys())
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 更新失败: {e}")
            return {
                "code": 500,
                "message": f"更新{entity}失败: {str(e)}",
                "data": None
            }

    async def _handle_entity_delete(
        self,
        entity: str,
        entity_model,
        field_definitions: Dict,
        request: Request,
        db,
        handler_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """处理实体删除"""
        from sqlalchemy import text
        
        try:
            lookup = self._resolve_entity_identifier(
                entity=entity,
                field_definitions=field_definitions,
                request=request,
                handler_config=handler_config,
            )
            if not lookup.get("ok"):
                return lookup["error"]

            entity_id = lookup["entity_id"]
            query_field = lookup["query_field"]
            
            table_name = self._build_entity_table_name(entity)
            table_name_sql = self._quote_identifier(table_name)
            safe_query_field = self._sanitize_sql_identifier(query_field)
            
            # 检查记录是否存在
            check_query = text(
                f"SELECT COUNT(*) as count FROM {table_name_sql} "
                f"WHERE {self._quote_identifier(safe_query_field)} = :entity_id"
            )
            exists = db.execute(check_query, {"entity_id": entity_id}).fetchone()
            
            if not exists or exists[0] == 0:
                return {
                    "code": 404,
                    "message": f"{entity_model.display_name}不存在",
                    "data": None
                }
            
            # 执行删除
            delete_query = text(
                f"DELETE FROM {table_name_sql} "
                f"WHERE {self._quote_identifier(safe_query_field)} = :entity_id"
            )
            db.execute(delete_query, {"entity_id": entity_id})
            db.commit()
            
            return {
                "code": 200,
                "message": f"删除{entity_model.display_name}成功",
                "data": {
                    "id": entity_id,
                    "query_field": query_field,
                    "entity": entity,
                    "deleted_at": time.strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 删除失败: {e}")
            return {
                "code": 500,
                "message": f"删除{entity}失败: {str(e)}",
                "data": None
            }


        
        


def get_dynamic_router() -> DynamicRouteHandler:
    """获取动态路由管理器实例"""
    if dynamic_router is None:
        raise RuntimeError("动态路由管理器未初始化")
    return dynamic_router


# 全局动态路由管理器实例
dynamic_router: Optional[DynamicRouteHandler] = None


def init_dynamic_router(app: FastAPI):
    """初始化动态路由管理器"""
    global dynamic_router
    dynamic_router = DynamicRouteHandler(app)
    return dynamic_router
