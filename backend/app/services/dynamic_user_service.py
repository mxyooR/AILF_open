"""
动态用户管理服务
根据实体建模中定义的用户实体动态处理用户管理
"""
import json
import time
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.database import get_db_session
from app.core.logging_config import get_logger
from app.models.entity import EntityDBModel, EntityFieldDBModel
from app.models.user import User
from app.models.role import RoleDBModel
from app.services.entity_service import EntityService

logger = get_logger(__name__)


class DynamicUserService:
    """动态用户管理服务"""
    
    def __init__(self):
        self.entity_service = EntityService()
        self.user_entity_name = "user"  # 默认用户实体名称

    def sync_entity_roles(self, db: Session, role_entities: List[EntityDBModel]) -> Dict[str, Any]:
        """
        根据传入的实体列表，同步创建或更新角色记录
        Args:
            db: 数据库会话
            role_entities: 标记为角色的实体对象列表
        """
        try:
            created_roles = []
            updated_roles = []

            for entity in role_entities:
                if not entity.is_role:
                    continue

                # 检查是否已存在对应的角色
                existing_role = db.query(RoleDBModel).filter(RoleDBModel.code == entity.name).first()

                if not existing_role:
                    # 创建新角色
                    role_id = f"role_{entity.name}_{int(time.time() * 1000)}"
                    new_role = RoleDBModel(
                        id=role_id,
                        name=entity.display_name,
                        code=entity.name,
                        description=f"基于 {entity.display_name} 实体自动创建的角色",
                        status="active",
                        user_count=0,
                        created_by="system"
                    )
                    db.add(new_role)
                    created_roles.append({
                        "entity_id": entity.id,
                        "entity_name": entity.name,
                        "role_id": role_id,
                        "role_name": entity.display_name
                    })
                else:
                    # 更新现有角色信息
                    existing_role.name = entity.display_name
                    existing_role.description = f"基于 {entity.display_name} 实体的角色"
                    updated_roles.append({
                        "entity_id": entity.id,
                        "entity_name": entity.name,
                        "role_id": existing_role.id,
                        "role_name": existing_role.name
                    })
            
            # 注意：此函数不再负责commit，由调用方处理
            return {
                "success": True,
                "created_roles": created_roles,
                "updated_roles": updated_roles,
                "total_entities": len(role_entities)
            }
        except Exception as e:
            logger.error(f"❌ 同步角色实体失败: {e}")
            import traceback
            logger.debug(f"详细错误信息: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e)
            }

    def sync_entity_roles_all(self) -> Dict[str, Any]:
        """
        同步所有角色实体为角色记录（向后兼容方法）
        """
        try:
            with get_db_session() as db:
                # 查找所有标记为角色的实体
                role_entities = db.query(EntityDBModel).filter(EntityDBModel.is_role == True).all()

                if not role_entities:
                    return {
                        "success": True,
                        "created_roles": [],
                        "updated_roles": [],
                        "total_entities": 0
                    }

                # 调用主要的同步方法
                result = self.sync_entity_roles(db=db, role_entities=role_entities)

                if result["success"]:
                    db.commit()

                return result
        except Exception as e:
            logger.error(f"同步所有角色实体失败: {e}")
            import traceback
            logger.debug(f"详细错误信息: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_role_entities(self) -> List[Dict[str, Any]]:
        """获取所有标记为角色的实体"""
        try:
            with get_db_session() as db:
                # 查找所有标记为角色的实体 (is_role: true)
                entities = db.query(EntityDBModel).filter(EntityDBModel.is_role == True).all()

                role_entities = []
                for entity in entities:
                    # 获取对应的角色信息
                    role = db.query(RoleDBModel).filter(RoleDBModel.code == entity.name).first()

                    role_entities.append({
                        "id": entity.id,
                        "name": entity.name,
                        "display_name": entity.display_name,
                        "description": entity.description,
                        "is_role": entity.is_role,
                        "field_count": entity.field_count,
                        "role_id": role.id if role else None,
                        "role_name": role.name if role else None,
                        "created_at": entity.created_at.isoformat() if entity.created_at else None
                    })

                return role_entities

        except Exception as e:
            logger.error(f"获取角色实体列表失败: {e}")
            import traceback
            logger.debug(f"详细错误信息: {traceback.format_exc()}")
            return []

    def get_entity_fields(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """获取指定实体的字段定义"""
        try:
            with get_db_session() as db:
                entity = db.query(EntityDBModel).filter(EntityDBModel.id == entity_id).first()
                if not entity:
                    return None

                # 获取实体字段
                fields = db.query(EntityFieldDBModel).filter(
                    EntityFieldDBModel.entity_id == entity.id
                ).order_by(EntityFieldDBModel.sort_order).all()

                return {
                    "entity_id": entity.id,
                    "entity_name": entity.name,
                    "display_name": entity.display_name,
                    "fields": [
                        {
                            "id": field.id,
                            "name": field.name,
                            "display_name": field.display_name,
                            "type": field.type,
                            "required": field.required,
                            "unique": field.unique_field,
                            "default_value": field.default_value,
                            "validation": field.validation,
                            "options": field.options,
                            "sort_order": field.sort_order
                        }
                        for field in fields
                    ]
                }

        except Exception as e:
            logger.error(f"获取实体字段定义失败: {e}")
            import traceback
            logger.debug(f"详细错误信息: {traceback.format_exc()}")
            return None
    
    def get_user_entity_definition(self, role_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取用户实体定义（基于角色）"""
        try:
            with get_db_session() as db:
                if role_id:
                    # 根据角色ID获取对应的实体
                    role = db.query(RoleDBModel).filter(RoleDBModel.id == role_id).first()
                    if role:
                        # 根据角色代码查找对应的实体
                        entity = db.query(EntityDBModel).filter(
                            EntityDBModel.name == role.code,
                            EntityDBModel.is_role == True
                        ).first()
                        if entity:
                            return self.get_entity_fields(entity.id)

                # 如果没有指定角色或找不到对应实体，返回第一个角色实体
                role_entities = self.get_role_entities()
                if role_entities:
                    return self.get_entity_fields(role_entities[0]["id"])

                # 如果没有角色实体，尝试查找传统的用户实体
                user_entity = db.query(EntityDBModel).filter(
                    EntityDBModel.name == self.user_entity_name
                ).first()

                if not user_entity:
                    # 如果没有找到，尝试查找其他可能的用户实体名称
                    possible_names = ["users", "User", "用户"]
                    for name in possible_names:
                        user_entity = db.query(EntityDBModel).filter(
                            EntityDBModel.name == name
                        ).first()
                        if user_entity:
                            self.user_entity_name = name
                            break

                if user_entity:
                    return self.get_entity_fields(user_entity.id)

                return None

        except Exception as e:
            logger.error(f"获取用户实体定义失败: {e}")
            import traceback
            logger.debug(f"详细错误信息: {traceback.format_exc()}")
            return None
    
    def get_user_form_schema(self, role_id: Optional[str] = None) -> Dict[str, Any]:
        """获取用户表单schema（基于角色）"""
        try:
            logger.debug(f"开始获取用户实体定义，角色ID: {role_id}")
            entity_def = self.get_user_entity_definition(role_id)
            logger.debug(f"获取到实体定义: {entity_def}")

            if not entity_def:
                logger.debug("未找到用户实体定义，返回默认schema")
                # 返回默认的用户表单schema
                return self._get_default_user_form_schema()

            # 根据实体定义生成表单schema
            form_fields = []

            for field in entity_def["fields"]:
                field_schema = self._convert_field_to_form_schema(field)
                if field_schema:
                    form_fields.append(field_schema)

            # 添加基础的用户认证字段（用户名、邮箱、密码）
            auth_fields = self._get_auth_fields()
            form_fields.extend(auth_fields)

            # 获取角色信息
            role_info = None
            if role_id:
                with get_db_session() as db:
                    role = db.query(RoleDBModel).filter(RoleDBModel.id == role_id).first()
                    if role:
                        role_info = {
                            "role_id": role.id,
                            "role_name": role.name
                        }

            result = {
                "entity_id": entity_def.get("entity_id"),
                "entity_name": entity_def.get("entity_name"),
                "display_name": entity_def.get("display_name"),
                "role_id": role_info["role_id"] if role_info else None,
                "role_name": role_info["role_name"] if role_info else None,
                "fields": form_fields
            }
            logger.debug(f"生成的表单schema: {result}")
            return result

        except Exception as e:
            logger.error(f"获取用户表单schema时发生错误: {e}")
            import traceback
            logger.debug(f"详细错误信息: {traceback.format_exc()}")
            # 发生错误时返回默认schema
            return self._get_default_user_form_schema()

    def _get_auth_fields(self) -> List[Dict[str, Any]]:
        """获取基础认证字段"""
        return [
            {
                "name": "username",
                "label": "登录用户名",
                "type": "input-text",
                "required": True,
                "placeholder": "请输入登录用户名",
                "validations": {
                    "matchRegexp": "^[a-zA-Z0-9_]{3,20}$"
                }
            },
            {
                "name": "email",
                "label": "邮箱",
                "type": "input-email",
                "required": True,
                "placeholder": "请输入邮箱"
            },
            {
                "name": "password",
                "label": "密码",
                "type": "input-password",
                "required": True,
                "placeholder": "请输入密码",
                "validations": {
                    "minLength": 6
                }
            }
        ]

    def _convert_field_to_form_schema(self, field: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """将实体字段转换为表单字段schema"""
        field_name = field["name"]
        field_type = field["type"]
        
        # 跳过系统字段
        if field_name in ["id", "created_at", "updated_at"]:
            return None
        
        # 基础字段配置
        form_field = {
            "name": field_name,
            "label": field["display_name"],
            "required": field["required"],
            "placeholder": f"请输入{field['display_name']}"
        }
        
        # 根据字段类型设置表单控件类型
        if field_type == "string":
            form_field["type"] = "input-text"
            if field["validation"]:
                validation = field["validation"]
                if validation.get("maxLength"):
                    form_field["maxLength"] = validation["maxLength"]
                if validation.get("minLength"):
                    form_field["minLength"] = validation["minLength"]
                if validation.get("pattern"):
                    form_field["validations"] = {"matchRegexp": validation["pattern"]}
        
        elif field_type == "email":
            form_field["type"] = "input-email"
        
        elif field_type == "password":
            form_field["type"] = "input-password"
        
        elif field_type == "phone":
            form_field["type"] = "input-text"
            form_field["validations"] = {"matchRegexp": "^1[3-9]\\d{9}$"}
        
        elif field_type == "integer":
            form_field["type"] = "input-number"
        
        elif field_type == "boolean":
            form_field["type"] = "switch"
        
        elif field_type == "text":
            form_field["type"] = "textarea"
        
        elif field_type == "select" and field.get("options"):
            form_field["type"] = "select"
            form_field["options"] = [
                {"label": option, "value": option} for option in field["options"]
            ]
        
        elif field_type == "datetime":
            form_field["type"] = "input-datetime"
        
        elif field_type == "url":
            form_field["type"] = "input-url"
        
        else:
            # 默认为文本输入
            form_field["type"] = "input-text"
        
        # 设置默认值
        if field.get("default_value"):
            form_field["value"] = field["default_value"]
        
        return form_field
    
    def _get_default_user_form_schema(self) -> Dict[str, Any]:
        """获取默认用户表单schema"""
        return {
            "entity_id": None,
            "entity_name": "user",
            "display_name": "用户",
            "fields": [
                {
                    "name": "username",
                    "label": "用户名",
                    "type": "input-text",
                    "required": True,
                    "placeholder": "请输入用户名",
                    "validations": {"matchRegexp": "^[a-zA-Z0-9_]{3,20}$"}
                },
                {
                    "name": "email",
                    "label": "邮箱",
                    "type": "input-email",
                    "required": True,
                    "placeholder": "请输入邮箱"
                },
                {
                    "name": "password",
                    "label": "密码",
                    "type": "input-password",
                    "required": True,
                    "placeholder": "请输入密码",
                    "minLength": 6,
                    "maxLength": 20
                },
                {
                    "name": "real_name",
                    "label": "真实姓名",
                    "type": "input-text",
                    "placeholder": "请输入真实姓名"
                },
                {
                    "name": "phone",
                    "label": "手机号",
                    "type": "input-text",
                    "placeholder": "请输入手机号",
                    "validations": {"matchRegexp": "^1[3-9]\\d{9}$"}
                },
                {
                    "name": "role_id",
                    "label": "用户角色",
                    "type": "select",
                    "required": True,
                    "placeholder": "请选择用户角色",
                    "source": "/api/v1/users/roles/available"
                },
                {
                    "name": "is_active",
                    "label": "用户状态",
                    "type": "switch",
                    "value": True
                }
            ]
        }
    
    def get_user_table_columns(self) -> List[Dict[str, Any]]:
        """获取用户表格列配置"""
        entity_def = self.get_user_entity_definition()
        
        if not entity_def:
            return self._get_default_user_table_columns()
        
        columns = []
        
        # 添加基础信息列
        for field in entity_def["fields"]:
            if field["name"] in ["username", "email", "real_name", "phone"]:
                column = {
                    "name": field["name"],
                    "label": field["display_name"],
                    "type": "text"
                }
                columns.append(column)
        
        # 添加角色列
        columns.append({
            "name": "role",
            "label": "角色",
            "type": "mapping",
            "map": {
                "*": "${role.name}"
            }
        })
        
        # 添加状态列
        columns.append({
            "name": "is_active",
            "label": "状态",
            "type": "status",
            "map": {
                "true": {"value": "启用", "status": "success"},
                "false": {"value": "禁用", "status": "fail"}
            }
        })
        
        # 添加时间列
        for field in entity_def["fields"]:
            if field["name"] in ["created_at", "last_login"]:
                column = {
                    "name": field["name"],
                    "label": field["display_name"],
                    "type": "datetime"
                }
                columns.append(column)
        
        return columns
    
    def _get_default_user_table_columns(self) -> List[Dict[str, Any]]:
        """获取默认用户表格列配置"""
        return [
            {"name": "username", "label": "用户名", "type": "text"},
            {"name": "email", "label": "邮箱", "type": "text"},
            {"name": "real_name", "label": "真实姓名", "type": "text"},
            {"name": "role", "label": "角色", "type": "mapping", "map": {"*": "${role.name}"}},
            {"name": "is_active", "label": "状态", "type": "status", "map": {
                "true": {"value": "启用", "status": "success"},
                "false": {"value": "禁用", "status": "fail"}
            }},
            {"name": "created_at", "label": "创建时间", "type": "datetime"},
            {"name": "last_login", "label": "最后登录", "type": "datetime"}
        ]
    
    def validate_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证用户数据"""
        entity_def = self.get_user_entity_definition()
        
        if not entity_def:
            # 使用默认验证
            return self._validate_default_user_data(user_data)
        
        errors = []
        warnings = []
        
        # 根据实体字段定义验证数据
        for field in entity_def["fields"]:
            field_name = field["name"]
            field_value = user_data.get(field_name)
            
            # 检查必填字段
            if field["required"] and not field_value:
                errors.append(f"{field['display_name']}是必填字段")
                continue
            
            # 检查字段验证规则
            if field_value and field.get("validation"):
                validation_result = self._validate_field_value(
                    field_value, field["validation"], field["display_name"]
                )
                errors.extend(validation_result.get("errors", []))
                warnings.extend(validation_result.get("warnings", []))
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_field_value(self, value: Any, validation: Dict[str, Any], field_label: str) -> Dict[str, Any]:
        """验证字段值"""
        errors = []
        warnings = []
        
        if isinstance(value, str):
            if validation.get("minLength") and len(value) < validation["minLength"]:
                errors.append(f"{field_label}长度不能少于{validation['minLength']}个字符")
            
            if validation.get("maxLength") and len(value) > validation["maxLength"]:
                errors.append(f"{field_label}长度不能超过{validation['maxLength']}个字符")
            
            if validation.get("pattern"):
                import re
                if not re.match(validation["pattern"], value):
                    errors.append(f"{field_label}格式不正确")
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_default_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """默认用户数据验证"""
        errors = []
        
        # 基础验证
        if not user_data.get("username"):
            errors.append("用户名是必填字段")
        elif len(user_data["username"]) < 3 or len(user_data["username"]) > 20:
            errors.append("用户名长度必须在3-20字符之间")
        
        if not user_data.get("email"):
            errors.append("邮箱是必填字段")
        
        if not user_data.get("password"):
            errors.append("密码是必填字段")
        elif len(user_data["password"]) < 6 or len(user_data["password"]) > 20:
            errors.append("密码长度必须在6-20字符之间")
        
        if not user_data.get("role_id"):
            errors.append("用户角色是必填字段")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": []
        }


# 全局实例
dynamic_user_service = DynamicUserService()
