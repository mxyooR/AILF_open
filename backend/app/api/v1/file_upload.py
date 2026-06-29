"""
文件上传API路由
支持图片上传和静态文件服务
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import os
import uuid
import time
from pathlib import Path
import mimetypes
from PIL import Image
import io

from app.core.auth import verify_developer_token
from app.core.response import UnifiedResponse

router = APIRouter(prefix="/files", tags=["文件管理"])

# 配置文件上传目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 创建子目录
IMAGES_DIR = UPLOAD_DIR / "images"
DOCUMENTS_DIR = UPLOAD_DIR / "documents"
TEMP_DIR = UPLOAD_DIR / "temp"

for dir_path in [IMAGES_DIR, DOCUMENTS_DIR, TEMP_DIR]:
    dir_path.mkdir(exist_ok=True)

# 支持的文件类型
ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp", "image/bmp"
}
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf", "application/msword", 
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain", "text/csv"
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = "general",
    _: dict = Depends(verify_developer_token)
):
    """
    上传文件接口
    
    - **file**: 上传的文件
    - **category**: 文件分类 (images, documents, general)
    
    返回上传后的文件信息
    """
    try:
        # 检查文件大小
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise UnifiedResponse.payload_too_large(
                message="文件大小超过限制（10MB）",
                error_type="file_too_large",
                suggestion="请上传小于10MB的文件"
            )
        
        # 检查文件类型
        content_type = file.content_type or mimetypes.guess_type(file.filename)[0]
        
        # 根据类型选择存储目录
        if category == "images" and content_type in ALLOWED_IMAGE_TYPES:
            save_dir = IMAGES_DIR
        elif category == "documents" and content_type in ALLOWED_DOCUMENT_TYPES:
            save_dir = DOCUMENTS_DIR
        else:
            save_dir = UPLOAD_DIR
        
        # 生成唯一文件名
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4().hex}_{int(time.time())}{file_extension}"
        file_path = save_dir / unique_filename
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 如果是图片，获取图片信息
        file_info = {
            "file_id": unique_filename.split('.')[0],
            "original_name": file.filename,
            "filename": unique_filename,
            "file_path": str(file_path.relative_to(UPLOAD_DIR)),
            "content_type": content_type,
            "size": len(file_content),
            "category": category,
            "upload_time": int(time.time()),
            "url": f"/api/v1/files/serve/{unique_filename}"
        }
        
        if category == "images" and content_type in ALLOWED_IMAGE_TYPES:
            try:
                with Image.open(file_path) as img:
                    file_info.update({
                        "width": img.width,
                        "height": img.height,
                        "format": img.format
                    })
            except Exception as e:
                print(f"无法获取图片信息: {e}")
        
        return UnifiedResponse.success(
            message="文件上传成功",
            data=file_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"文件上传错误: {e}")
        raise UnifiedResponse.internal_error(
            message="文件上传失败",
            error_type="upload_failed",
            details=str(e)
        )


@router.get("/serve/{filename}")
async def serve_file(filename: str, download: bool = False):
    """
    提供文件服务接口
    
    - **filename**: 文件名
    
    返回文件内容
    """
    try:
        # 在各个目录中查找文件
        for directory in [IMAGES_DIR, DOCUMENTS_DIR, UPLOAD_DIR]:
            file_path = directory / filename
            if file_path.exists():
                media_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
                return FileResponse(
                    path=str(file_path),
                    filename=filename,
                    media_type=media_type,
                    content_disposition_type="attachment" if download else "inline"
                )
        
        raise UnifiedResponse.not_found(
            message="文件不存在",
            error_type="file_not_found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"文件服务错误: {e}")
        raise UnifiedResponse.internal_error(
            message="文件服务失败",
            error_type="serve_failed",
            details=str(e)
        )


@router.get("/images/{image_id}")
async def display_image(
    image_id: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    quality: Optional[int] = 85
):
    """
    图片显示接口，支持尺寸调整
    
    - **image_id**: 图片ID或文件名
    - **width**: 目标宽度
    - **height**: 目标高度  
    - **quality**: 图片质量 (1-100)
    
    返回图片文件
    """
    try:
        # 查找图片文件
        image_path = None
        for directory in [IMAGES_DIR, UPLOAD_DIR]:
            # 尝试直接匹配文件名
            potential_path = directory / image_id
            if potential_path.exists():
                image_path = potential_path
                break
            
            # 尝试匹配以image_id开头的文件
            for file_path in directory.glob(f"{image_id}*"):
                if file_path.is_file():
                    image_path = file_path
                    break
            
            if image_path:
                break
        
        if not image_path:
            raise UnifiedResponse.not_found(
                message="图片不存在",
                error_type="image_not_found"
            )
        
        # 如果没有指定尺寸，直接返回原图
        if not width and not height:
            return FileResponse(
                path=str(image_path),
                media_type="image/jpeg"
            )
        
        # 处理图片尺寸调整
        try:
            with Image.open(image_path) as img:
                # 如果指定了尺寸，调整图片大小
                if width or height:
                    original_width, original_height = img.size
                    
                    # 计算新尺寸，保持纵横比
                    if width and height:
                        new_size = (width, height)
                    elif width:
                        ratio = width / original_width
                        new_size = (width, int(original_height * ratio))
                    else:  # height only
                        ratio = height / original_height
                        new_size = (int(original_width * ratio), height)
                    
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # 保存到临时文件
                temp_filename = f"temp_{image_id}_{width or 'auto'}x{height or 'auto'}_{int(time.time())}.jpg"
                temp_path = TEMP_DIR / temp_filename
                
                img.save(temp_path, "JPEG", quality=quality, optimize=True)
                
                return FileResponse(
                    path=str(temp_path),
                    media_type="image/jpeg",
                    filename=temp_filename
                )
                
        except Exception as e:
            print(f"图片处理错误: {e}")
            # 如果处理失败，返回原图
            return FileResponse(
                path=str(image_path),
                media_type="image/jpeg"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"图片显示错误: {e}")
        raise UnifiedResponse.internal_error(
            message="图片显示失败",
            error_type="display_failed",
            details=str(e)
        )


@router.get("/list")
async def list_files(
    category: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    _: dict = Depends(verify_developer_token)
):
    """
    获取文件列表
    
    - **category**: 文件分类筛选
    - **page**: 页码
    - **limit**: 每页数量
    
    返回文件列表
    """
    try:
        files = []
        
        # 根据分类选择目录
        if category == "images":
            directories = [IMAGES_DIR]
        elif category == "documents":
            directories = [DOCUMENTS_DIR]
        else:
            directories = [IMAGES_DIR, DOCUMENTS_DIR, UPLOAD_DIR]
        
        for directory in directories:
            if directory.exists():
                for file_path in directory.iterdir():
                    if file_path.is_file():
                        stat = file_path.stat()
                        file_info = {
                            "filename": file_path.name,
                            "file_path": str(file_path.relative_to(UPLOAD_DIR)),
                            "size": stat.st_size,
                            "created_time": int(stat.st_ctime),
                            "modified_time": int(stat.st_mtime),
                            "category": directory.name if directory.name in ["images", "documents"] else "general",
                            "url": f"/api/v1/files/serve/{file_path.name}"
                        }
                        
                        # 添加内容类型
                        content_type = mimetypes.guess_type(file_path.name)[0]
                        if content_type:
                            file_info["content_type"] = content_type
                        
                        files.append(file_info)
        
        # 排序和分页
        files.sort(key=lambda x: x["created_time"], reverse=True)
        
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        page_files = files[start_idx:end_idx]
        
        return UnifiedResponse.success(
            message="获取文件列表成功",
            data={
                "files": page_files,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": len(files),
                    "total_pages": (len(files) + limit - 1) // limit
                }
            }
        )
        
    except Exception as e:
        print(f"获取文件列表错误: {e}")
        raise UnifiedResponse.internal_error(
            message="获取文件列表失败",
            error_type="list_failed",
            details=str(e)
        )


@router.delete("/{filename}")
async def delete_file(
    filename: str,
    _: dict = Depends(verify_developer_token)
):
    """
    删除文件接口
    
    - **filename**: 文件名
    
    返回删除结果
    """
    try:
        deleted = False
        
        # 在各个目录中查找并删除文件
        for directory in [IMAGES_DIR, DOCUMENTS_DIR, UPLOAD_DIR, TEMP_DIR]:
            file_path = directory / filename
            if file_path.exists():
                file_path.unlink()
                deleted = True
                break
        
        if not deleted:
            raise UnifiedResponse.not_found(
                message="文件不存在",
                error_type="file_not_found"
            )
        
        return UnifiedResponse.success(
            message="文件删除成功",
            data={
                "filename": filename,
                "deleted": True
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"删除文件错误: {e}")
        raise UnifiedResponse.internal_error(
            message="删除文件失败",
            error_type="delete_failed",
            details=str(e)
        )
