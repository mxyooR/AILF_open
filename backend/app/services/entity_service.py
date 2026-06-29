"""
实体建模服务
处理实体定义、字段、关系和数据记录的业务逻辑
"""
import json
import time
import re
from datetime import datetime, date
from app.core.logging_config import get_logger
from app.core.utils import generate_id
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from app.core.database import get_db_session, db_manager
from app.models.entity import (
    EntityDBModel, EntityFieldDBModel, EntityRelationshipDBModel
)
# 注意：EntityRecordDBModel已废弃，实体数据现在存储在独立的entity_{name}表中
from app.schemas.entity import (
    EntityCreateRequest, EntityUpdateRequest, Entity, EntityListItem,
    EntityField, EntityRelationship, EntityRecord, PaginationInfo,
    EntityStatistics, FieldType, RelationshipType, EntityStatus
)

# 配置日志
logger = get_logger(__name__)


class EntityService:
    """实体管理服务类"""
    
    def __init__(self):
        # Cache field labels to avoid frequent DB hits during schema generation.
        self._field_label_cache = {}
        self._field_label_cache_ts = {}
    
    def _generate_id(self, prefix: str) -> str:
        """生成唯一ID"""
        return generate_id(prefix)

    def get_field_label(self, field_name: str, entity_id: Optional[str] = None) -> Optional[str]:
        """
        Resolve a human label for a field using entity metadata (display_name/aliases).
        Falls back to None when not found.
        """
        if not field_name or not isinstance(field_name, str):
            return None

        cache_key = entity_id or "__all__"
        now = time.time()
        cached = self._field_label_cache.get(cache_key)
        cached_ts = self._field_label_cache_ts.get(cache_key, 0)

        # Refresh cache every 60s
        if cached and (now - cached_ts) < 60:
            return cached.get(field_name)

        try:
            with get_db_session() as db:
                query = db.query(EntityFieldDBModel)
                if entity_id:
                    query = query.filter(EntityFieldDBModel.entity_id == entity_id)
                fields = query.all()

                label_map: Dict[str, str] = {}
                for field in fields:
                    display = field.display_name or field.name
                    if field.name and field.name not in label_map:
                        label_map[field.name] = display
                    # include aliases from field.aliases or validation.aliases
                    aliases = field.aliases
                    if not aliases and isinstance(field.validation, dict):
                        aliases = field.validation.get("aliases")
                    if isinstance(aliases, list):
                        for alias in aliases:
                            if alias and alias not in label_map:
                                label_map[alias] = display

                self._field_label_cache[cache_key] = label_map
                self._field_label_cache_ts[cache_key] = now

                return label_map.get(field_name)
        except Exception as e:
            logger.warning(f"获取字段标签失败: {e}")
            return None

    def get_field_label_map(
        self,
        entity_name: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get field->label mapping for an entity (or all entities when not specified).
        """
        cache_key = entity_id or (f"name:{entity_name}" if entity_name else "__all__")
        now = time.time()
        cached = self._field_label_cache.get(cache_key)
        cached_ts = self._field_label_cache_ts.get(cache_key, 0)

        # Refresh cache every 60s
        if cached and (now - cached_ts) < 60:
            return dict(cached)

        try:
            with get_db_session() as db:
                query = db.query(EntityFieldDBModel)
                if entity_id:
                    query = query.filter(EntityFieldDBModel.entity_id == entity_id)
                elif entity_name:
                    entity = db.query(EntityDBModel).filter(EntityDBModel.name == entity_name).first()
                    if not entity:
                        return {}
                    query = query.filter(EntityFieldDBModel.entity_id == entity.id)
                fields = query.all()

                label_map: Dict[str, str] = {}
                for field in fields:
                    display = field.display_name or field.name
                    if field.name and field.name not in label_map:
                        label_map[field.name] = display
                    aliases = field.aliases
                    if not aliases and isinstance(field.validation, dict):
                        aliases = field.validation.get("aliases")
                    if isinstance(aliases, list):
                        for alias in aliases:
                            if alias and alias not in label_map:
                                label_map[alias] = display

                self._field_label_cache[cache_key] = label_map
                self._field_label_cache_ts[cache_key] = now

                return dict(label_map)
        except Exception as e:
            logger.warning(f"获取字段标签失败: {e}")
            return {}
    
    def _convert_db_entity_to_schema(self, db_entity: EntityDBModel, include_fields: bool = True, 
                                   include_relationships: bool = False, include_statistics: bool = False) -> Entity:
        """将数据库实体转换为Schema模型"""
        # 基础字段
        entity_data = {
            "id": db_entity.id,
            "name": db_entity.name,
            "displayName": db_entity.display_name,
            "description": db_entity.description,
            "icon": db_entity.icon,
            "isRole": bool(db_entity.is_role) if db_entity.is_role is not None else False,
            "status": EntityStatus(db_entity.status),
            "field_count": db_entity.field_count,
            "record_count": db_entity.record_count,
            "created_at": db_entity.created_at.isoformat() if db_entity.created_at else "",
            "updated_at": db_entity.updated_at.isoformat() if db_entity.updated_at else ""
        }
        
        # 包含字段信息
        if include_fields and db_entity.fields:
            entity_data["fields"] = [
                EntityField(
                    id=field.id,
                    name=field.name,
                    displayName=field.display_name,
                    type=FieldType(field.type),
                    required=field.required,
                    unique=field.unique_field,
                    defaultValue=field.default_value,
                    validation=field.validation,
                    options=field.options,
                    aliases=field.aliases or (field.validation.get("aliases") if isinstance(field.validation, dict) else None),
                    sort_order=field.sort_order
                ) for field in sorted(db_entity.fields, key=lambda x: x.sort_order)
            ]
        
        # 包含关系信息
        if include_relationships and db_entity.source_relationships:
            entity_data["relationships"] = [
                EntityRelationship(
                    id=rel.id,
                    name=rel.name,
                    sourceEntity=db_entity.name,
                    targetEntity=rel.target_entity.name if rel.target_entity else rel.target_entity_id,
                    type=RelationshipType(rel.type),
                    foreignKey=rel.foreign_key,
                    constraints=rel.constraints,
                    created_at=rel.created_at.isoformat() if rel.created_at else "",
                    updated_at=rel.updated_at.isoformat() if rel.updated_at else ""
                ) for rel in db_entity.source_relationships
            ]
        
        # 包含统计信息
        if include_statistics:
            entity_data["statistics"] = EntityStatistics(
                record_count=db_entity.record_count or 0,
                field_count=db_entity.field_count or 0,
                relationship_count=len(db_entity.source_relationships) if db_entity.source_relationships else 0,
                last_updated=db_entity.updated_at.isoformat() if db_entity.updated_at else ""
            )
        
        return Entity(**entity_data)
    
    async def create_entity(self, request: EntityCreateRequest) -> Dict[str, Any]:
        """创建实体"""
        try:
            with get_db_session() as db:
                logger.debug(f"[EntityService] create_entity 参数:")
                logger.debug(f"  - entity name: {request.name}")
                logger.debug(f"  - display name: {request.displayName}")
                
                # 检查实体名称是否重复
                existing_entity = db.query(EntityDBModel).filter(
                    EntityDBModel.name == request.name
                ).first()
                
                if existing_entity:
                    return {
                        "success": False,
                        "error": "duplicate_entity_name",
                        "details": "实体名称已存在"
                    }
                
                # 创建实体
                entity_id = self._generate_id("entity")
                db_entity = EntityDBModel(
                    id=entity_id,
                    name=request.name,
                    display_name=request.displayName,
                    description=request.description,
                    icon=request.icon,
                    status="active",
                    is_role=request.isRole or False,
                    field_count=len(request.fields),
                    record_count=0
                )
                
                db.add(db_entity)
                db.flush()  # 获取实体ID
                
                # 创建字段
                for i, field_request in enumerate(request.fields):
                    field_id = self._generate_id("field")
                    db_field = EntityFieldDBModel(
                        id=field_id,
                        entity_id=entity_id,
                        name=field_request.name,
                        display_name=field_request.displayName,
                        type=field_request.type.value,
                        required=field_request.required,
                        unique_field=field_request.unique,
                        default_value=field_request.defaultValue,
                        validation=field_request.validation.model_dump() if field_request.validation else None,
                        options=field_request.options,
                        aliases=field_request.aliases,
                        sort_order=i
                    )
                    db.add(db_field)
                
                db.commit()
                
                # 自动创建数据库表
                try:
                    await self._create_entity_database_table(request.name, request.fields, db)
                    logger.info(f"✅ 为实体 '{request.displayName}' 自动创建了数据库表")
                except Exception as table_error:
                    logger.warning(f"⚠️ 实体 '{request.displayName}' 的数据库表创建失败: {str(table_error)}")
                    import traceback
                    logger.debug(f"表创建错误详情: {traceback.format_exc()}")
                
                # 重新查询以获取完整信息
                db_entity = db.query(EntityDBModel).filter(EntityDBModel.id == entity_id).first()
                entity = self._convert_db_entity_to_schema(db_entity, include_fields=True)
                
                # 如果是角色实体，自动创建对应的角色
                if request.isRole:
                    try:
                        from app.services.dynamic_user_service import DynamicUserService
                        user_service = DynamicUserService()
                        # 传递当前数据库会话和刚创建的实体
                        sync_result = user_service.sync_entity_roles(db=db, role_entities=[entity])
                        if sync_result.get("success") and sync_result.get("created_roles"):
                            created_roles = sync_result.get("created_roles", [])
                            logger.info(f"✅ 为角色实体 {request.displayName} 自动创建了 {len(created_roles)} 个角色")
                            for role in created_roles:
                                logger.debug(f"  - 创建角色: {role['role_name']} (基于实体: {role['entity_name']})")
                        else:
                            logger.warning(f"⚠️ 角色实体 {request.displayName} 未找到需要同步的角色")
                    except Exception as e:
                        logger.warning(f"⚠️ 角色实体 {request.displayName} 的角色同步失败: {str(e)}")
                        import traceback
                        logger.debug(f"详细错误信息: {traceback.format_exc()}")
                
                return {
                    "success": True,
                    "data": {"entity": entity}
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": "creation_failed",
                "details": f"创建实体失败: {str(e)}"
            }
    
    def get_entities_list(self, include_fields: bool = True, status: Optional[str] = None) -> Dict[str, Any]:
        """获取实体列表"""
        try:
            with get_db_session() as db:
                query = db.query(EntityDBModel)
                
                # 筛选条件
                if status:
                    query = query.filter(EntityDBModel.status == status)
                
                db_entities = query.order_by(EntityDBModel.created_at.desc()).all()
                
                entities = []
                for db_entity in db_entities:
                    entity_item = EntityListItem(
                        id=db_entity.id,
                        name=db_entity.name,
                        displayName=db_entity.display_name,
                        description=db_entity.description,
                        icon=db_entity.icon,
                        isRole=db_entity.is_role or False,
                        status=EntityStatus(db_entity.status),
                        field_count=db_entity.field_count or 0,
                        record_count=db_entity.record_count or 0,
                        created_at=db_entity.created_at.isoformat() if db_entity.created_at else "",
                        updated_at=db_entity.updated_at.isoformat() if db_entity.updated_at else ""
                    )
                    
                    # 包含字段信息
                    if include_fields and db_entity.fields:
                        entity_item.fields = [
                        EntityField(
                            id=field.id,
                            name=field.name,
                            displayName=field.display_name,
                            type=FieldType(field.type),
                            required=field.required,
                            unique=field.unique_field,
                            defaultValue=field.default_value,
                            validation=field.validation,
                            options=field.options,
                            aliases=field.aliases or (field.validation.get("aliases") if isinstance(field.validation, dict) else None),
                            sort_order=field.sort_order
                        ) for field in sorted(db_entity.fields, key=lambda x: x.sort_order)
                    ]
                    
                    entities.append(entity_item)
                
                return {
                    "success": True,
                    "data": {
                        "entities": entities,
                        "total": len(entities)
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": "query_failed",
                "details": f"查询实体列表失败: {str(e)}"
            }
    
    def get_entity_by_id(self, entity_id: str) -> Dict[str, Any]:
        """根据ID获取实体详情"""
        try:
            with get_db_session() as db:
                db_entity = db.query(EntityDBModel).filter(EntityDBModel.id == entity_id).first()
                
                if not db_entity:
                    return {
                        "success": False,
                        "error": "entity_not_found",
                        "details": "实体不存在"
                    }
                
                entity = self._convert_db_entity_to_schema(
                    db_entity, 
                    include_fields=True, 
                    include_relationships=True, 
                    include_statistics=True
                )
                
                return {
                    "success": True,
                    "data": {"entity": entity}
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": "query_failed",
                "details": f"查询实体详情失败: {str(e)}"
            }

    def get_entity_by_name(self, entity_name: str) -> Dict[str, Any]:
        """根据名称获取实体详情"""
        try:
            with get_db_session() as db:
                from sqlalchemy.orm import joinedload

                query = db.query(EntityDBModel).options(
                    joinedload(EntityDBModel.fields)
                ).filter(EntityDBModel.name == entity_name)

                db_entity = query.first()

                if not db_entity:
                    return {
                        "success": False,
                        "error": "entity_not_found",
                        "details": f"实体 '{entity_name}' 不存在"
                    }

                # 调试信息
                logger.debug(f"找到实体: {db_entity.name}, 字段数量: {len(db_entity.fields) if db_entity.fields else 0}")
                if db_entity.fields:
                    for field in db_entity.fields:
                        logger.debug(f"  - 字段: {field.name} ({field.display_name})")

                entity = self._convert_db_entity_to_schema(
                    db_entity,
                    include_fields=True,
                    include_relationships=True,
                    include_statistics=True
                )

                return {
                    "success": True,
                    "data": {"entity": entity}
                }

        except Exception as e:
            return {
                "success": False,
                "error": "query_failed",
                "details": f"查询实体详情失败: {str(e)}"
            }

    async def update_entity(self, entity_id: str, request: EntityUpdateRequest) -> Dict[str, Any]:
        """更新实体"""
        try:
            with get_db_session() as db:
                db_entity = db.query(EntityDBModel).filter(EntityDBModel.id == entity_id).first()
                
                if not db_entity:
                    return {
                        "success": False,
                        "error": "entity_not_found",
                        "details": "实体不存在"
                    }
                
                original_name = db_entity.name
                
                # 更新基础信息
                if request.displayName is not None:
                    db_entity.display_name = request.displayName
                if request.description is not None:
                    db_entity.description = request.description
                if request.icon is not None:
                    db_entity.icon = request.icon
                if request.isRole is not None:
                    db_entity.is_role = request.isRole
                
                # 更新字段（如果提供）
                if request.fields is not None:
                    # 删除现有字段
                    db.query(EntityFieldDBModel).filter(EntityFieldDBModel.entity_id == entity_id).delete()
                    
                    # 创建新字段
                    for i, field_request in enumerate(request.fields):
                        field_id = self._generate_id("field")
                        db_field = EntityFieldDBModel(
                            id=field_id,
                            entity_id=entity_id,
                            name=field_request.name,
                            display_name=field_request.displayName,
                            type=field_request.type.value,
                            required=field_request.required,
                            unique_field=field_request.unique,
                            default_value=field_request.defaultValue,
                            validation=field_request.validation.model_dump() if field_request.validation else None,
                            options=field_request.options,
                            aliases=field_request.aliases,
                            sort_order=i
                        )
                        db.add(db_field)
                    
                    db_entity.field_count = len(request.fields)
                
                db.commit()

                # 更新数据库表结构
                if request.fields is not None:
                    try:
                        await self._alter_entity_database_table(original_name, request.fields, db)
                        logger.info(f"✅ 尝试为实体 '{db_entity.display_name}' 更新数据库表结构")
                    except Exception as table_error:
                        logger.error(f"⚠️ 实体 '{db_entity.display_name}' 的数据库表更新失败: {str(table_error)}")
                        import traceback
                        logger.error(f"表更新错误详情: {traceback.format_exc()}")

                # 重新查询以获取完整信息
                db.refresh(db_entity)
                entity = self._convert_db_entity_to_schema(db_entity, include_fields=True)
                
                return {
                    "success": True,
                    "data": {"entity": entity}
                }
                
        except Exception as e:
            logger.error(f"更新实体失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": "update_failed",
                "details": f"更新实体失败: {str(e)}"
            }
    
    async def _alter_entity_database_table(self, entity_name: str, fields: List, db: Session) -> None:
        """为实体自动更新MySQL数据库表结构"""
        from sqlalchemy import text
        
        table_name = f"entity_{self._safe_table_name(entity_name)}"
        
        # 1. 获取当前表结构
        try:
            get_columns_query = text(f"""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table_name}'
            """)
            existing_columns_result = db.execute(get_columns_query).fetchall()
            existing_columns = {row[0] for row in existing_columns_result}
        except Exception as e:
            logger.error(f"无法获取表 '{table_name}' 的结构: {e}")
            return

        # 2. 找出需要添加的新字段
        desired_fields = {self._safe_column_name(field.name) for field in fields}
        fields_to_add = desired_fields - existing_columns
        
        if not fields_to_add:
            logger.info(f"表 {table_name} 结构已是最新，无需更新。")
            return

        # 3. 构建并执行 ALTER TABLE 语句
        for field in fields:
            field_name = self._safe_column_name(field.name)
            if field_name not in fields_to_add:
                continue

            if field.type.value in ['number', 'integer']:
                sql_type = "DECIMAL(10,2)"
            elif field.type.value == 'boolean':
                sql_type = "BOOLEAN"
            elif field.type.value == 'date':
                sql_type = "DATE"
            elif field.type.value == 'datetime':
                sql_type = "DATETIME"
            elif field.type.value == 'email':
                sql_type = "VARCHAR(255)"
            elif field.type.value == 'phone':
                sql_type = "VARCHAR(20)"
            elif field.type.value == 'reference':
                sql_type = "VARCHAR(36)"
            elif field.type.value in ['select', 'multiselect', 'text']:
                sql_type = "TEXT"
            else:
                sql_type = "VARCHAR(500)"
            
            constraints = []
            if field.required:
                constraints.append("NOT NULL")
            if getattr(field, 'unique', False):
                constraints.append("UNIQUE")
            if field.defaultValue:
                escaped_default = self._escape_sql_literal(field.defaultValue)
                if sql_type == "TEXT" and field.defaultValue:
                    sql_type = "VARCHAR(255)"
                    constraints.append(f"DEFAULT '{escaped_default}'")
                elif sql_type in ["VARCHAR(500)", "VARCHAR(255)", "VARCHAR(20)"]:
                    constraints.append(f"DEFAULT '{escaped_default}'")
                else:
                    constraints.append(f"DEFAULT '{escaped_default}'")
            
            constraint_str = " ".join(constraints)
            column_def = f"`{field_name}` {sql_type} {constraint_str}".strip()

            try:
                alter_sql = text(f"ALTER TABLE `{table_name}` ADD COLUMN {column_def}")
                db.execute(alter_sql)
                logger.info(f"成功为表 '{table_name}' 添加字段: {field_name}")
            except Exception as e:
                logger.error(f"为表 '{table_name}' 添加字段 '{field_name}' 失败: {e}")
        
        db.commit()

    def delete_entity(self, entity_id: str, force: bool = False, backup: bool = True) -> Dict[str, Any]:
        """删除实体"""
        try:
            with get_db_session() as db:
                db_entity = db.query(EntityDBModel).filter(EntityDBModel.id == entity_id).first()
                
                if not db_entity:
                    return {
                        "success": False,
                        "error": "entity_not_found",
                        "details": "实体不存在"
                    }
                
                # 统计影响的关系
                affected_relationships = db.query(EntityRelationshipDBModel).filter(
                    or_(
                        EntityRelationshipDBModel.source_entity_id == entity_id,
                        EntityRelationshipDBModel.target_entity_id == entity_id
                    )
                ).count()
                
                # 统计实体表中的记录数
                table_name = f"entity_{self._safe_table_name(db_entity.name)}"
                affected_records = 0
                try:
                    from sqlalchemy import text
                    check_table_query = text(f"""
                        SELECT table_name FROM information_schema.tables
                        WHERE table_schema = DATABASE() AND table_name = :table_name
                    """)
                    table_exists = db.execute(check_table_query, {"table_name": table_name}).fetchone()
                    if table_exists:
                        count_query = text(f"SELECT COUNT(*) FROM `{table_name}`")
                        affected_records = db.execute(count_query).scalar() or 0
                except Exception as e:
                    logger.warning(f"统计实体记录数失败: {e}")
                
                # 备份数据（如果需要）
                backup_file = None
                if backup:
                    backup_data = {
                        "entity": {
                            "id": db_entity.id,
                            "name": db_entity.name,
                            "display_name": db_entity.display_name,
                            "description": db_entity.description,
                            "icon": db_entity.icon,
                            "status": db_entity.status
                        },
                        "fields": [
                            {
                                "name": field.name,
                                "display_name": field.display_name,
                                "type": field.type,
                                "required": field.required,
                                "unique_field": field.unique_field,
                                "default_value": field.default_value,
                                "validation": field.validation,
                                "options": field.options
                            } for field in db_entity.fields
                        ]
                    }
                    backup_file = f"/backups/entity_{db_entity.name}_{int(time.time())}.json"
                    # 这里应该实际保存备份文件，暂时只是生成文件名
                
                # 获取实体名称用于删除对应的数据表
                entity_name = db_entity.name
                table_name = f"entity_{self._safe_table_name(entity_name)}"
                
                # 删除对应的MySQL数据表
                try:
                    self._drop_entity_database_table(db, table_name)
                    logger.info(f"删除实体数据表成功: {table_name}")
                except Exception as table_error:
                    logger.warning(f"删除实体数据表失败: {table_error}")
                    # 继续执行，不因为表删除失败而中断实体删除
                
                # 删除实体（级联删除字段、关系和记录）
                db.delete(db_entity)
                db.commit()
                
                return {
                    "success": True,
                    "data": {
                        "entity_id": entity_id,
                        "name": db_entity.name,
                        "table_name": table_name,
                        "deleted_at": time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                        "backup_file": backup_file,
                        "affected_records": affected_records,
                        "affected_relationships": affected_relationships
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": "deletion_failed",
                "details": f"删除实体失败: {str(e)}"
            }


    def get_entity_records(self, entity_id: str, page: int = 1, limit: int = 20,
                          filters: Optional[Dict[str, Any]] = None,
                          sort_by: Optional[str] = None, sort_order: str = "desc") -> Dict[str, Any]:
        """获取实体数据记录列表 - 从实体独立表读取"""
        try:
            from sqlalchemy import text
            
            with get_db_session() as db:
                # 检查实体是否存在
                db_entity = db.query(EntityDBModel).filter(EntityDBModel.id == entity_id).first()
                if not db_entity:
                    return {
                        "success": False,
                        "error": "entity_not_found",
                        "details": "实体不存在"
                    }

                # 获取实体对应的表名
                table_name = f"entity_{self._safe_table_name(db_entity.name)}"
                
                # 检查表是否存在
                check_table_query = text(f"""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = DATABASE() AND table_name = :table_name
                """)
                table_exists = db.execute(check_table_query, {"table_name": table_name}).fetchone()
                
                if not table_exists:
                    # 表不存在，返回空记录
                    logger.warning(f"实体表 {table_name} 不存在")
                    return {
                        "success": True,
                        "data": {
                            "records": [],
                            "pagination": PaginationInfo(
                                page=page,
                                limit=limit,
                                total=0,
                                pages=0,
                                has_next=False,
                                has_prev=False
                            )
                        }
                    }

                # 构建WHERE子句
                where_clauses = []
                params = {}
                field_names = set()
                field_alias_map = {}
                base_columns = {"id", "created_at", "updated_at"}
                if db_entity.fields:
                    for field in db_entity.fields:
                        field_names.add(field.name)
                        aliases = field.aliases or (field.validation.get("aliases") if isinstance(field.validation, dict) else None)
                        if aliases and isinstance(aliases, list):
                            for alias in aliases:
                                if alias:
                                    field_alias_map[alias] = field.name
                    # Fallback alias: <entity>_number -> <entity>_id when *_id field is absent
                    for field_name in list(field_names):
                        if field_name.endswith("_number"):
                            base = field_name[:-7]
                            candidate = f"{base}_id"
                            if candidate not in field_names and candidate not in field_alias_map:
                                field_alias_map[candidate] = field_name
                if filters:
                    for i, (field_name, value) in enumerate(filters.items()):
                        if value is not None:
                            resolved_field = field_alias_map.get(field_name, field_name)
                            if resolved_field not in field_names and resolved_field not in base_columns:
                                logger.warning(f"忽略未知过滤字段: {field_name} -> {resolved_field}")
                                continue
                            param_name = f"filter_{i}"
                            where_clauses.append(f"`{resolved_field}` = :{param_name}")
                            params[param_name] = value

                where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

                # 排序
                order_field = sort_by if sort_by else "created_at"
                if order_field:
                    order_field = field_alias_map.get(order_field, order_field)
                    if order_field not in field_names and order_field not in base_columns:
                        logger.warning(f"忽略未知排序字段: {sort_by} -> {order_field}, fallback created_at")
                        order_field = "created_at"
                order_direction = "ASC" if sort_order.lower() == "asc" else "DESC"
                order_sql = f"ORDER BY `{order_field}` {order_direction}"

                # 获取总数
                count_sql = text(f"SELECT COUNT(*) FROM `{table_name}` {where_sql}")
                total = db.execute(count_sql, params).scalar() or 0

                # 分页查询
                offset = (page - 1) * limit
                query_sql = text(f"SELECT * FROM `{table_name}` {where_sql} {order_sql} LIMIT :limit OFFSET :offset")
                params["limit"] = limit
                params["offset"] = offset
                
                result = db.execute(query_sql, params)
                rows = result.fetchall()
                columns = result.keys()

                # 转换为响应格式
                records = []
                for row in rows:
                    record_data = {}
                    for col, val in zip(columns, row):
                        if col in ['created_at', 'updated_at'] and val:
                            record_data[col] = val.isoformat() if hasattr(val, 'isoformat') else str(val)
                        else:
                            record_data[col] = val
                    # Add alias fields for output consistency
                    if field_alias_map:
                        for alias, resolved_field in field_alias_map.items():
                            if alias not in record_data and resolved_field in record_data:
                                record_data[alias] = record_data.get(resolved_field)
                    records.append(record_data)

                # 分页信息
                pages = (total + limit - 1) // limit if total > 0 else 0
                pagination = PaginationInfo(
                    page=page,
                    limit=limit,
                    total=total,
                    pages=pages,
                    has_next=page < pages,
                    has_prev=page > 1
                )

                return {
                    "success": True,
                    "data": {
                        "records": records,
                        "pagination": pagination
                    }
                }

        except Exception as e:
            logger.error(f"查询实体记录失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": "query_failed",
                "details": f"查询实体记录失败: {str(e)}"
            }

    def create_entity_record(self, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建实体数据记录 - 插入到实体独立表"""
        try:
            from sqlalchemy import text
            import uuid
            
            with get_db_session() as db:
                # 检查实体是否存在
                db_entity = db.query(EntityDBModel).filter(EntityDBModel.id == entity_id).first()
                if not db_entity:
                    return {
                        "success": False,
                        "error": "entity_not_found",
                        "details": "实体不存在"
                    }

                # 验证数据（简化版本）
                validation_result = self._validate_record_data(db_entity, data)
                if not validation_result["valid"]:
                    return {
                        "success": False,
                        "error": "validation_failed",
                        "details": validation_result["errors"]
                    }

                # 获取实体对应的表名
                table_name = f"entity_{self._safe_table_name(db_entity.name)}"
                
                # 检查表是否存在
                check_table_query = text(f"""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = DATABASE() AND table_name = :table_name
                """)
                table_exists = db.execute(check_table_query, {"table_name": table_name}).fetchone()
                
                if not table_exists:
                    return {
                        "success": False,
                        "error": "table_not_found",
                        "details": f"实体数据表 {table_name} 不存在，请重新创建实体"
                    }

                # 生成记录ID
                record_id = str(uuid.uuid4())
                
                # 构建INSERT语句
                columns = ["id"]
                placeholders = [":id"]
                params = {"id": record_id}
                
                def _normalize_field_value(field: EntityFieldDBModel, value: Any) -> Any:
                    if value is None:
                        return value
                    field_type = (field.type or "").lower()
                    if field_type in ("datetime", "timestamp"):
                        if isinstance(value, datetime):
                            return value.strftime("%Y-%m-%d %H:%M:%S")
                        if isinstance(value, str):
                            raw = value.strip()
                            iso = raw
                            if iso.endswith("Z"):
                                iso = iso[:-1] + "+00:00"
                            try:
                                parsed = datetime.fromisoformat(iso)
                                return parsed.strftime("%Y-%m-%d %H:%M:%S")
                            except Exception:
                                cleaned = raw.replace("T", " ").replace("Z", "")
                                cleaned = re.sub(r"(?:\\+|-)\\d{2}:?\\d{2}$", "", cleaned)
                                return cleaned
                    if field_type == "date":
                        if isinstance(value, date):
                            return value.strftime("%Y-%m-%d")
                        if isinstance(value, str):
                            raw = value.strip()
                            iso = raw
                            if iso.endswith("Z"):
                                iso = iso[:-1] + "+00:00"
                            try:
                                parsed = datetime.fromisoformat(iso)
                                return parsed.strftime("%Y-%m-%d")
                            except Exception:
                                cleaned = raw.split("T")[0]
                                return cleaned
                    return value

                for field in db_entity.fields:
                    field_name = field.name
                    if field_name in data:
                        columns.append(f"`{field_name}`")
                        param_name = f"p_{field_name}"
                        placeholders.append(f":{param_name}")
                        params[param_name] = _normalize_field_value(field, data[field_name])
                
                insert_sql = text(f"""
                    INSERT INTO `{table_name}` ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """)
                
                db.execute(insert_sql, params)
                
                # 更新实体记录数量
                db_entity.record_count = (db_entity.record_count or 0) + 1
                
                db.commit()

                # 查询刚插入的记录以获取完整数据（包括created_at等）
                select_sql = text(f"SELECT * FROM `{table_name}` WHERE id = :id")
                result = db.execute(select_sql, {"id": record_id})
                row = result.fetchone()
                columns = result.keys()
                
                # 构建响应数据
                record_data = {}
                if row:
                    for col, val in zip(columns, row):
                        if col in ['created_at', 'updated_at'] and val:
                            record_data[col] = val.isoformat() if hasattr(val, 'isoformat') else str(val)
                        else:
                            record_data[col] = val
                else:
                    record_data = data.copy()
                    record_data["id"] = record_id

                return {
                    "success": True,
                    "data": {"record": record_data}
                }

        except Exception as e:
            logger.error(f"创建记录失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": "creation_failed",
                "details": f"创建记录失败: {str(e)}"
            }

    def update_entity_record(self, entity_id: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新实体数据记录 - 更新实体独立表"""
        try:
            from sqlalchemy import text
            
            with get_db_session() as db:
                # 检查实体是否存在
                db_entity = db.query(EntityDBModel).filter(EntityDBModel.id == entity_id).first()
                if not db_entity:
                    return {
                        "success": False,
                        "error": "entity_not_found",
                        "details": "实体不存在"
                    }

                # 获取实体对应的表名
                table_name = f"entity_{self._safe_table_name(db_entity.name)}"
                
                # 检查记录是否存在
                check_record_sql = text(f"SELECT id FROM `{table_name}` WHERE id = :id")
                record_exists = db.execute(check_record_sql, {"id": record_id}).fetchone()
                
                if not record_exists:
                    return {
                        "success": False,
                        "error": "record_not_found",
                        "details": "记录不存在"
                    }

                # 验证数据（排除当前记录进行唯一性检查）
                validation_result = self._validate_record_data(
                    db_entity,
                    data,
                    exclude_record_id=record_id,
                    partial=True
                )
                if not validation_result["valid"]:
                    return {
                        "success": False,
                        "error": "validation_failed",
                        "details": validation_result["errors"]
                    }

                # 构建UPDATE语句
                set_clauses = ["updated_at = NOW()"]  # 自动更新 updated_at 字段
                params = {"id": record_id}
                
                for field in db_entity.fields:
                    field_name = field.name
                    if field_name in data:
                        param_name = f"p_{field_name}"
                        set_clauses.append(f"`{field_name}` = :{param_name}")
                        params[param_name] = data[field_name]
                
                if len(set_clauses) <= 1:  # 只有 updated_at，没有其他字段
                    return {
                        "success": False,
                        "error": "no_data",
                        "details": "没有要更新的数据"
                    }
                
                update_sql = text(f"""
                    UPDATE `{table_name}` 
                    SET {', '.join(set_clauses)}
                    WHERE id = :id
                """)
                
                db.execute(update_sql, params)
                db.commit()

                # 查询更新后的记录
                select_sql = text(f"SELECT * FROM `{table_name}` WHERE id = :id")
                result = db.execute(select_sql, {"id": record_id})
                row = result.fetchone()
                columns = result.keys()
                
                # 构建响应数据
                record_data = {}
                if row:
                    for col, val in zip(columns, row):
                        if col in ['created_at', 'updated_at'] and val:
                            record_data[col] = val.isoformat() if hasattr(val, 'isoformat') else str(val)
                        else:
                            record_data[col] = val
                else:
                    record_data = data.copy()
                    record_data["id"] = record_id

                return {
                    "success": True,
                    "data": {"record": record_data}
                }

        except Exception as e:
            logger.error(f"更新记录失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": "update_failed",
                "details": f"更新记录失败: {str(e)}"
            }

    def delete_entity_record(self, entity_id: str, record_id: str) -> Dict[str, Any]:
        """删除实体数据记录 - 从实体独立表删除"""
        try:
            from sqlalchemy import text
            import time
            
            with get_db_session() as db:
                # 检查实体是否存在
                db_entity = db.query(EntityDBModel).filter(EntityDBModel.id == entity_id).first()
                if not db_entity:
                    return {
                        "success": False,
                        "error": "entity_not_found",
                        "details": "实体不存在"
                    }

                # 获取实体对应的表名
                table_name = f"entity_{self._safe_table_name(db_entity.name)}"
                
                # 检查记录是否存在
                check_record_sql = text(f"SELECT id FROM `{table_name}` WHERE id = :id")
                record_exists = db.execute(check_record_sql, {"id": record_id}).fetchone()
                
                if not record_exists:
                    return {
                        "success": False,
                        "error": "record_not_found",
                        "details": "记录不存在"
                    }

                # 删除记录
                delete_sql = text(f"DELETE FROM `{table_name}` WHERE id = :id")
                db.execute(delete_sql, {"id": record_id})

                # 更新实体记录数量
                db_entity.record_count = max(0, (db_entity.record_count or 1) - 1)

                db.commit()

                return {
                    "success": True,
                    "data": {
                        "record_id": record_id,
                        "deleted_at": time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                    }
                }

        except Exception as e:
            logger.error(f"删除记录失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": "deletion_failed",
                "details": f"删除记录失败: {str(e)}"
            }

    def _validate_record_data(
        self,
        db_entity: EntityDBModel,
        data: Dict[str, Any],
        exclude_record_id: Optional[str] = None,
        *,
        partial: bool = False
    ) -> Dict[str, Any]:
        """
        验证记录数据
        
        Args:
            db_entity: 实体数据库模型
            data: 要验证的数据
            exclude_record_id: 排除的记录ID（用于更新时排除自身）
        """
        from sqlalchemy import text
        
        errors = []

        # 检查必填字段（partial 更新仅校验传入字段）
        for field in db_entity.fields:
            if not field.required:
                continue
            if partial and field.name not in data:
                continue
            if field.name not in data or data[field.name] is None or data[field.name] == '':
                errors.append(f"字段 '{field.display_name}' 是必填的")

        # 检查唯一字段
        with get_db_session() as db:
            table_name = f"entity_{self._safe_table_name(db_entity.name)}"
            
            # 检查表是否存在
            check_table_query = text(f"""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = DATABASE() AND table_name = :table_name
            """)
            table_exists = db.execute(check_table_query, {"table_name": table_name}).fetchone()
            
            if table_exists:
                for field in db_entity.fields:
                    if field.unique_field and field.name in data and data[field.name] is not None:
                        # 构建唯一性检查查询
                        if exclude_record_id:
                            check_unique_sql = text(f"""
                                SELECT COUNT(*) FROM `{table_name}` 
                                WHERE `{field.name}` = :value AND id != :exclude_id
                            """)
                            count = db.execute(check_unique_sql, {
                                "value": data[field.name],
                                "exclude_id": exclude_record_id
                            }).scalar()
                        else:
                            check_unique_sql = text(f"""
                                SELECT COUNT(*) FROM `{table_name}` 
                                WHERE `{field.name}` = :value
                            """)
                            count = db.execute(check_unique_sql, {"value": data[field.name]}).scalar()
                        
                        if count > 0:
                            errors.append(f"字段 '{field.display_name}' 的值 '{data[field.name]}' 已存在，必须唯一")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def get_entity_relationships(self, entity_id: str) -> Dict[str, Any]:
        """获取实体关系列表"""
        try:
            with get_db_session() as db:
                # 检查实体是否存在
                db_entity = db.query(EntityDBModel).filter(EntityDBModel.id == entity_id).first()
                if not db_entity:
                    return {
                        "success": False,
                        "error": "entity_not_found",
                        "details": "实体不存在"
                    }

                # 获取作为源实体的关系
                source_relationships = db.query(EntityRelationshipDBModel).filter(
                    EntityRelationshipDBModel.source_entity_id == entity_id
                ).all()

                # 获取作为目标实体的关系
                target_relationships = db.query(EntityRelationshipDBModel).filter(
                    EntityRelationshipDBModel.target_entity_id == entity_id
                ).all()

                relationships = []

                # 处理源关系
                for rel in source_relationships:
                    target_entity = db.query(EntityDBModel).filter(EntityDBModel.id == rel.target_entity_id).first()
                    relationships.append(EntityRelationship(
                        id=rel.id,
                        name=rel.name,
                        sourceEntity=db_entity.name,
                        targetEntity=target_entity.name if target_entity else rel.target_entity_id,
                        type=RelationshipType(rel.type),
                        foreignKey=rel.foreign_key,
                        constraints=rel.constraints,
                        created_at=rel.created_at.isoformat() if rel.created_at else "",
                        updated_at=rel.updated_at.isoformat() if rel.updated_at else ""
                    ))

                # 处理目标关系（反向关系）
                for rel in target_relationships:
                    source_entity = db.query(EntityDBModel).filter(EntityDBModel.id == rel.source_entity_id).first()
                    relationships.append(EntityRelationship(
                        id=rel.id,
                        name=f"{rel.name} (反向)",
                        sourceEntity=source_entity.name if source_entity else rel.source_entity_id,
                        targetEntity=db_entity.name,
                        type=RelationshipType(rel.type),
                        foreignKey=rel.foreign_key,
                        constraints=rel.constraints,
                        created_at=rel.created_at.isoformat() if rel.created_at else "",
                        updated_at=rel.updated_at.isoformat() if rel.updated_at else ""
                    ))

                return {
                    "success": True,
                    "data": {
                        "relationships": relationships,
                        "total": len(relationships)
                    }
                }

        except Exception as e:
            return {
                "success": False,
                "error": "query_failed",
                "details": f"查询实体关系失败: {str(e)}"
            }

    async def create_relationship(self, request) -> Dict[str, Any]:
        """创建实体关系（通用方法）"""
        try:
            with get_db_session() as db:
                # 根据源实体名称查找源实体ID
                source_entity = db.query(EntityDBModel).filter(EntityDBModel.name == request.sourceEntity).first()
                if not source_entity:
                    return {
                        "success": False,
                        "error": "source_entity_not_found",
                        "details": "源实体不存在"
                    }

                # 调用现有的create_entity_relationship方法
                return await self.create_entity_relationship(source_entity.id, request)

        except Exception as e:
            return {
                "success": False,
                "error": "creation_failed",
                "details": f"创建关系失败: {str(e)}"
            }

    async def create_entity_relationship(self, source_entity_id: str, request) -> Dict[str, Any]:
        """创建实体关系"""
        try:
            with get_db_session() as db:
                # 检查源实体是否存在
                source_entity = db.query(EntityDBModel).filter(EntityDBModel.id == source_entity_id).first()
                if not source_entity:
                    return {
                        "success": False,
                        "error": "source_entity_not_found",
                        "details": "源实体不存在"
                    }

                # 检查目标实体是否存在
                target_entity = db.query(EntityDBModel).filter(EntityDBModel.name == request.targetEntity).first()
                if not target_entity:
                    return {
                        "success": False,
                        "error": "target_entity_not_found",
                        "details": "目标实体不存在"
                    }

                # 检查关系是否已存在
                existing_rel = db.query(EntityRelationshipDBModel).filter(
                    and_(
                        EntityRelationshipDBModel.source_entity_id == source_entity_id,
                        EntityRelationshipDBModel.target_entity_id == target_entity.id,
                        EntityRelationshipDBModel.name == request.name
                    )
                ).first()

                if existing_rel:
                    return {
                        "success": False,
                        "error": "relationship_exists",
                        "details": "关系已存在"
                    }

                # 创建关系
                relationship_id = self._generate_id("rel")
                db_relationship = EntityRelationshipDBModel(
                    id=relationship_id,
                    name=request.name,
                    source_entity_id=source_entity_id,
                    target_entity_id=target_entity.id,
                    type=request.type.value,
                    foreign_key=request.foreignKey,
                    constraints=request.constraints.model_dump() if request.constraints else None
                )

                db.add(db_relationship)
                db.commit()

                # 更新数据库表结构以包含新的关系
                try:
                    await self._update_entity_database_relationships(source_entity.name)
                    logger.info(f"✅ 已为实体 '{source_entity.name}' 更新数据库表关系结构")
                except Exception as rel_error:
                    logger.warning(f"⚠️ 更新数据库表关系结构失败: {str(rel_error)}")

                # 构建响应
                relationship = EntityRelationship(
                    id=relationship_id,
                    name=request.name,
                    sourceEntity=source_entity.name,
                    targetEntity=target_entity.name,
                    type=request.type,
                    foreignKey=request.foreignKey,
                    constraints=request.constraints,
                    created_at=db_relationship.created_at.isoformat() if db_relationship.created_at else "",
                    updated_at=db_relationship.updated_at.isoformat() if db_relationship.updated_at else ""
                )

                return {
                    "success": True,
                    "data": {"relationship": relationship}
                }

        except Exception as e:
            return {
                "success": False,
                "error": "creation_failed",
                "details": f"创建关系失败: {str(e)}"
            }

    def delete_entity_relationship(self, entity_id: str, relationship_id: str) -> Dict[str, Any]:
        """删除实体关系"""
        try:
            with get_db_session() as db:
                # 检查关系是否存在
                db_relationship = db.query(EntityRelationshipDBModel).filter(
                    and_(
                        EntityRelationshipDBModel.id == relationship_id,
                        or_(
                            EntityRelationshipDBModel.source_entity_id == entity_id,
                            EntityRelationshipDBModel.target_entity_id == entity_id
                        )
                    )
                ).first()

                if not db_relationship:
                    return {
                        "success": False,
                        "error": "relationship_not_found",
                        "details": "关系不存在"
                    }

                # 删除关系
                relationship_name = db_relationship.name
                db.delete(db_relationship)
                db.commit()

                return {
                    "success": True,
                    "data": {
                        "relationship_id": relationship_id,
                        "name": relationship_name,
                        "deleted_at": time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                    }
                }

        except Exception as e:
            return {
                "success": False,
                "error": "deletion_failed",
                "details": f"删除关系失败: {str(e)}"
            }

    def update_entity_relationship_by_id(self, relationship_id: str, request) -> Dict[str, Any]:
        """根据关系ID更新实体关系"""
        try:
            with get_db_session() as db:
                # 检查关系是否存在
                db_relationship = db.query(EntityRelationshipDBModel).filter(
                    EntityRelationshipDBModel.id == relationship_id
                ).first()

                if not db_relationship:
                    return {
                        "success": False,
                        "error": "relationship_not_found",
                        "details": "关系不存在"
                    }

                # 检查目标实体是否存在
                target_entity = db.query(EntityDBModel).filter(EntityDBModel.name == request.targetEntity).first()
                if not target_entity:
                    return {
                        "success": False,
                        "error": "target_entity_not_found",
                        "details": "目标实体不存在"
                    }

                # 更新关系
                db_relationship.name = request.name
                db_relationship.target_entity_id = target_entity.id
                db_relationship.type = request.type.value
                db_relationship.foreign_key = request.foreignKey
                db_relationship.constraints = request.constraints.model_dump() if request.constraints else None

                db.commit()

                # 构建响应
                source_entity = db.query(EntityDBModel).filter(EntityDBModel.id == db_relationship.source_entity_id).first()
                relationship = EntityRelationship(
                    id=relationship_id,
                    name=request.name,
                    sourceEntity=source_entity.name if source_entity else db_relationship.source_entity_id,
                    targetEntity=target_entity.name,
                    type=request.type,
                    foreignKey=request.foreignKey,
                    constraints=request.constraints,
                    created_at=db_relationship.created_at.isoformat() if db_relationship.created_at else "",
                    updated_at=db_relationship.updated_at.isoformat() if db_relationship.updated_at else ""
                )

                return {
                    "success": True,
                    "data": {"relationship": relationship}
                }

        except Exception as e:
            return {
                "success": False,
                "error": "update_failed",
                "details": f"更新关系失败: {str(e)}"
            }

    def delete_entity_relationship_by_id(self, relationship_id: str) -> Dict[str, Any]:
        """根据关系ID删除实体关系"""
        try:
            with get_db_session() as db:
                # 检查关系是否存在
                db_relationship = db.query(EntityRelationshipDBModel).filter(
                    EntityRelationshipDBModel.id == relationship_id
                ).first()

                if not db_relationship:
                    return {
                        "success": False,
                        "error": "relationship_not_found",
                        "details": "关系不存在"
                    }

                # 删除关系
                relationship_name = db_relationship.name
                db.delete(db_relationship)
                db.commit()

                return {
                    "success": True,
                    "data": {
                        "relationship_id": relationship_id,
                        "name": relationship_name,
                        "deleted_at": time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                    }
                }

        except Exception as e:
            return {
                "success": False,
                "error": "deletion_failed",
                "details": f"删除关系失败: {str(e)}"
            }
    
    def _create_entity_database_table_sync(self, entity_name: str, fields: List, db: Session) -> None:
        """为实体自动创建MySQL数据库表（同步版本）"""
        from sqlalchemy import text

        table_name = f"entity_{self._safe_table_name(entity_name)}"

        # 检查表是否已存在 (MySQL语法)
        check_table_query = text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = DATABASE() AND table_name = :table_name
        """)
        table_exists = db.execute(check_table_query, {"table_name": table_name}).fetchone()

        if table_exists:
            logger.warning(f"⚠️ 表 {table_name} 已存在，跳过创建")
            return

        # 构建表结构 (MySQL语法)
        columns = [
            "id VARCHAR(36) PRIMARY KEY DEFAULT (UUID())",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        ]

        foreign_keys = []
        indexes = []

        # 添加业务字段
        for field in fields:
            field_name = self._safe_column_name(field.name)
            field_type = field.type.value if hasattr(field.type, 'value') else str(field.type)

            # 映射字段类型到MySQL类型
            sql_type = self._map_field_type_to_mysql(field_type)

            constraints = []
            if field.required:
                constraints.append("NOT NULL")
            if field.unique:
                constraints.append("UNIQUE")
            if hasattr(field, 'defaultValue') and field.defaultValue:
                escaped_default = self._escape_sql_literal(field.defaultValue)
                constraints.append(f"DEFAULT '{escaped_default}'")

            constraint_str = " ".join(constraints)
            column_def = f"`{field_name}` {sql_type} {constraint_str}".strip()
            columns.append(column_def)

        # 添加外键约束
        if foreign_keys:
            columns.extend(foreign_keys)

        # 创建表 (MySQL语法，添加字符集和引擎)
        create_table_sql = f"""
            CREATE TABLE `{table_name}` (
                {', '.join(columns)}
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        try:
            # 创建表
            db.execute(text(create_table_sql))

            # 创建索引
            for index_sql in indexes:
                try:
                    db.execute(text(index_sql))
                except Exception as idx_error:
                    logger.warning(f"⚠️ 创建索引失败: {str(idx_error)}")

            db.commit()
            logger.info(f"✅ 成功创建MySQL实体表: {table_name}")
            logger.debug(f"   表结构: {', '.join(columns[:3])} + {len(columns)-3} 个字段列")
            if foreign_keys:
                logger.debug(f"   外键关系: {len(foreign_keys)} 个")
            if indexes:
                logger.debug(f"   索引: {len(indexes)} 个")
        except Exception as e:
            logger.error(f"❌ 创建MySQL表 {table_name} 失败: {str(e)}")
            raise e

    async def _create_entity_database_table(self, entity_name: str, fields: List, db: Session) -> None:
        """为实体自动创建MySQL数据库表"""
        # 调用同步版本
        self._create_entity_database_table_sync(entity_name, fields, db)

    def _map_field_type_to_mysql(self, field_type: str) -> str:
        """映射字段类型到MySQL类型"""
        type_mapping = {
            "text": "VARCHAR(255)",
            "string": "VARCHAR(255)",
            "number": "INT",
            "integer": "INT",
            "decimal": "DECIMAL(10,2)",
            "float": "FLOAT",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "datetime": "DATETIME",
            "timestamp": "TIMESTAMP",
            "json": "JSON",
            "enum": "VARCHAR(50)",
            "select": "VARCHAR(100)",
            "email": "VARCHAR(255)",
            "phone": "VARCHAR(20)",
            "url": "VARCHAR(500)"
        }
        return type_mapping.get(field_type.lower(), "VARCHAR(255)")
    
    async def _update_entity_database_relationships(self, entity_name: str) -> None:
        """更新实体数据库表的关系结构"""
        try:
            with get_db_session() as db:
                # 获取实体及其关系
                entity = db.query(EntityDBModel).filter(EntityDBModel.name == entity_name).first()
                if not entity:
                    return
                
                # 获取该实体作为源实体的所有关系
                relationships = db.query(EntityRelationshipDBModel).filter(
                    EntityRelationshipDBModel.source_entity_id == entity.id
                ).all()
                
                if not relationships:
                    return
                
                table_name = f"entity_{self._safe_table_name(entity_name)}"
                
                # 为每个关系添加外键列（如果不存在）
                for rel in relationships:
                    target_entity = db.query(EntityDBModel).filter(
                        EntityDBModel.id == rel.target_entity_id
                    ).first()
                    
                    if not target_entity:
                        continue
                    
                    foreign_key_column = self._safe_column_name(
                        rel.foreign_key or f"{target_entity.name.lower()}_id"
                    )
                    
                    # 检查列是否存在
                    from sqlalchemy import text
                    check_column_sql = text("""
                        SELECT COLUMN_NAME
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME = :table_name
                          AND COLUMN_NAME = :column_name
                    """)
                    column_exists = db.execute(
                        check_column_sql,
                        {"table_name": table_name, "column_name": foreign_key_column}
                    ).fetchone() is not None

                    if not column_exists:
                        # 添加外键列
                        try:
                            alter_table_sql = text(f"""
                                ALTER TABLE `{table_name}` 
                                ADD COLUMN `{foreign_key_column}` TEXT
                            """)
                            db.execute(alter_table_sql)
                            
                            # 创建索引
                            safe_index_name = self._safe_table_name(
                                f"idx_{table_name}_{foreign_key_column}"
                            )[:64]
                            index_sql = text(f"""
                                CREATE INDEX `{safe_index_name}` 
                                ON `{table_name}`(`{foreign_key_column}`)
                            """)
                            db.execute(index_sql)
                            
                            logger.info(f"✅ 为表 {table_name} 添加外键列: {foreign_key_column}")
                            
                        except Exception as alter_error:
                            logger.warning(f"⚠️ 添加外键列失败: {str(alter_error)}")
                
                db.commit()
                
        except Exception as e:
            logger.error(f"❌ 更新实体关系结构失败: {str(e)}")
            raise e

    def _safe_table_name(self, name: str) -> str:
        """
        生成安全的表名
        移除特殊字符，转换为小写，适合MySQL表名
        """
        import re
        # 移除特殊字符，只保留字母、数字和下划线
        safe_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', name)
        # 转换为小写 (对于中文保持原样)
        return safe_name.lower()

    def _safe_column_name(self, name: str) -> str:
        """生成安全的列名，避免DDL/DML标识符注入。"""
        raw = str(name or "").strip()
        safe_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', raw)
        safe_name = re.sub(r'_+', '_', safe_name).strip('_')
        if not safe_name:
            raise ValueError("列名不能为空")
        if safe_name[0].isdigit():
            safe_name = f"f_{safe_name}"
        return safe_name.lower()

    def _escape_sql_literal(self, value: Any) -> str:
        """转义SQL字符串字面量内容。"""
        return str(value).replace("'", "''")
    
    def _drop_entity_database_table(self, db: Session, table_name: str) -> None:
        """
        删除实体对应的MySQL数据表
        """
        from sqlalchemy import text
        
        try:
            # 检查表是否存在 (MySQL语法)
            check_table_query = text(f"""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = DATABASE() AND table_name = '{table_name}'
            """)
            table_exists = db.execute(check_table_query).fetchone()
            
            if not table_exists:
                logger.info(f"表 {table_name} 不存在，无需删除")
                return
            
            # 先删除相关的外键约束 (如果有的话)
            try:
                # 获取外键约束信息
                fk_query = text(f"""
                    SELECT CONSTRAINT_NAME 
                    FROM information_schema.KEY_COLUMN_USAGE 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = '{table_name}' 
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """)
                foreign_keys = db.execute(fk_query).fetchall()
                
                # 删除外键约束
                for fk in foreign_keys:
                    drop_fk_sql = text(f"ALTER TABLE {table_name} DROP FOREIGN KEY {fk[0]}")
                    db.execute(drop_fk_sql)
                    logger.info(f"删除外键约束: {fk[0]}")
                    
            except Exception as fk_error:
                logger.warning(f"删除外键约束时出错: {fk_error}")
                # 继续执行，不因为外键删除失败而中断
            
            # 删除表
            drop_table_sql = text(f"DROP TABLE IF EXISTS {table_name}")
            db.execute(drop_table_sql)
            db.commit()
            
            logger.info(f"成功删除数据表: {table_name}")
            
        except Exception as e:
            logger.error(f"删除数据表失败 {table_name}: {str(e)}")
            raise e


# 全局实体服务实例
entity_service = EntityService()
