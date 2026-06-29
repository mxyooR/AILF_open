"""
权限控制服务层
实现权限检查、权限配置和权限矩阵管理的核心业务逻辑
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.core.logging_config import get_logger
from app.core.database import get_db_session
from app.core.utils import format_datetime, generate_id
from app.models.role import RoleDBModel, PermissionDBModel
from app.models.permission_control import (
    APIEndpointDBModel, RoleAPIPermissionDBModel, PermissionCheckLogDBModel
)
from app.models.api_route import APIRouteDBModel
from app.schemas.permission_control import (
    PermissionCheckRequest, RoleAPIPermissionRequest, BatchPermissionUpdateRequest
)

logger = get_logger(__name__)


class PermissionService:
    """权限控制服务类"""
    
    def _generate_id(self, prefix: str) -> str:
        """生成唯一ID"""
        return generate_id(prefix)
    
    def _get_user_roles(self, user_id: str, db: Session) -> List[Dict[str, Any]]:
        """获取用户角色列表（从数据库读取）"""
        try:
            # 从用户表获取用户信息
            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()

            if not user or not user.role_id:
                return []

            # 获取用户角色
            role = db.query(RoleDBModel).filter(RoleDBModel.id == user.role_id).first()

            if not role:
                return []

            return [
                {
                    "id": role.id,
                    "name": role.name,
                    "code": role.code,
                    "status": role.status
                }
            ]

        except Exception as e:
            logger.warning(f"⚠️ 获取用户角色失败: {str(e)}")
            return []
    
    def _log_permission_check(self, user_id: str, resource: str, action: str, 
                            permission_required: str, is_allowed: bool, 
                            granted_by_role: str = None, denial_reason: str = None,
                            request_context: Dict = None, user_roles: List = None,
                            db: Session = None):
        """记录权限检查日志"""
        try:
            log_id = self._generate_id("perm_log")
            log = PermissionCheckLogDBModel(
                id=log_id,
                user_id=user_id,
                resource=resource,
                action=action,
                permission_required=permission_required,
                is_allowed=is_allowed,
                granted_by_role=granted_by_role,
                denial_reason=denial_reason,
                request_context=request_context or {},
                user_roles=[role.get("code") for role in user_roles] if user_roles else []
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.warning(f"⚠️ 记录权限检查日志失败: {e}")

    def check_guest_permission(self, resource: str, action: str,
                              context: dict = None, db=None) -> Dict[str, Any]:
        """检查访客是否有访问特定API的权限"""
        try:
            if db is None:
                with get_db_session() as db:
                    return self._check_guest_permission_internal(resource, action, context, db)
            else:
                return self._check_guest_permission_internal(resource, action, context, db)
        except Exception as e:
            logger.error(f"访客权限检查失败: {e}")
            return {
                "allowed": False,
                "reason": f"权限检查异常: {str(e)}",
                "user_roles": [],
                "matched_permissions": []
            }

    def _check_guest_permission_internal(self, resource: str, action: str,
                                       context: dict, db) -> Dict[str, Any]:
        """内部访客权限检查方法"""
        # 获取guest角色
        from app.models.role import RoleDBModel
        guest_role = db.query(RoleDBModel).filter(
            RoleDBModel.code == "guest",
            RoleDBModel.status == "active"
        ).first()

        if not guest_role:
            logger.warning("未找到guest角色，拒绝访客访问")
            return {
                "allowed": False,
                "reason": "系统未配置访客角色",
                "user_roles": [],
                "matched_permissions": []
            }

        # 获取guest角色的权限
        guest_permissions = []
        for permission in guest_role.permissions:
            guest_permissions.append(f"{permission.resource}:{permission.action}")

        # 检查是否有匹配的权限
        required_permission = f"{resource}:{action}"

        # 精确匹配
        if required_permission in guest_permissions:
            logger.info(f"访客权限匹配成功: {required_permission}")
            return {
                "allowed": True,
                "reason": "访客权限验证通过",
                "user_roles": [{"name": "访客", "code": "guest"}],
                "matched_permissions": [required_permission]
            }

        # 通配符匹配
        for perm in guest_permissions:
            if perm.endswith(":*") and perm.startswith(f"{resource}:"):
                logger.info(f"访客权限通配符匹配成功: {perm} -> {required_permission}")
                return {
                    "allowed": True,
                    "reason": "访客权限验证通过（通配符匹配）",
                    "user_roles": [{"name": "访客", "code": "guest"}],
                    "matched_permissions": [perm]
                }

        logger.warning(f"访客权限不足: 需要 {required_permission}，可用权限: {guest_permissions}")
        return {
            "allowed": False,
            "reason": f"访客没有'{required_permission}'权限",
            "user_roles": [{"name": "访客", "code": "guest"}],
            "matched_permissions": [],
            "available_permissions": guest_permissions
        }

    # 权限检查方法
    def check_permission(self, request: PermissionCheckRequest, 
                        operator_id: str = None) -> Dict[str, Any]:
        """检查用户是否有访问特定API的权限"""
        try:
            with get_db_session() as db:
                # 获取用户角色
                user_roles = self._get_user_roles(request.user_id, db)
                
                if not user_roles:
                    # 记录日志
                    self._log_permission_check(
                        request.user_id, request.resource, request.action,
                        f"{request.resource}:{request.action}", False,
                        denial_reason="用户没有任何角色", db=db
                    )
                    
                    return {
                        "success": True,
                        "allowed": False,
                        "data": {
                            "allowed": False,
                            "user": {
                                "id": request.user_id,
                                "name": f"用户{request.user_id}",
                                "roles": []
                            },
                            "permission": {
                                "resource": request.resource,
                                "action": request.action,
                                "required_permission": f"{request.resource}:{request.action}"
                            },
                            "reason": "用户没有任何角色",
                            "suggestions": [
                                "联系管理员分配角色",
                                "检查用户账户状态"
                            ],
                            "checked_at": format_datetime(datetime.now())
                        }
                    }
                
                # 检查权限
                permission_required = f"{request.resource}:{request.action}"
                granted_by_role = None
                
                # 遍历用户角色，检查是否有所需权限
                for role in user_roles:
                    role_obj = db.query(RoleDBModel).filter(RoleDBModel.id == role["id"]).first()
                    if role_obj:
                        # 检查角色是否有所需权限
                        role_permissions = [p.name for p in role_obj.permissions]
                        has_permission = (
                            permission_required in role_permissions or
                            f"{request.resource}:*" in role_permissions or
                            "*:*" in role_permissions
                        )
                        
                        if has_permission:
                            granted_by_role = f"role:{role['code']}"
                            break
                
                # 构建响应
                if granted_by_role:
                    # 有权限
                    self._log_permission_check(
                        request.user_id, request.resource, request.action,
                        permission_required, True, granted_by_role,
                        request_context=request.context, user_roles=user_roles, db=db
                    )
                    
                    return {
                        "success": True,
                        "allowed": True,
                        "data": {
                            "allowed": True,
                            "user": {
                                "id": request.user_id,
                                "name": f"用户{request.user_id}",
                                "roles": [role["code"] for role in user_roles]
                            },
                            "permission": {
                                "resource": request.resource,
                                "action": request.action,
                                "granted_by": granted_by_role,
                                "permission_name": permission_required
                            },
                            "context": request.context or {},
                            "checked_at": format_datetime(datetime.now())
                        }
                    }
                else:
                    # 无权限
                    role_names = [role["name"] for role in user_roles]
                    denial_reason = f"用户角色 {', '.join(role_names)} 没有 '{permission_required}' 权限"
                    
                    self._log_permission_check(
                        request.user_id, request.resource, request.action,
                        permission_required, False, denial_reason=denial_reason,
                        request_context=request.context, user_roles=user_roles, db=db
                    )
                    
                    return {
                        "success": True,
                        "allowed": False,
                        "data": {
                            "allowed": False,
                            "user": {
                                "id": request.user_id,
                                "name": f"用户{request.user_id}",
                                "roles": [role["code"] for role in user_roles]
                            },
                            "permission": {
                                "resource": request.resource,
                                "action": request.action,
                                "required_permission": permission_required
                            },
                            "reason": denial_reason,
                            "suggestions": [
                                "联系管理员申请权限",
                                "使用具有相应权限的账户"
                            ],
                            "checked_at": format_datetime(datetime.now())
                        }
                    }
                
        except Exception as e:
            return {
                "success": False,
                "error": "permission_check_failed",
                "details": f"权限检查失败: {str(e)}"
            }
    
    # 权限配置管理方法
    def update_role_api_permission(self, request: RoleAPIPermissionRequest,
                                 operator_id: str = None) -> Dict[str, Any]:
        """更新角色对特定API的访问权限"""
        try:
            with get_db_session() as db:
                # 查询角色
                role = db.query(RoleDBModel).filter(RoleDBModel.id == request.role_id).first()
                if not role:
                    return {
                        "success": False,
                        "error": "role_not_found",
                        "details": f"角色 {request.role_id} 不存在"
                    }

                # 查询API路由
                from app.models.api_route import APIRouteDBModel

                api = db.query(APIRouteDBModel).filter(APIRouteDBModel.id == request.api_id).first()
                if not api:
                    return {
                        "success": False,
                        "error": "api_not_found",
                        "details": f"API路由 {request.api_id} 不存在"
                    }

                # 为API路由生成权限名称
                permission_name = request.permission
                if permission_name == "access":
                    # 如果是通用访问权限，使用API ID生成权限名称
                    permission_name = f"{api.api_id}:access"

                permission = db.query(PermissionDBModel).filter(
                    PermissionDBModel.name == permission_name
                ).first()
                if not permission:
                    # 如果权限不存在，自动创建
                    permission_id = self._generate_id("perm")
                    # 从API ID中提取资源名称
                    resource_name = api.api_id.replace("_api", "").replace("_", "")
                    permission = PermissionDBModel(
                        id=permission_id,
                        name=permission_name,
                        description=f"API路由权限: {api.name}",
                        resource=resource_name,
                        action="access"
                    )
                    db.add(permission)
                    db.flush()  # 确保权限被创建

                # 执行权限操作
                if request.action == "grant":
                    # 授予权限
                    if permission not in role.permissions:
                        role.permissions.append(permission)
                        db.flush()

                        logger.info(f"✅ 为角色 {role.name} 授予权限 {permission.name}")
                        logger.debug(f"角色当前所有权限: {[p.name for p in role.permissions]}")

                        # 记录权限分配日志
                        from app.models.role import RolePermissionLogDBModel
                        log_id = self._generate_id("log")
                        log = RolePermissionLogDBModel(
                            id=log_id,
                            role_id=request.role_id,
                            permission_id=permission.id,
                            operation="grant",
                            operator_id=operator_id,
                            reason=f"通过API {api.name} 授予权限"
                        )
                        db.add(log)

                        db.commit()
                        logger.debug(f"权限更新已提交到数据库")

                        return {
                            "success": True,
                            "data": {
                                "role": {
                                    "id": role.id,
                                    "name": role.name,
                                    "code": role.code
                                },
                                "api": {
                                    "id": api.id,
                                    "name": api.name,
                                    "endpoint": api.endpoint,
                                    "method": api.method
                                },
                                "permission": {
                                    "name": request.permission,
                                    "action": "grant",
                                    "granted_at": format_datetime(datetime.now()),
                                    "granted_by": operator_id or "system"
                                }
                            }
                        }
                    else:
                        return {
                            "success": False,
                            "error": "permission_already_granted",
                            "details": f"角色 {role.name} 已经拥有权限 {request.permission}"
                        }

                elif request.action == "revoke":
                    # 撤销权限
                    if permission in role.permissions:
                        role.permissions.remove(permission)
                        db.flush()

                        # 记录权限撤销日志
                        from app.models.role import RolePermissionLogDBModel
                        log_id = self._generate_id("log")
                        log = RolePermissionLogDBModel(
                            id=log_id,
                            role_id=request.role_id,
                            permission_id=permission.id,
                            operation="revoke",
                            operator_id=operator_id,
                            reason=f"通过API {api.name} 撤销权限"
                        )
                        db.add(log)

                        db.commit()

                        return {
                            "success": True,
                            "data": {
                                "role": {
                                    "id": role.id,
                                    "name": role.name,
                                    "code": role.code
                                },
                                "api": {
                                    "id": api.id,
                                    "name": api.name,
                                    "endpoint": api.endpoint,
                                    "method": api.method
                                },
                                "permission": {
                                    "name": request.permission,
                                    "action": "revoke",
                                    "revoked_at": format_datetime(datetime.now()),
                                    "revoked_by": operator_id or "system"
                                }
                            }
                        }
                    else:
                        return {
                            "success": False,
                            "error": "permission_not_granted",
                            "details": f"角色 {role.name} 没有权限 {request.permission}"
                        }

        except Exception as e:
            return {
                "success": False,
                "error": "update_failed",
                "details": f"更新角色API权限失败: {str(e)}"
            }

    def batch_update_permissions(self, request: BatchPermissionUpdateRequest,
                               operator_id: str = None) -> Dict[str, Any]:
        """批量更新多个角色的API权限"""
        try:
            results = []
            successful = 0
            failed = 0
            granted = 0
            revoked = 0

            for update in request.updates:
                if request.dry_run:
                    # 试运行模式，只验证不执行
                    result = {
                        "role_id": update.role_id,
                        "api_id": update.api_id,
                        "permission": update.permission,
                        "action": update.action,
                        "status": "dry_run",
                        "message": "试运行模式，未实际执行"
                    }
                    results.append(result)
                    successful += 1
                else:
                    # 实际执行更新
                    update_result = self.update_role_api_permission(update, operator_id)

                    if update_result["success"]:
                        result = {
                            "role_id": update.role_id,
                            "api_id": update.api_id,
                            "permission": update.permission,
                            "action": update.action,
                            "status": "success",
                            "message": "权限更新成功"
                        }
                        successful += 1
                        if update.action == "grant":
                            granted += 1
                        else:
                            revoked += 1
                    else:
                        result = {
                            "role_id": update.role_id,
                            "api_id": update.api_id,
                            "permission": update.permission,
                            "action": update.action,
                            "status": "failed",
                            "message": update_result.get("details", "更新失败"),
                            "error": update_result.get("error", "unknown_error")
                        }
                        failed += 1

                    results.append(result)

            return {
                "success": True,
                "data": {
                    "results": results,
                    "summary": {
                        "total": len(request.updates),
                        "successful": successful,
                        "failed": failed,
                        "granted": granted,
                        "revoked": revoked
                    }
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": "batch_update_failed",
                "details": f"批量权限更新失败: {str(e)}"
            }

    # 权限矩阵管理方法
    def get_permission_matrix(self, format_type: str = "matrix",
                            include_inactive: bool = False) -> Dict[str, Any]:
        """获取完整的权限矩阵"""
        try:
            with get_db_session() as db:
                # 获取角色列表
                role_query = db.query(RoleDBModel)
                if not include_inactive:
                    role_query = role_query.filter(RoleDBModel.status == "active")

                roles = role_query.all()

                # 获取API列表 - 使用真实的API路由数据（包含公开路由和私有路由）
                from app.models.api_route import APIRouteDBModel, RouteStatus

                apis = db.query(APIRouteDBModel).filter(
                    APIRouteDBModel.status == RouteStatus.ACTIVE
                    # 不过滤 auth_required，包含公开路由
                ).all()

                logger.debug(f"找到 {len(apis)} 个活跃的API路由")
                for api in apis:
                    logger.debug(f"  - {api.name} ({api.api_id}): {api.method} {api.endpoint}")

                # 构建角色信息
                role_list = []
                for role in roles:
                    role_list.append({
                        "id": role.id,
                        "name": role.name,
                        "code": role.code,
                        "status": role.status
                    })

                # 构建API信息
                api_list = []
                for api in apis:
                    # 为API路由生成权限标识符
                    # 格式：api_id:action 或者 resource:action
                    permission_name = f"{api.api_id}:access"

                    api_list.append({
                        "id": api.id,
                        "name": api.name,
                        "endpoint": api.endpoint,
                        "method": api.method,
                        "permission": permission_name,
                        "api_id": api.api_id,
                        "description": api.description,
                        "auth_required": api.auth_required,
                        "is_public": not api.auth_required  # 标记是否为公开路由（前端用于禁用编辑）
                    })

                # 构建权限矩阵
                permissions_matrix = {}
                total_permissions = 0
                granted_permissions = 0

                for role in roles:
                    role_permissions = {}
                    # 重新查询角色权限以确保数据是最新的
                    fresh_role = db.query(RoleDBModel).filter(RoleDBModel.id == role.id).first()
                    role_perms = [p.name for p in fresh_role.permissions] if fresh_role else []

                    logger.debug(f"角色 {role.name} 的权限: {role_perms}")

                    for api in apis:
                        total_permissions += 1
                        # 为API路由生成权限标识符
                        permission_name = f"{api.api_id}:access"

                        # 公开路由：所有角色都有权限，不可修改
                        if not api.auth_required:
                            has_permission = True
                            logger.debug(f"公开路由 {api.name} - 所有角色可访问")
                        else:
                            # 私有路由：检查角色是否有此API的权限
                            has_permission = (
                                permission_name in role_perms or
                                f"{api.api_id}:*" in role_perms or
                                "*:*" in role_perms
                            )
                            if has_permission:
                                logger.debug(f"角色 {role.name} 有权限访问 {api.name}")
                            else:
                                logger.debug(f"角色 {role.name} 无权限访问 {api.name}")
                        
                        role_permissions[api.id] = has_permission
                        if has_permission:
                            granted_permissions += 1

                    permissions_matrix[role.id] = role_permissions

                # 计算统计信息
                denied_permissions = total_permissions - granted_permissions
                coverage = (granted_permissions / total_permissions * 100) if total_permissions > 0 else 0

                return {
                    "success": True,
                    "data": {
                        "matrix": {
                            "roles": role_list,
                            "apis": api_list,
                            "permissions": permissions_matrix
                        },
                        "statistics": {
                            "total_roles": len(roles),
                            "total_apis": len(apis),
                            "total_permissions": total_permissions,
                            "granted_permissions": granted_permissions,
                            "denied_permissions": denied_permissions,
                            "coverage": round(coverage, 1)
                        }
                    }
                }

        except Exception as e:
            return {
                "success": False,
                "error": "matrix_query_failed",
                "details": f"获取权限矩阵失败: {str(e)}"
            }


    def get_user_permissions(self, user, db: Session) -> List[str]:
        """获取用户权限列表"""
        try:
            if not user or not user.role_id:
                return ["user:read"]  # 默认最小权限

            # 获取用户角色
            user_role = db.query(RoleDBModel).filter(RoleDBModel.id == user.role_id).first()
            if not user_role:
                return ["user:read"]

            # 从角色的权限关联中获取权限
            permissions = []
            for permission in user_role.permissions:
                permissions.append(permission.name)

            # 如果没有关联权限，返回基础权限
            if not permissions:
                permissions = ["user:read", "user:update_self"]

            return permissions

        except Exception as e:
            logger.warning(f"⚠️ 获取用户权限失败: {str(e)}")
            return ["user:read"]  # 返回最小权限

    def get_user_accessible_apis(self, user, db: Session) -> List[Dict[str, Any]]:
        """获取用户可访问的API列表"""
        try:
            if not user or not user.role_id:
                return self._get_guest_apis()

            # 获取用户角色
            user_role = db.query(RoleDBModel).filter(RoleDBModel.id == user.role_id).first()
            if not user_role:
                return self._get_guest_apis()

            # 获取基础API
            apis = self._get_base_apis()

            # 获取动态分配的API权限
            dynamic_apis = self._get_dynamic_apis_by_role(user.role_id, db)
            apis.extend(dynamic_apis)

            return apis

        except Exception as e:
            logger.warning(f"⚠️ 获取用户可访问API失败: {str(e)}")
            return self._get_guest_apis()

    def _get_guest_apis(self) -> List[Dict[str, Any]]:
        """获取访客可访问的API"""
        return [
            {
                "endpoint": "/api/v1/user/login",
                "method": "POST",
                "description": "用户登录",
                "resource": "user",
                "action": "login"
            },
            {
                "endpoint": "/api/v1/user/register",
                "method": "POST",
                "description": "用户注册",
                "resource": "user",
                "action": "register"
            }
        ]

    def _get_base_apis(self) -> List[Dict[str, Any]]:
        """获取基础API列表"""
        return [
            {
                "endpoint": "/api/v1/user/me",
                "method": "GET",
                "description": "获取个人信息",
                "resource": "user",
                "action": "read"
            },
            {
                "endpoint": "/api/v1/user/logout",
                "method": "POST",
                "description": "用户登出",
                "resource": "user",
                "action": "logout"
            },
            {
                "endpoint": "/api/v1/command/async",
                "method": "POST",
                "description": "AI命令处理",
                "resource": "ai",
                "action": "command"
            }
        ]

    def _get_dynamic_apis_by_role(self, role_id: str, db: Session) -> List[Dict[str, Any]]:
        """获取角色动态分配的API权限"""
        try:
            # 获取所有活跃的API路由（包含公开路由和私有路由）
            from app.models.api_route import APIRouteDBModel, RouteStatus
            apis = db.query(APIRouteDBModel).filter(
                APIRouteDBModel.status == RouteStatus.ACTIVE
                # 不过滤 auth_required，包含公开路由
            ).all()


            # 获取角色权限
            role = db.query(RoleDBModel).filter(RoleDBModel.id == role_id).first()
            if not role:
                return []

            role_permissions = [p.name for p in role.permissions]
            accessible_apis = []

            for api in apis:
                # 公开路由：所有用户都可以访问，不需要权限检查
                if not api.auth_required:
                    has_access = True
                else:
                    # 私有路由：检查是否有权限访问此API
                    required_permission = f"{api.api_id}:access"
                    wildcard_permission = f"{api.api_id}:*"
                    super_permission = "*:*"

                    has_access = (
                        required_permission in role_permissions or
                        wildcard_permission in role_permissions or
                        super_permission in role_permissions
                    )

                if has_access:
                    api_info = {
                        "api_id": api.api_id,  # 添加api_id字段
                        "name": api.name,  # 添加API名称
                        "endpoint": api.endpoint,
                        "method": api.method,
                        "description": api.description,
                        "resource": api.api_id.replace("_api", "").replace("_", ""),
                        "action": "access"
                    }
                    
                    # 添加参数配置供AI图谱使用
                    if api.parameters_config:
                        api_info["parameters"] = api.parameters_config
                    
                    # 添加响应schema信息供AI使用
                    if api.responses_config:
                        api_info["responses_config"] = api.responses_config
                        # 尝试提取主要的schema信息以便AI更好地理解
                        if "200" in api.responses_config:
                            response_200 = api.responses_config["200"]
                            if "response_schema" in response_200:
                                api_info["schema"] = response_200["response_schema"]
                            elif "schema" in response_200:
                                api_info["schema"] = response_200["schema"]
                    
                    # 添加处理器配置信息
                    if api.handler_config:
                        api_info["handler_config"] = api.handler_config
                    
                    accessible_apis.append(api_info)

            return accessible_apis

        except Exception as e:
            logger.warning(f"⚠️ 获取动态API权限失败: {str(e)}")
            return []


# 全局权限服务实例
permission_service = PermissionService()
