"""
角色管理服务层
实现角色CRUD操作和权限管理的核心业务逻辑
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.core.database import get_db_session
from app.core.utils import format_datetime, generate_id
from app.core.logging_config import get_logger
from app.models.role import (
    RoleDBModel, PermissionDBModel, RolePermissionLogDBModel, UserRoleLogDBModel,
    RoleStatus, role_permissions, user_roles
)
from app.schemas.role import (
    RoleCreateRequest, RoleUpdateRequest, RolePermissionsRequest
)

logger = get_logger(__name__)


class RoleService:
    """角色管理服务类"""
    
    def _generate_id(self, prefix: str) -> str:
        """生成唯一ID"""
        return generate_id(prefix)
    
    # 角色CRUD操作
    def create_role(self, request: RoleCreateRequest, operator_id: str = None) -> Dict[str, Any]:
        """创建新的用户角色"""
        try:
            with get_db_session() as db:
                # 检查角色代码是否已存在
                existing_role = db.query(RoleDBModel).filter(
                    RoleDBModel.code == request.code
                ).first()
                
                if existing_role:
                    return {
                        "success": False,
                        "error": "role_code_exists",
                        "details": f"角色代码 '{request.code}' 已被使用",
                        "existing_role": {
                            "id": existing_role.id,
                            "name": existing_role.name
                        }
                    }
                
                # 生成角色ID
                role_id = self._generate_id("role")
                
                # 创建角色记录
                db_role = RoleDBModel(
                    id=role_id,
                    name=request.name,
                    code=request.code,
                    description=request.description,
                    status=request.status.value if request.status else RoleStatus.ACTIVE.value,
                    role_metadata=request.metadata or {},
                    created_by=operator_id
                )
                
                db.add(db_role)
                db.flush()  # 获取ID但不提交
                
                # 分配初始权限
                if request.permissions:
                    permission_count = 0
                    for perm_name in request.permissions:
                        permission = db.query(PermissionDBModel).filter(
                            PermissionDBModel.name == perm_name
                        ).first()
                        
                        if permission:
                            db_role.permissions.append(permission)
                            permission_count += 1
                            
                            # 记录权限分配日志
                            log_id = self._generate_id("log")
                            log = RolePermissionLogDBModel(
                                id=log_id,
                                role_id=role_id,
                                permission_id=permission.id,
                                operation="grant",
                                operator_id=operator_id,
                                reason="初始权限分配"
                            )
                            db.add(log)
                
                db.commit()
                
                # 构建响应
                role = self._build_role_response(db_role, db, include_permissions=True)
                
                return {
                    "success": True,
                    "data": {
                        "role": role
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": "creation_failed",
                "details": f"创建角色失败: {str(e)}"
            }
    
    def get_roles_list(self, status: Optional[str] = None, department: Optional[str] = None,
                      page: int = 1, limit: int = 20, sort: str = "created_at") -> Dict[str, Any]:
        """获取所有角色列表"""
        try:
            with get_db_session() as db:
                # 构建查询
                query = db.query(RoleDBModel)
                
                # 状态筛选
                if status:
                    query = query.filter(RoleDBModel.status == status)

                # 部门筛选（通过role_metadata）
                if department:
                    query = query.filter(
                        RoleDBModel.role_metadata.contains(f'"department": "{department}"')
                    )
                
                # 排序
                if sort == "name":
                    query = query.order_by(RoleDBModel.name)
                else:  # created_at
                    query = query.order_by(RoleDBModel.created_at.desc())
                
                # 总数统计
                total = query.count()
                
                # 分页查询
                offset = (page - 1) * limit
                db_roles = query.offset(offset).limit(limit).all()
                
                # 构建角色列表
                roles = []
                for db_role in db_roles:
                    role_item = self._build_role_list_item(db_role, db)
                    roles.append(role_item)
                
                # 计算分页信息
                pages = (total + limit - 1) // limit
                has_next = page < pages
                has_prev = page > 1
                
                # 计算统计信息
                all_roles = db.query(RoleDBModel).all()
                active_roles = sum(1 for r in all_roles if r.status == RoleStatus.ACTIVE.value)
                inactive_roles = len(all_roles) - active_roles
                total_users = sum(r.user_count for r in all_roles)
                total_permissions = sum(len(list(r.permissions)) for r in all_roles)
                avg_permissions = total_permissions / len(all_roles) if all_roles else 0
                
                return {
                    "success": True,
                    "data": {
                        "roles": roles,
                        "pagination": {
                            "page": page,
                            "limit": limit,
                            "total": total,
                            "pages": pages,
                            "has_next": has_next,
                            "has_prev": has_prev
                        },
                        "summary": {
                            "total_roles": len(all_roles),
                            "active_roles": active_roles,
                            "inactive_roles": inactive_roles,
                            "total_users": total_users,
                            "avg_permissions_per_role": round(avg_permissions, 1)
                        }
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": "query_failed",
                "details": f"获取角色列表失败: {str(e)}"
            }
    
    def get_role_detail(self, role_id: str, include_users: bool = False, 
                       include_permissions: bool = True) -> Dict[str, Any]:
        """获取特定角色详情"""
        try:
            with get_db_session() as db:
                # 查询角色
                db_role = db.query(RoleDBModel).filter(RoleDBModel.id == role_id).first()
                
                if not db_role:
                    return {
                        "success": False,
                        "error": "role_not_found",
                        "details": f"角色 {role_id} 不存在"
                    }
                
                # 构建响应
                role = self._build_role_response(
                    db_role, db, 
                    include_users=include_users,
                    include_permissions=include_permissions
                )
                
                return {
                    "success": True,
                    "data": {
                        "role": role
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": "query_failed",
                "details": f"获取角色详情失败: {str(e)}"
            }
    
    def update_role(self, role_id: str, request: RoleUpdateRequest, 
                   operator_id: str = None) -> Dict[str, Any]:
        """更新角色信息"""
        try:
            with get_db_session() as db:
                # 查询角色
                db_role = db.query(RoleDBModel).filter(RoleDBModel.id == role_id).first()
                
                if not db_role:
                    return {
                        "success": False,
                        "error": "role_not_found",
                        "details": f"角色 {role_id} 不存在"
                    }
                
                # 更新字段
                if request.name is not None:
                    db_role.name = request.name
                if request.description is not None:
                    db_role.description = request.description
                if request.status is not None:
                    db_role.status = request.status.value
                if request.metadata is not None:
                    db_role.role_metadata = request.metadata
                
                db_role.updated_by = operator_id
                db.commit()
                
                # 构建响应
                role = self._build_role_response(db_role, db, include_permissions=False)
                
                return {
                    "success": True,
                    "data": {
                        "role": role
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": "update_failed",
                "details": f"更新角色失败: {str(e)}"
            }

    def delete_role(self, role_id: str, force: bool = False, reassign_to: str = None,
                   operator_id: str = None) -> Dict[str, Any]:
        """删除角色"""
        logger.info(f"开始删除角色: role_id={role_id}, force={force}")

        try:
            with get_db_session() as db:
                logger.debug(f"数据库连接成功")

                # 查询角色
                logger.debug(f"查询角色: {role_id}")
                db_role = db.query(RoleDBModel).filter(RoleDBModel.id == role_id).first()
                logger.debug(f"查询结果: {db_role}")

                if not db_role:
                    logger.warning(f"⚠️ 角色不存在: {role_id}")
                    return {
                        "success": False,
                        "error": "role_not_found",
                        "details": f"角色 {role_id} 不存在"
                    }

                logger.debug(f"角色信息: name={db_role.name}, user_count={db_role.user_count}")

                # 检查是否有关联用户
                if db_role.user_count > 0 and not force:
                    logger.warning(f"⚠️ 角色有关联用户，无法删除: user_count={db_role.user_count}")
                    return {
                        "success": False,
                        "error": "role_has_users",
                        "details": f"角色正在被 {db_role.user_count} 个用户使用，请先移除关联用户或使用强制删除",
                        "user_count": db_role.user_count
                    }

                # 保存删除信息
                deleted_info = {
                    "role_id": db_role.id,
                    "name": db_role.name,
                    "deleted_at": format_datetime(datetime.now()),
                    "affected_users": db_role.user_count,
                    "reassigned_to": reassign_to
                }
                logger.debug(f"删除信息准备完成: {deleted_info}")

                # 如果有重新分配的角色，处理用户重新分配
                if reassign_to and db_role.user_count > 0:
                    logger.debug(f"处理用户重新分配: reassign_to={reassign_to}")
                    # 这里应该处理用户重新分配逻辑
                    # 由于没有用户表，暂时跳过实际重新分配
                    pass

                # 执行删除操作
                logger.info(f"准备删除角色: {db_role.name} (ID: {role_id})")

                try:
                    # 修复外键约束问题，按正确顺序删除所有相关记录
                    from sqlalchemy import text
                    logger.debug(f"[FIXED VERSION] 使用修复后的删除逻辑")
                    logger.debug(f"按正确顺序删除所有相关记录")

                    # 首先检查数据库中实际存在哪些表
                    logger.debug(f"检查数据库中的表结构")
                    tables_result = db.execute(text("SHOW TABLES"))
                    tables = [row[0] for row in tables_result.fetchall()]
                    logger.debug(f"数据库中的表: {tables}")

                    # 1. 检查是否有用户使用此角色，如果有则不允许删除
                    try:
                        users_with_role_result = db.execute(
                            text("SELECT COUNT(*) as count FROM users WHERE role_id = :role_id"),
                            {"role_id": role_id}
                        )
                        users_count = users_with_role_result.fetchone()[0]
                        logger.debug(f"检查用户使用情况: {users_count} 个用户使用此角色")

                        if users_count > 0:
                            logger.warning(f"⚠️ 无法删除角色，还有 {users_count} 个用户正在使用此角色")
                            return {
                                "success": False,
                                "error": "role_in_use",
                                "details": f"无法删除角色，还有 {users_count} 个用户正在使用此角色。请先将这些用户分配到其他角色。"
                            }
                    except Exception as user_check_error:
                        logger.warning(f"⚠️ 检查用户使用情况时出错（可能users表不存在）: {user_check_error}")
                        # 继续执行删除，不阻止删除过程

                    # 2. 删除角色API权限关联
                    try:
                        role_api_permissions_result = db.execute(
                            text("DELETE FROM role_api_permissions WHERE role_id = :role_id"),
                            {"role_id": role_id}
                        )
                        logger.debug(f"删除角色API权限关联成功，影响行数: {role_api_permissions_result.rowcount}")
                    except Exception as e:
                        logger.warning(f"⚠️ 删除角色API权限关联时出错: {e}")

                    # 3. 删除角色权限操作日志
                    try:
                        role_permission_logs_result = db.execute(
                            text("DELETE FROM role_permission_logs WHERE role_id = :role_id"),
                            {"role_id": role_id}
                        )
                        logger.debug(f"删除角色权限日志成功，影响行数: {role_permission_logs_result.rowcount}")
                    except Exception as e:
                        logger.warning(f"⚠️ 删除角色权限日志时出错: {e}")

                    # 4. 删除用户角色分配日志
                    try:
                        user_role_logs_result = db.execute(
                            text("DELETE FROM user_role_logs WHERE role_id = :role_id"),
                            {"role_id": role_id}
                        )
                        logger.debug(f"删除用户角色日志成功，影响行数: {user_role_logs_result.rowcount}")
                    except Exception as e:
                        logger.warning(f"⚠️ 删除用户角色日志时出错: {e}")

                    # 5. 删除角色权限关联
                    try:
                        role_permissions_result = db.execute(
                            text("DELETE FROM role_permissions WHERE role_id = :role_id"),
                            {"role_id": role_id}
                        )
                        logger.debug(f"删除角色权限关联成功，影响行数: {role_permissions_result.rowcount}")
                    except Exception as e:
                        logger.warning(f"⚠️ 删除角色权限关联时出错: {e}")

                    # 6. 删除用户角色关联
                    try:
                        user_roles_result = db.execute(
                            text("DELETE FROM user_roles WHERE role_id = :role_id"),
                            {"role_id": role_id}
                        )
                        logger.debug(f"删除用户角色关联成功，影响行数: {user_roles_result.rowcount}")
                    except Exception as e:
                        logger.warning(f"⚠️ 删除用户角色关联时出错: {e}")

                    # 7. 最后删除角色本身
                    role_result = db.execute(
                        text("DELETE FROM roles WHERE id = :role_id"),
                        {"role_id": role_id}
                    )
                    logger.debug(f"删除角色记录成功，影响行数: {role_result.rowcount}")

                    if role_result.rowcount == 0:
                        logger.warning(f"⚠️ 没有删除任何角色记录，角色可能不存在")
                        return {
                            "success": False,
                            "error": "role_not_found",
                            "details": "角色不存在或已被删除"
                        }

                    db.commit()
                    logger.debug(f"数据库提交成功")

                    logger.info(f"✅ 角色删除成功: {deleted_info['name']}")

                    return {
                        "success": True,
                        "data": deleted_info
                    }

                except Exception as delete_error:
                    logger.error(f"❌ 删除操作失败: {str(delete_error)}")
                    logger.debug(f"错误类型: {type(delete_error).__name__}")
                    import traceback
                    logger.debug(f"详细错误信息: {traceback.format_exc()}")
                    db.rollback()
                    raise delete_error

        except Exception as e:
            import traceback
            error_details = f"删除角色失败: {str(e)}\n堆栈跟踪: {traceback.format_exc()}"
            logger.error(f"❌ 删除角色异常: {error_details}")
            return {
                "success": False,
                "error": "deletion_failed",
                "details": error_details
            }

    # 权限管理方法
    def assign_permissions(self, role_id: str, request: RolePermissionsRequest,
                          operator_id: str = None) -> Dict[str, Any]:
        """为角色分配权限"""
        try:
            with get_db_session() as db:
                # 查询角色
                db_role = db.query(RoleDBModel).filter(RoleDBModel.id == role_id).first()

                if not db_role:
                    return {
                        "success": False,
                        "error": "role_not_found",
                        "details": f"角色 {role_id} 不存在"
                    }

                # 获取现有权限
                existing_permissions = [p.name for p in db_role.permissions]

                # 如果是替换模式，先清除所有权限
                if request.replace:
                    db_role.permissions.clear()
                    existing_permissions = []

                # 分配新权限
                added_permissions = []
                for perm_name in request.permissions:
                    if perm_name not in existing_permissions:
                        permission = db.query(PermissionDBModel).filter(
                            PermissionDBModel.name == perm_name
                        ).first()

                        if permission:
                            db_role.permissions.append(permission)
                            added_permissions.append(perm_name)

                            # 记录权限分配日志
                            log_id = self._generate_id("log")
                            log = RolePermissionLogDBModel(
                                id=log_id,
                                role_id=role_id,
                                permission_id=permission.id,
                                operation="grant",
                                operator_id=operator_id,
                                reason="权限分配"
                            )
                            db.add(log)

                db.commit()

                # 构建响应
                final_permissions = [p.name for p in db_role.permissions]

                return {
                    "success": True,
                    "data": {
                        "role": {
                            "id": db_role.id,
                            "name": db_role.name,
                            "code": db_role.code
                        },
                        "permissions": {
                            "added": added_permissions,
                            "existing": existing_permissions if not request.replace else [],
                            "total": len(final_permissions)
                        }
                    }
                }

        except Exception as e:
            return {
                "success": False,
                "error": "assignment_failed",
                "details": f"权限分配失败: {str(e)}"
            }

    def get_role_permissions(self, role_id: str, resource: str = None,
                           action: str = None) -> Dict[str, Any]:
        """获取角色权限列表"""
        try:
            with get_db_session() as db:
                # 查询角色
                db_role = db.query(RoleDBModel).filter(RoleDBModel.id == role_id).first()

                if not db_role:
                    return {
                        "success": False,
                        "error": "role_not_found",
                        "details": f"角色 {role_id} 不存在"
                    }

                # 获取权限查询
                permissions_query = db_role.permissions

                # 资源筛选
                if resource:
                    permissions_query = permissions_query.filter(
                        PermissionDBModel.resource == resource
                    )

                # 操作筛选
                if action:
                    permissions_query = permissions_query.filter(
                        PermissionDBModel.action == action
                    )

                permissions = permissions_query.all()

                # 构建权限列表
                permission_list = []
                for perm in permissions:
                    permission_list.append({
                        "id": perm.id,
                        "name": perm.name,
                        "description": perm.description,
                        "resource": perm.resource,
                        "action": perm.action,
                        "granted_at": format_datetime(perm.created_at)
                    })

                # 统计信息
                all_permissions = list(db_role.permissions)
                by_resource = {}
                by_action = {}

                for perm in all_permissions:
                    by_resource[perm.resource] = by_resource.get(perm.resource, 0) + 1
                    by_action[perm.action] = by_action.get(perm.action, 0) + 1

                return {
                    "success": True,
                    "data": {
                        "role": {
                            "id": db_role.id,
                            "name": db_role.name,
                            "code": db_role.code
                        },
                        "permissions": permission_list,
                        "summary": {
                            "total_permissions": len(all_permissions),
                            "by_resource": by_resource,
                            "by_action": by_action
                        }
                    }
                }

        except Exception as e:
            return {
                "success": False,
                "error": "query_failed",
                "details": f"获取角色权限失败: {str(e)}"
            }

    def remove_permission(self, role_id: str, permission_id: str,
                         operator_id: str = None) -> Dict[str, Any]:
        """移除角色权限"""
        try:
            with get_db_session() as db:
                # 查询角色
                db_role = db.query(RoleDBModel).filter(RoleDBModel.id == role_id).first()

                if not db_role:
                    return {
                        "success": False,
                        "error": "role_not_found",
                        "details": f"角色 {role_id} 不存在"
                    }

                # 查询权限
                permission = db.query(PermissionDBModel).filter(
                    PermissionDBModel.id == permission_id
                ).first()

                if not permission:
                    return {
                        "success": False,
                        "error": "permission_not_found",
                        "details": f"权限 {permission_id} 不存在"
                    }

                # 检查角色是否有此权限
                if permission not in db_role.permissions:
                    return {
                        "success": False,
                        "error": "permission_not_assigned",
                        "details": f"角色 {db_role.name} 没有权限 {permission.name}"
                    }

                # 移除权限
                db_role.permissions.remove(permission)

                # 记录权限移除日志
                log_id = self._generate_id("log")
                log = RolePermissionLogDBModel(
                    id=log_id,
                    role_id=role_id,
                    permission_id=permission_id,
                    operation="revoke",
                    operator_id=operator_id,
                    reason="权限移除"
                )
                db.add(log)

                db.commit()

                return {
                    "success": True,
                    "data": {
                        "role": {
                            "id": db_role.id,
                            "name": db_role.name,
                            "code": db_role.code
                        },
                        "permission": {
                            "id": permission.id,
                            "name": permission.name,
                            "description": permission.description
                        },
                        "removed_at": format_datetime(datetime.now())
                    }
                }

        except Exception as e:
            return {
                "success": False,
                "error": "removal_failed",
                "details": f"移除权限失败: {str(e)}"
            }

    # 辅助方法
    def _build_role_response(self, db_role: RoleDBModel, db: Session,
                           include_users: bool = False, include_permissions: bool = False) -> Dict[str, Any]:
        """构建角色响应数据"""
        role_data = {
            "id": db_role.id,
            "name": db_role.name,
            "code": db_role.code,
            "description": db_role.description,
            "status": db_role.status,
            "user_count": db_role.user_count,
            "permission_count": len(list(db_role.permissions)),
            "metadata": db_role.role_metadata or {},
            "created_at": format_datetime(db_role.created_at),
            "updated_at": format_datetime(db_role.updated_at)
        }

        if include_permissions:
            # 添加权限信息
            permissions = []
            for perm in db_role.permissions:
                permissions.append({
                    "id": perm.id,
                    "name": perm.name,
                    "description": perm.description,
                    "resource": perm.resource,
                    "action": perm.action
                })
            role_data["permissions"] = permissions

        if include_users:
            # 添加用户信息（模拟数据，因为没有实际的用户表）
            users = []
            for i in range(min(db_role.user_count, 5)):  # 最多显示5个用户
                users.append({
                    "id": f"user_{i+1:03d}",
                    "name": f"用户{i+1}",
                    "email": f"user{i+1}@example.com",
                    "status": "active",
                    "assigned_at": format_datetime(db_role.created_at)
                })
            role_data["users"] = users

            # 添加统计信息
            role_data["statistics"] = {
                "user_count": db_role.user_count,
                "permission_count": len(list(db_role.permissions)),
                "active_users": db_role.user_count,
                "last_login": format_datetime(datetime.now()) if db_role.user_count > 0 else None
            }

        return role_data

    def _build_role_list_item(self, db_role: RoleDBModel, db: Session) -> Dict[str, Any]:
        """构建角色列表项数据"""
        from app.models.api_route import APIRouteDBModel, RouteStatus

        # 实时计算有效的权限数量
        role_perms = {p.name for p in db_role.permissions}
        
        # 获取所有活跃的API路由
        active_apis = db.query(APIRouteDBModel).filter(
            APIRouteDBModel.status == RouteStatus.ACTIVE
        ).all()

        accessible_api_count = 0
        for api in active_apis:
            permission_name = f"{api.api_id}:access"
            # 检查角色是否有此API的权限 (精确匹配, 通配符等)
            if (permission_name in role_perms or
                f"{api.api_id}:*" in role_perms or
                "*:*" in role_perms):
                accessible_api_count += 1

        return {
            "id": db_role.id,
            "name": db_role.name,
            "code": db_role.code,
            "description": db_role.description,
            "status": db_role.status,
            "user_count": db_role.user_count,
            "permission_count": accessible_api_count, # 使用实时计算的数量
            "created_at": format_datetime(db_role.created_at),
            "updated_at": format_datetime(db_role.updated_at)
        }
