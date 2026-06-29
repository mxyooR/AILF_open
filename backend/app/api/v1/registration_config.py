"""
注册配置管理API
管理用户注册相关的配置，包括默认角色、是否允许公开注册等
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import verify_developer_token
from app.models.role import RoleDBModel
from app.config import settings
from typing import Dict, Any, List
from app.core.logging_config import get_logger
from app.core.response import UnifiedResponse
from app.services.security_audit_service import log_security_event
import os

logger = get_logger(__name__)

router = APIRouter(prefix="/registration-config", tags=["注册配置"])


@router.get("/", response_model=dict)
async def get_registration_config(
    current_user: dict = Depends(verify_developer_token),
    db: Session = Depends(get_db)
):
    """
    获取当前注册配置
    """
    try:
        # 获取所有可用角色
        roles = db.query(RoleDBModel).filter(RoleDBModel.status == "active").all()

        # 获取当前默认角色信息
        default_role = db.query(RoleDBModel).filter(
            RoleDBModel.code == settings.DEFAULT_REGISTER_ROLE_CODE,
            RoleDBModel.status == "active"
        ).first()

        # 获取默认角色对应的实体字段
        default_role_fields = []
        if default_role:
            try:
                from app.services.entity_service import EntityService
                entity_service = EntityService()

                # 根据角色代码查找对应的实体
                entity_result = entity_service.get_entity_by_name(default_role.code)

                if entity_result.get("success") and entity_result.get("data"):
                    entity_data = entity_result["data"]["entity"]
                    if hasattr(entity_data, 'fields') and entity_data.fields:
                        for field in entity_data.fields:
                            # 过滤掉系统字段，只保留用户可填写的字段
                            if field.name not in ["id", "created_at", "updated_at", "user_id"]:
                                default_role_fields.append({
                                    "name": field.name,
                                    "display_name": field.displayName,
                                    "type": field.type.value if hasattr(field.type, 'value') else str(field.type),
                                    "required": field.required,
                                    "description": getattr(field, 'description', "")
                                })
                        logger.info(f"获取到默认角色 {default_role.code} 的实体字段: {len(default_role_fields)} 个")
                else:
                    logger.warning(f"未找到默认角色 {default_role.code} 对应的实体")
            except Exception as e:
                logger.error(f"获取默认角色实体字段失败: {str(e)}")

        return UnifiedResponse.success(
            message="获取注册配置成功",
            data={
                "default_role_code": settings.DEFAULT_REGISTER_ROLE_CODE,
                "default_role_info": {
                    "id": default_role.id if default_role else None,
                    "name": default_role.name if default_role else "角色不存在",
                    "code": default_role.code if default_role else settings.DEFAULT_REGISTER_ROLE_CODE,
                    "description": default_role.description if default_role else "默认角色不存在"
                } if default_role else None,
                "default_role_fields": default_role_fields,
                "allow_public_registration": settings.ALLOW_PUBLIC_REGISTRATION,
                "available_roles": [
                    {
                        "id": role.id,
                        "name": role.name,
                        "code": role.code,
                        "description": role.description,
                        "user_count": role.user_count
                    }
                    for role in roles
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"获取注册配置失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="获取注册配置失败",
            error_type="get_config_failed",
            details=str(e)
        )


@router.put("/", response_model=dict)
async def update_registration_config(
    http_request: Request,
    config_data: dict,
    current_user: dict = Depends(verify_developer_token),
    db: Session = Depends(get_db)
):
    """
    更新注册配置
    """
    try:
        default_role_code = config_data.get("default_role_code")
        allow_public_registration = config_data.get("allow_public_registration", True)
        
        # 验证角色是否存在
        if default_role_code:
            role = db.query(RoleDBModel).filter(
                RoleDBModel.code == default_role_code,
                RoleDBModel.status == "active"
            ).first()
            
            if not role:
                raise UnifiedResponse.bad_request(
                    message=f"角色代码 '{default_role_code}' 不存在或已禁用",
                    error_type="invalid_role_code"
                )
        
        # 更新环境变量文件
        env_file_path = ".env"
        env_lines = []
        
        # 读取现有的.env文件
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r', encoding='utf-8') as f:
                env_lines = f.readlines()
        
        # 更新或添加配置项
        updated_lines = []
        default_role_updated = False
        allow_registration_updated = False
        
        for line in env_lines:
            if line.startswith("DEFAULT_REGISTER_ROLE_CODE="):
                updated_lines.append(f"DEFAULT_REGISTER_ROLE_CODE={default_role_code}\n")
                default_role_updated = True
            elif line.startswith("ALLOW_PUBLIC_REGISTRATION="):
                updated_lines.append(f"ALLOW_PUBLIC_REGISTRATION={'true' if allow_public_registration else 'false'}\n")
                allow_registration_updated = True
            else:
                updated_lines.append(line)
        
        # 如果配置项不存在，则添加
        if not default_role_updated:
            updated_lines.append(f"DEFAULT_REGISTER_ROLE_CODE={default_role_code}\n")
        if not allow_registration_updated:
            updated_lines.append(f"ALLOW_PUBLIC_REGISTRATION={'true' if allow_public_registration else 'false'}\n")
        
        # 写入.env文件
        with open(env_file_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        # 更新运行时配置
        settings.DEFAULT_REGISTER_ROLE_CODE = default_role_code
        settings.ALLOW_PUBLIC_REGISTRATION = allow_public_registration
        
        logger.info(f"注册配置更新成功: 默认角色={default_role_code}, 允许公开注册={allow_public_registration}")
        log_security_event(
            event_type="config",
            action="update_registration_config",
            actor_type="developer",
            actor_id=str(current_user.get("user_id", "developer")),
            success=True,
            request=http_request,
            target_type="registration_config",
            target_id="global",
            details={
                "default_role_code": default_role_code,
                "allow_public_registration": allow_public_registration
            }
        )
        
        return UnifiedResponse.success(
            message="注册配置更新成功",
            data={
                "default_role_code": default_role_code,
                "allow_public_registration": allow_public_registration,
                "updated_at": "now"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新注册配置失败: {str(e)}")
        log_security_event(
            event_type="config",
            action="update_registration_config",
            actor_type="developer",
            actor_id=str(current_user.get("user_id", "developer")),
            success=False,
            request=http_request,
            target_type="registration_config",
            target_id="global",
            error="update_config_failed",
            details={"reason": str(e)}
        )
        raise UnifiedResponse.internal_error(
            message="更新注册配置失败",
            error_type="update_config_failed",
            details=str(e)
        )


@router.get("/roles", response_model=dict)
async def get_available_roles(
    current_user: dict = Depends(verify_developer_token),
    db: Session = Depends(get_db)
):
    """
    获取可用于注册的角色列表
    """
    try:
        roles = db.query(RoleDBModel).filter(RoleDBModel.status == "active").all()
        
        return UnifiedResponse.success(
            message="获取可用角色列表成功",
            data=[
                {
                    "id": role.id,
                    "name": role.name,
                    "code": role.code,
                    "description": role.description,
                    "user_count": role.user_count,
                    "is_default": role.code == settings.DEFAULT_REGISTER_ROLE_CODE
                }
                for role in roles
            ]
        )
        
    except Exception as e:
        logger.error(f"获取可用角色列表失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="获取可用角色列表失败",
            error_type="get_roles_failed",
            details=str(e)
        )
