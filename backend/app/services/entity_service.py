"""
实体建模服务
处理实体定义、字段、关系和数据记录的业务逻辑
"""
import json
import time
import re
from datetime import datetime, date, timezone
from app.core.logging_config import get_logger
from app.core.utils import generate_id
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, case, Column, DateTime, MetaData, String, Table, func, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateColumn
from app.services.entity_storage import (
    decode_record, default_value, field_type, normalize_field_value,
    serialize_default, sql_default, sql_field_type, sql_type_signature, storage_value,
)
import hashlib
import uuid
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
        if include_fields:
            entity_data["fields"] = [
                EntityField(
                    id=field.id,
                    name=field.name,
                    displayName=field.display_name,
                    type=FieldType(field.type),
                    required=field.required,
                    unique=field.unique_field,
                    defaultValue=default_value(field),
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
        table_created = False
        table_name = f"entity_{self._safe_table_name(request.name)}"
        try:
            with get_db_session() as db:
                if db.query(EntityDBModel).filter(EntityDBModel.name == request.name).first():
                    return {"success": False, "error": "duplicate_entity_name", "details": "实体名称已存在"}
                if self._table_exists(db, table_name):
                    raise ValueError("同名实体数据表已存在，请先核对实体配置")
                # MySQL DDL 会隐式提交；必须先建物理表，再写配置，避免保存出不存在的表。
                await self._create_entity_database_table(request.name, request.fields, db)
                table_created = True
                entity_id = self._generate_id("entity")
                record = EntityDBModel(
                    id=entity_id, name=request.name, display_name=request.displayName,
                    description=request.description, icon=request.icon, status="active",
                    is_role=request.isRole or False, field_count=len(request.fields), record_count=0,
                )
                db.add(record)
                db.flush()
                for index, field in enumerate(request.fields):
                    db.add(EntityFieldDBModel(
                        id=self._generate_id("field"), entity_id=entity_id, name=field.name,
                        display_name=field.displayName, type=field.type.value,
                        required=field.required, unique_field=field.unique,
                        default_value=serialize_default(field.defaultValue),
                        validation=field.validation.model_dump(exclude_none=True) if field.validation else None,
                        options=field.options, aliases=field.aliases, sort_order=index,
                    ))
                db.flush()
                entity = self._convert_db_entity_to_schema(record, include_fields=True)
                if request.isRole:
                    from app.services.dynamic_user_service import DynamicUserService
                    DynamicUserService().sync_entity_roles(db=db, role_entities=[entity])
                self._field_label_cache.clear()
                self._field_label_cache_ts.clear()
                return {"success": True, "data": {"entity": entity}}
        except Exception as exc:
            if table_created:
                # 仅清理由本次调用创建、尚无定义和记录的空表，不能误删已有业务数据。
                try:
                    with get_db_session() as cleanup_db:
                        registered = cleanup_db.query(EntityDBModel).filter(EntityDBModel.name == request.name).first()
                        if registered is None and self._table_exists(cleanup_db, table_name):
                            count = cleanup_db.execute(text(f"SELECT COUNT(*) FROM `{table_name}`")).scalar()
                            if count == 0:
                                Table(table_name, MetaData()).drop(cleanup_db.connection())
                except Exception:
                    logger.exception("新实体空表清理失败")
            logger.exception("创建实体失败")
            return {"success": False, "error": "creation_failed", "details": f"创建实体失败: {exc}"}

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

    async def update_entity(self, entity_id, request: EntityUpdateRequest):
        """先验证并修改物理表，再保存配置；同名字段保留原 ID，失败时不返回成功。"""
        try:
            with get_db_session() as db:
                record = db.query(EntityDBModel).filter(
                    EntityDBModel.id == entity_id
                ).with_for_update().first()
                if record is None:
                    return {"success": False, "error": "entity_not_found", "details": "实体不存在"}
                if request.fields is not None:
                    # 先校验并变更物理表；DDL 失败时，ORM 中的字段定义仍保持原样。
                    await self._alter_entity_database_table(record.name, request.fields, db)
                    current = {field.name.lower(): field for field in record.fields}
                    retained = set()
                    for index, field in enumerate(request.fields):
                        existing = current.get(field.name.lower())
                        if existing is None:
                            existing = EntityFieldDBModel(id=self._generate_id("field"), entity_id=entity_id)
                            db.add(existing)
                        retained.add(existing.id)
                        existing.name = field.name
                        existing.display_name = field.displayName
                        existing.type = field.type.value
                        existing.required = field.required
                        existing.unique_field = field.unique
                        existing.default_value = serialize_default(field.defaultValue)
                        existing.validation = field.validation.model_dump(exclude_none=True) if field.validation else None
                        existing.options = field.options
                        existing.aliases = field.aliases
                        existing.sort_order = index
                    for field in current.values():
                        if field.id not in retained:
                            db.delete(field)
                    record.field_count = len(request.fields)
                changes = request.model_dump(exclude_unset=True)
                for key, column in (("displayName", "display_name"), ("description", "description"),
                                    ("icon", "icon"), ("isRole", "is_role")):
                    if key in changes:
                        setattr(record, column, changes[key])
                db.flush()
                db.expire(record, ["fields"])
                entity = self._convert_db_entity_to_schema(record, include_fields=True)
                self._field_label_cache.clear()
                self._field_label_cache_ts.clear()
                return {"success": True, "data": {"entity": entity}}
        except Exception as exc:
            logger.exception("更新实体失败")
            return {"success": False, "error": "update_failed", "details": f"更新实体失败: {exc}"}

    @staticmethod
    def _table_exists(db, table_name):
        """通过当前事务的连接检查表是否存在，避免额外连接读取旧结构。"""
        return inspect(db.connection()).has_table(table_name)

    def _column_definition(self, field, dialect, *, unique=False):
        """建表和改表共用列定义，必填、默认值和类型保持一致。"""
        name = self._safe_column_name(field.name)
        default = sql_default(field, dialect)
        return Column(
            name, sql_field_type(field), nullable=not field.required,
            unique=unique, server_default=text(default) if default is not None else None,
        )

    async def _alter_entity_database_table(self, entity_name, fields, db):
        """先规划全部 DDL，再统一执行；有记录的列不自动转换或收窄类型。"""
        table_name = f"entity_{self._safe_table_name(entity_name)}"
        if not self._table_exists(db, table_name):
            await self._create_entity_database_table(entity_name, fields, db)
            return
        inspector = inspect(db.connection())
        columns = {column["name"].lower(): column for column in inspector.get_columns(table_name)}
        definition = db.query(EntityDBModel).filter(EntityDBModel.name == entity_name).first()
        previous = {field.name.lower(): field for field in definition.fields} if definition else {}
        count = db.execute(text(f"SELECT COUNT(*) FROM `{table_name}`")).scalar()
        dialect = db.bind.dialect
        changes = []
        # MySQL 会在两个接口中返回同一个唯一索引，按名称去重后才能安全删除。
        indexes = list({item.get("name") or tuple(item.get("column_names") or []): item for item in
                        inspector.get_indexes(table_name) + inspector.get_unique_constraints(table_name)}.values())
        requested_names = {field.name.lower() for field in fields}
        for name, old in previous.items():
            if name not in requested_names and old.required and not columns.get(name, {}).get("nullable", True):
                # 移除字段只从定义中隐藏，不删历史数据；释放 NOT NULL 后新记录才能正常创建。
                if dialect.name == "sqlite":
                    raise ValueError("SQLite 回归数据库不支持修改已有列的必填约束")
                from types import SimpleNamespace
                retained = SimpleNamespace(
                    name=old.name, type=old.type, required=False, default_value=old.default_value,
                    validation=old.validation, options=old.options,
                )
                changes.append("MODIFY COLUMN " + str(CreateColumn(
                    self._column_definition(retained, dialect)
                ).compile(dialect=dialect)))
        for field in fields:
            name = self._safe_column_name(field.name)
            old = previous.get(field.name.lower())
            new_column = self._column_definition(field, dialect)
            if name not in columns:
                if count and field.required and field.defaultValue is None:
                    raise ValueError(f"已有记录时添加必填字段 {field.name} 需要默认值")
                changes.append("ADD COLUMN " + str(CreateColumn(new_column).compile(dialect=dialect)))
            elif old is None:
                # 已移除字段的物理列仍在，重新加入时必须与真实列核对，不能仅恢复元数据。
                physical = columns[name]
                same_type = sql_type_signature(physical["type"], dialect) == sql_type_signature(new_column.type, dialect)
                if count and not same_type:
                    raise ValueError(f"字段 {field.name} 已有数据，不能自动转换或收窄类型")
                if field.required and count:
                    nulls = db.execute(text(f"SELECT COUNT(*) FROM `{table_name}` WHERE `{name}` IS NULL")).scalar()
                    if nulls:
                        raise ValueError(f"字段 {field.name} 存在空值，请先补齐记录")
                if dialect.name == "sqlite":
                    if (not same_type or physical["nullable"] == field.required
                            or physical.get("default") != sql_default(field, dialect)):
                        raise ValueError("SQLite 回归数据库不支持修改已有列定义")
                else:
                    changes.append("MODIFY COLUMN " + str(CreateColumn(new_column).compile(dialect=dialect)))
            elif old is not None:
                old_default = serialize_default(default_value(old))
                old_type = str(sql_field_type(old).compile(dialect=dialect))
                new_type = str(sql_field_type(field).compile(dialect=dialect))
                # 小数位数也改变物理列类型，不能只比较字段类型名称。
                changed = (
                    field_type(old) != field_type(field) or bool(old.required) != field.required
                    or old_default != serialize_default(field.defaultValue) or old_type != new_type
                )
                if changed and count and old_type != new_type:
                    raise ValueError(f"字段 {field.name} 已有数据，不能自动转换或收窄类型")
                if field.required and count:
                    nulls = db.execute(text(f"SELECT COUNT(*) FROM `{table_name}` WHERE `{name}` IS NULL")).scalar()
                    if nulls:
                        raise ValueError(f"字段 {field.name} 存在空值，请先补齐记录")
                if changed:
                    if dialect.name == "sqlite":
                        raise ValueError("SQLite 回归数据库不支持修改已有列定义")
                    changes.append("MODIFY COLUMN " + str(CreateColumn(new_column).compile(dialect=dialect)))
            existing_unique = [
                item for item in indexes if item.get("unique", True)
                and [value.lower() for value in item.get("column_names") or []] == [name]
            ]
            if field.unique and not existing_unique:
                index_name = "uq_" + hashlib.sha256(f"{table_name}:{name}".encode()).hexdigest()[:20]
                if dialect.name == "sqlite":
                    changes.append(f"CREATE UNIQUE INDEX `{index_name}` ON `{table_name}` (`{name}`)")
                else:
                    changes.append(f"ADD UNIQUE INDEX `{index_name}` (`{name}`)")
            elif not field.unique:
                for item in existing_unique:
                    if item.get("name"):
                        index_name = self._safe_column_name(item["name"])
                        if dialect.name == "sqlite":
                            raise ValueError("SQLite 回归数据库不支持删除列内唯一约束")
                        changes.append(f"DROP INDEX `{index_name}`")
        if changes:
            if dialect.name == "sqlite":
                for change in changes:
                    statement = change if change.startswith("CREATE UNIQUE INDEX") else f"ALTER TABLE `{table_name}` {change}"
                    db.execute(text(statement))
            else:
                # MySQL 8 用一条 ALTER 应用列和索引变更；成功后才更新 ORM 中的实体定义。
                db.execute(text(f"ALTER TABLE `{table_name}` " + ", ".join(changes)))

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
                          sort_by: Optional[str] = None, sort_order: str = "desc",
                          lock_for_update: bool = False) -> Dict[str, Any]:
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
                table_exists = self._table_exists(db, table_name)
                
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
                                # 忽略条件会把“查询指定记录”变成“取第一条”，支付和通知会误操作他人记录。
                                return {"success": False, "error": "invalid_filter", "details": f"未知过滤字段: {field_name}"}
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
                # MySQL 在事务中锁定业务记录，重复支付请求会在锁后重新读取最新状态。
                lock_sql = " FOR UPDATE" if lock_for_update and db.bind.dialect.name == "mysql" else ""
                query_sql = text(f"SELECT * FROM `{table_name}` {where_sql} {order_sql} LIMIT :limit OFFSET :offset{lock_sql}")
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
                    record_data = decode_record(record_data, db_entity.fields)
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

    def _prepare_record_data(self, entity, data, *, partial=False):
        """统一处理别名、默认值和类型；局部更新只处理明确提交的字段。"""
        if not isinstance(data, dict):
            raise ValueError("记录数据必须是对象")
        aliases = {}
        for field in entity.fields:
            for alias in field.aliases or []:
                aliases[alias] = field.name
        prepared = {aliases.get(key, key): value for key, value in data.items()}
        for field in entity.fields:
            if field.name in prepared:
                prepared[field.name] = normalize_field_value(field, prepared[field.name])
            elif not partial and field.default_value is not None:
                prepared[field.name] = default_value(field)
        return prepared

    def create_entity_record(self, entity_id, data):
        """校验并写入业务表，在同一事务中原子增加记录计数。"""
        try:
            with get_db_session() as db:
                entity = db.get(EntityDBModel, entity_id)
                if entity is None:
                    return {"success": False, "error": "entity_not_found", "details": "实体不存在"}
                table_name = f"entity_{self._safe_table_name(entity.name)}"
                if not self._table_exists(db, table_name):
                    return {"success": False, "error": "table_not_found", "details": "实体数据表不存在，请在配置中保存实体"}
                prepared = self._prepare_record_data(entity, data)
                validation = self._validate_record_data(entity, prepared, db=db)
                if not validation["valid"]:
                    return {"success": False, "error": "validation_failed", "details": validation["errors"]}
                record_id = str(uuid.uuid4())
                columns, values, parameters = ["id"], [":id"], {"id": record_id}
                for index, field in enumerate(entity.fields):
                    if field.name in prepared:
                        name = self._safe_column_name(field.name)
                        parameter = f"value_{index}"
                        columns.append(f"`{name}`")
                        values.append(f":{parameter}")
                        parameters[parameter] = storage_value(field, prepared[field.name])
                db.execute(text(
                    f"INSERT INTO `{table_name}` ({', '.join(columns)}) VALUES ({', '.join(values)})"
                ), parameters)
                db.query(EntityDBModel).filter(EntityDBModel.id == entity_id).update({
                    EntityDBModel.record_count: func.coalesce(EntityDBModel.record_count, 0) + 1
                }, synchronize_session=False)
                row = db.execute(text(f"SELECT * FROM `{table_name}` WHERE id = :id"), {"id": record_id}).mappings().one()
                return {"success": True, "data": {"record": decode_record(row, entity.fields)}}
        except (ValueError, TypeError, IntegrityError) as exc:
            return {"success": False, "error": "validation_failed", "details": str(exc)}
        except Exception as exc:
            logger.exception("创建实体记录失败")
            return {"success": False, "error": "creation_failed", "details": str(exc)}

    def update_entity_record(self, entity_id, record_id, data):
        """局部更新与创建共用转换规则，唯一性检查排除当前记录。"""
        try:
            with get_db_session() as db:
                entity = db.get(EntityDBModel, entity_id)
                if entity is None:
                    return {"success": False, "error": "entity_not_found", "details": "实体不存在"}
                table_name = f"entity_{self._safe_table_name(entity.name)}"
                if not self._table_exists(db, table_name):
                    return {"success": False, "error": "table_not_found", "details": "实体数据表不存在"}
                exists = db.execute(text(f"SELECT id FROM `{table_name}` WHERE id = :id"), {"id": record_id}).first()
                if exists is None:
                    return {"success": False, "error": "record_not_found", "details": "记录不存在"}
                prepared = self._prepare_record_data(entity, data, partial=True)
                validation = self._validate_record_data(entity, prepared, record_id, partial=True, db=db)
                if not validation["valid"]:
                    return {"success": False, "error": "validation_failed", "details": validation["errors"]}
                assignments, parameters = [], {"id": record_id, "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}
                for index, field in enumerate(entity.fields):
                    if field.name in prepared:
                        parameter = f"value_{index}"
                        assignments.append(f"`{self._safe_column_name(field.name)}` = :{parameter}")
                        parameters[parameter] = storage_value(field, prepared[field.name])
                if not assignments:
                    return {"success": False, "error": "no_data", "details": "没有要更新的数据"}
                assignments.append("updated_at = :updated_at")
                db.execute(text(
                    f"UPDATE `{table_name}` SET {', '.join(assignments)} WHERE id = :id"
                ), parameters)
                row = db.execute(text(f"SELECT * FROM `{table_name}` WHERE id = :id"), {"id": record_id}).mappings().one()
                return {"success": True, "data": {"record": decode_record(row, entity.fields)}}
        except (ValueError, TypeError, IntegrityError) as exc:
            return {"success": False, "error": "validation_failed", "details": str(exc)}
        except Exception as exc:
            logger.exception("更新实体记录失败")
            return {"success": False, "error": "update_failed", "details": str(exc)}

    def delete_entity_record(self, entity_id, record_id):
        """删除成功才减少计数，避免不存在的记录导致数量错误。"""
        try:
            with get_db_session() as db:
                entity = db.get(EntityDBModel, entity_id)
                if entity is None:
                    return {"success": False, "error": "entity_not_found", "details": "实体不存在"}
                table_name = f"entity_{self._safe_table_name(entity.name)}"
                if not self._table_exists(db, table_name):
                    return {"success": False, "error": "table_not_found", "details": "实体数据表不存在"}
                deleted = db.execute(text(f"DELETE FROM `{table_name}` WHERE id = :id"), {"id": record_id}).rowcount
                if deleted == 0:
                    return {"success": False, "error": "record_not_found", "details": "记录不存在"}
                db.query(EntityDBModel).filter(EntityDBModel.id == entity_id).update({
                    EntityDBModel.record_count: case(
                        (EntityDBModel.record_count > 0, EntityDBModel.record_count - 1), else_=0
                    )
                }, synchronize_session=False)
                return {"success": True, "data": {"deleted_record_id": record_id}}
        except Exception as exc:
            logger.exception("删除实体记录失败")
            return {"success": False, "error": "deletion_failed", "details": str(exc)}

    def _validate_record_data(self, entity, data, exclude_record_id=None, *, partial=False, db=None):
        """复用当前事务检查必填、规则与唯一性，避免新连接看不到尚未提交的写入。"""
        if db is None:
            with get_db_session() as validation_db:
                return self._validate_record_data(
                    entity, data, exclude_record_id, partial=partial, db=validation_db
                )
        errors = []
        table_name = f"entity_{self._safe_table_name(entity.name)}"
        for field in entity.fields:
            if partial and field.name not in data:
                continue
            value = data.get(field.name)
            if field.required and value in (None, "", []):
                errors.append(f"字段 '{field.display_name}' 是必填的")
                continue
            if value is None:
                continue
            rules = field.validation or {}
            try:
                for key, check in (
                    ("min", lambda bound: value >= bound), ("max", lambda bound: value <= bound),
                    ("minLength", lambda bound: len(value) >= bound),
                    ("maxLength", lambda bound: len(value) <= bound),
                    ("pattern", lambda pattern: re.fullmatch(pattern, str(value)) is not None),
                ):
                    if rules.get(key) is not None and not check(rules[key]):
                        errors.append(f"字段 '{field.display_name}' 不满足 {key} 约束")
            except (TypeError, ValueError):
                errors.append(f"字段 '{field.display_name}' 的验证规则与数据类型不匹配")
            if field.unique_field and field.name in data:
                sql = f"SELECT COUNT(*) FROM `{table_name}` WHERE `{self._safe_column_name(field.name)}` = :value"
                parameters = {"value": storage_value(field, value)}
                if exclude_record_id is not None:
                    sql += " AND id != :exclude_id"
                    parameters["exclude_id"] = exclude_record_id
                if db.execute(text(sql), parameters).scalar():
                    errors.append(f"字段 '{field.display_name}' 的值必须唯一")
        return {"valid": not errors, "errors": errors}

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
    
    def _create_entity_database_table_sync(self, entity_name, fields, db):
        """使用明确的 SQL 类型和系统列建表，DDL 失败交给调用方回滚配置。"""
        table_name = f"entity_{self._safe_table_name(entity_name)}"
        if self._table_exists(db, table_name):
            raise ValueError("实体数据表已存在")
        dialect = db.bind.dialect
        columns = [
            Column("id", String(36), primary_key=True,
                   server_default=text("(UUID())") if dialect.name == "mysql" else None),
            Column("created_at", DateTime(), server_default=func.current_timestamp()),
            Column("updated_at", DateTime(), server_default=text(
                "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP" if dialect.name == "mysql" else "CURRENT_TIMESTAMP"
            )),
        ]
        columns.extend(self._column_definition(field, dialect, unique=field.unique) for field in fields)
        table = Table(
            table_name, MetaData(), *columns, mysql_engine="InnoDB",
            mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci",
        )
        table.create(db.connection())

    async def _create_entity_database_table(self, entity_name, fields, db):
        self._create_entity_database_table_sync(entity_name, fields, db)

    def _map_field_type_to_mysql(self, field_type):
        from sqlalchemy.dialects.mysql import dialect
        field = type("Field", (), {"type": field_type, "validation": {}})()
        return str(sql_field_type(field).compile(dialect=dialect()))

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
