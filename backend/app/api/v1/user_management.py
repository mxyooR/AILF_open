"""
用户管理API路由
提供管理员用户管理功能：创建用户、分配角色、权限管理等
"""
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from app.core.logging_config import get_logger
from datetime import datetime
from sqlalchemy import func

from app.core.database import get_db
from app.core.auth import verify_developer_token
from app.models.user import User
from app.models.role import RoleDBModel
from app.schemas.user_auth import UserRegisterRequest, AdminCreateUserRequest, UserResponse
from app.services.dynamic_user_service import dynamic_user_service
from app.api.v1.user_auth import hash_password
from app.config import settings
from app.services.permission_service import permission_service
from app.core.response import UnifiedResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", response_model=dict)
async def get_users_list(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    limit: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    role_id: Optional[str] = Query(None, description="按角色筛选"),
    status: Optional[str] = Query(None, description="按状态筛选：active, inactive"),
    search: Optional[str] = Query(None, description="搜索用户名、邮箱或真实姓名"),
    current_user: dict = Depends(verify_developer_token),
    db: Session = Depends(get_db)
):
    """
    获取用户列表
    
    支持分页、角色筛选、状态筛选和搜索功能
    """
    try:
        # 构建查询
        query = db.query(User).join(RoleDBModel, User.role_id == RoleDBModel.id)
        
        # 角色筛选
        if role_id:
            query = query.filter(User.role_id == role_id)
        
        # 状态筛选
        if status:
            is_active = status.lower() == "active"
            query = query.filter(User.is_active == is_active)
        
        # 搜索
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.username.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (User.real_name.ilike(search_term))
            )
        
        # 总数统计
        total = query.count()
        
        # 分页
        offset = (page - 1) * limit
        users = query.offset(offset).limit(limit).all()
        
        # 构建响应数据
        users_data = []
        for user in users:
            user_role = db.query(RoleDBModel).filter(RoleDBModel.id == user.role_id).first()
            users_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "real_name": user.real_name,
                "phone": user.phone,
                "is_active": user.is_active,
                "role": {
                    "id": user_role.id,
                    "name": user_role.name,
                    "code": user_role.code,
                    "description": user_role.description
                } if user_role else None,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            })
        
        return UnifiedResponse.success(
            message="获取用户列表成功",
            data={
                "users": users_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            }
        )
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="获取用户列表失败",
            error_type="get_users_error",
            details=str(e)
        )


@router.post("", response_model=UserResponse, status_code=201)
async def create_user_by_admin(
    request: AdminCreateUserRequest,
    current_user: dict = Depends(verify_developer_token),
    db: Session = Depends(get_db)
):
    """
    管理员创建用户
    
    管理员可以直接创建用户并指定角色，无需用户自己注册
    """
    try:
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(
            (User.username == request.username) | 
            (User.email == request.email)
        ).first()
        
        if existing_user:
            if existing_user.username == request.username:
                raise UnifiedResponse.conflict(
                    message="用户名已存在",
                    error_type="username_exists"
                )
            else:
                raise UnifiedResponse.conflict(
                    message="邮箱已存在",
                    error_type="email_exists"
                )
        
        # 验证角色是否存在（管理员创建用户时必须指定角色）
        target_role = db.query(RoleDBModel).filter(RoleDBModel.id == request.role_id).first()
        if not target_role:
            raise UnifiedResponse.bad_request(
                message="指定的角色不存在",
                error_type="role_not_found"
            )

        # 检查角色是否激活
        if target_role.status != "active":
            raise UnifiedResponse.bad_request(
                message="指定的角色未激活，无法分配给用户",
                error_type="role_inactive"
            )
        
        # 创建新用户
        hashed_password = hash_password(request.password)
        new_user = User(
            username=request.username,
            email=request.email,
            password_hash=hashed_password,
            phone=request.phone,
            real_name=request.real_name,
            role_id=target_role.id,
            is_active=request.is_active
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # 更新角色的用户数量统计
        target_role.user_count = (target_role.user_count or 0) + 1
        db.commit()

        return UserResponse(
            code=201,
            message="用户创建成功",
            data={
                "user_id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "real_name": new_user.real_name,
                "phone": new_user.phone,
                "is_active": new_user.is_active,
                "role": {
                    "id": target_role.id,
                    "name": target_role.name,
                    "code": target_role.code,
                    "description": target_role.description
                },
                "created_at": new_user.created_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"管理员创建用户失败: {str(e)}")
        db.rollback()
        raise UnifiedResponse.internal_error(
            message="创建用户失败，请稍后重试",
            error_type="create_user_error",
            details=str(e)
        )





@router.put("/{user_id}/role", response_model=dict)
async def update_user_role(
    user_id: int,
    role_id: str,
    current_user: dict = Depends(verify_developer_token),
    db: Session = Depends(get_db)
):
    """
    更新用户角色
    
    管理员可以修改用户的角色权限
    """
    try:
        # 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnifiedResponse.not_found(
                message="用户不存在",
                error_type="user_not_found"
            )
        
        # 检查角色是否存在
        new_role = db.query(RoleDBModel).filter(RoleDBModel.id == role_id).first()
        if not new_role:
            raise UnifiedResponse.bad_request(
                message="指定的角色不存在",
                error_type="role_not_found"
            )
        
        # 获取旧角色信息
        old_role = db.query(RoleDBModel).filter(RoleDBModel.id == user.role_id).first()
        
        # 更新用户角色
        user.role_id = role_id
        user.updated_at = datetime.utcnow()
        db.commit()
        
        return UnifiedResponse.success(
            message="用户角色更新成功",
            data={
                "user_id": user.id,
                "username": user.username,
                "old_role": {
                    "id": old_role.id,
                    "name": old_role.name,
                    "code": old_role.code
                } if old_role else None,
                "new_role": {
                    "id": new_role.id,
                    "name": new_role.name,
                    "code": new_role.code
                },
                "updated_at": user.updated_at.isoformat(),
                "updated_by": current_user.get("username", "管理员")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户角色失败: {str(e)}")
        db.rollback()
        raise UnifiedResponse.internal_error(
            message="更新用户角色失败",
            error_type="update_role_error",
            details=str(e)
        )


@router.put("/{user_id}/status", response_model=dict)
async def update_user_status(
    user_id: int,
    is_active: bool,
    current_user: dict = Depends(verify_developer_token),
    db: Session = Depends(get_db)
):
    """
    更新用户状态（启用/禁用）
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnifiedResponse.not_found(
                message="用户不存在",
                error_type="user_not_found"
            )

        old_status = user.is_active
        user.is_active = is_active
        user.updated_at = datetime.utcnow()
        db.commit()

        return UnifiedResponse.success(
            message=f"用户已{'启用' if is_active else '禁用'}",
            data={
                "user_id": user.id,
                "username": user.username,
                "old_status": old_status,
                "new_status": is_active,
                "updated_at": user.updated_at.isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户状态失败: {str(e)}")
        db.rollback()
        raise UnifiedResponse.internal_error(
            message="更新用户状态失败",
            error_type="update_status_error",
            details=str(e)
        )


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    current_user: dict = Depends(verify_developer_token),
    db: Session = Depends(get_db)
):
    """
    删除用户

    管理员可以删除用户账户
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnifiedResponse.not_found(
                message="用户不存在",
                error_type="user_not_found"
            )

        # 保存用户信息用于响应
        user_info = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "real_name": user.real_name
        }

        # 获取用户的角色信息，用于更新角色用户数量
        user_role_id = user.role_id

        # 删除用户
        db.delete(user)
        db.commit()

        # 更新角色的用户数量统计
        if user_role_id:
            target_role = db.query(RoleDBModel).filter(RoleDBModel.id == user_role_id).first()
            if target_role and target_role.user_count > 0:
                target_role.user_count = target_role.user_count - 1
                db.commit()

        return UnifiedResponse.success(
            message="用户删除成功",
            data={
                **user_info,
                "deleted_at": datetime.utcnow().isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        db.rollback()
        raise UnifiedResponse.internal_error(
            message="删除用户失败",
            error_type="delete_user_error",
            details=str(e)
        )


@router.get("/roles/available", response_model=dict)
async def get_available_roles(
    current_user: dict = Depends(verify_developer_token),
    db: Session = Depends(get_db)
):
    """
    获取可用角色列表

    用于用户注册时选择角色，只返回有对应实体的角色
    """
    try:
        # 获取角色实体列表
        role_entities = dynamic_user_service.get_role_entities()

        # 获取有对应实体的活跃角色
        roles_data = []
        for entity in role_entities:
            if entity["role_id"]:
                role = db.query(RoleDBModel).filter(
                    RoleDBModel.id == entity["role_id"],
                    RoleDBModel.status == "active"
                ).first()

                if role:
                    roles_data.append({
                        "id": role.id,
                        "name": role.name,
                        "code": role.code,
                        "description": role.description,
                        "user_count": role.user_count or 0,
                        "entity_id": entity["id"],
                        "entity_name": entity["name"],
                        "entity_display_name": entity["display_name"]
                    })

        return UnifiedResponse.success(
            message="获取可用角色列表成功",
            data={
                "roles": roles_data,
                "total": len(roles_data)
            }
        )

    except Exception as e:
        logger.error(f"获取可用角色列表失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="获取可用角色列表失败",
            error_type="get_roles_error",
            details=str(e)
        )


@router.post("/sync-entity-roles", response_model=dict)
async def sync_entity_roles(
    current_user: dict = Depends(verify_developer_token)
):
    """
    同步角色实体

    为标记为角色的实体自动创建对应的角色记录
    """
    try:
        logger.info("开始同步角色实体")

        result = dynamic_user_service.sync_entity_roles_all()

        if result["success"]:
            logger.info(f"角色实体同步成功: 创建 {len(result['created_roles'])} 个角色，更新 {len(result['updated_roles'])} 个角色")
            return UnifiedResponse.success(
                message="角色实体同步成功",
                data=result
            )
        else:
            logger.error(f"角色实体同步失败: {result['error']}")
            raise UnifiedResponse.internal_error(
                message="角色实体同步失败",
                error_type="sync_error",
                details=result['error']
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"角色实体同步失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="角色实体同步失败",
            error_type="sync_exception",
            details=str(e)
        )


@router.get("/role-entities", response_model=dict)
async def get_role_entities(
    current_user: dict = Depends(verify_developer_token)
):
    """
    获取角色实体列表

    获取所有标记为角色的实体（is_role: true）
    """
    try:
        logger.info("开始获取角色实体列表")

        role_entities = dynamic_user_service.get_role_entities()
        logger.info(f"获取到角色实体: {len(role_entities)} 个")

        return UnifiedResponse.success(
            message="获取角色实体列表成功",
            data={
                "entities": role_entities,
                "total": len(role_entities)
            }
        )

    except Exception as e:
        logger.error(f"获取角色实体列表失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="获取角色实体列表失败",
            error_type="get_entities_error",
            details=str(e)
        )


@router.get("/entity-fields/{entity_id}", response_model=dict)
async def get_entity_fields(
    entity_id: str,
    current_user: dict = Depends(verify_developer_token)
):
    """
    获取实体字段定义

    获取指定实体的字段定义，用于动态生成表单和表格配置
    """
    try:
        logger.info(f"开始获取实体字段定义，实体ID: {entity_id}")

        entity_fields = dynamic_user_service.get_entity_fields(entity_id)

        if not entity_fields:
            raise UnifiedResponse.not_found(
                message="实体不存在",
                error_type="entity_not_found"
            )

        return UnifiedResponse.success(
            message="获取实体字段定义成功",
            data=entity_fields
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实体字段定义失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="获取实体字段定义失败",
            error_type="get_fields_error",
            details=str(e)
        )


@router.get("/form-schema", response_model=dict)
async def get_user_form_schema(
    role_id: Optional[str] = None,
    current_user: dict = Depends(verify_developer_token)
):
    """
    获取用户表单schema

    根据角色对应的实体定义动态生成表单配置
    """
    try:
        logger.info(f"开始获取用户表单schema，角色ID: {role_id}")
        logger.info(f"当前用户: {current_user}")

        form_schema = dynamic_user_service.get_user_form_schema(role_id)
        logger.info(f"获取到表单schema: {form_schema}")

        return UnifiedResponse.success(
            message="获取用户表单schema成功",
            data=form_schema
        )

    except Exception as e:
        logger.error(f"获取用户表单schema失败: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        raise UnifiedResponse.internal_error(
            message="获取用户表单schema失败",
            error_type="get_schema_error",
            details=str(e)
        )


@router.get("/table-columns", response_model=dict)
async def get_user_table_columns(
    current_user: dict = Depends(verify_developer_token)
):
    """
    获取用户表格列配置

    根据实体建模中定义的用户实体动态生成表格列配置
    """
    try:
        columns = dynamic_user_service.get_user_table_columns()

        return UnifiedResponse.success(
            message="获取用户表格列配置成功",
            data={
                "columns": columns
            }
        )

    except Exception as e:
        logger.error(f"获取用户表格列配置失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="获取用户表格列配置失败",
            error_type="get_columns_error",
            details=str(e)
        )


@router.get("/{user_id}", response_model=dict)
async def get_user_detail(
    user_id: int,
    current_user: dict = Depends(verify_developer_token),
    db: Session = Depends(get_db)
):
    """
    获取用户详细信息
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnifiedResponse.not_found(
                message="用户不存在",
                error_type="user_not_found"
            )

        user_role = db.query(RoleDBModel).filter(RoleDBModel.id == user.role_id).first()

        return UnifiedResponse.success(
            message="获取用户详情成功",
            data={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "real_name": user.real_name,
                "phone": user.phone,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "avatar_url": user.avatar_url,
                "bio": user.bio,
                "settings": user.settings,
                "password_hash": user.password_hash[:20] + "..." if user.password_hash else None,  # 显示密码哈希的前20个字符
                "role": {
                    "id": user_role.id,
                    "name": user_role.name,
                    "code": user_role.code,
                    "description": user_role.description
                } if user_role else None,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户详情失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="获取用户详情失败",
            error_type="get_detail_error",
            details=str(e)
        )


@router.put("/{user_id}/password", response_model=dict)
async def update_user_password(
    user_id: int,
    request: dict,
    current_user: dict = Depends(verify_developer_token),
    db: Session = Depends(get_db)
):
    """
    更新用户密码
    """
    try:
        new_password = request.get("new_password")
        if not new_password:
            raise UnifiedResponse.bad_request(
                message="新密码不能为空",
                error_type="password_required"
            )

        if len(new_password) < 6:
            raise UnifiedResponse.bad_request(
                message="密码长度不能少于6位",
                error_type="password_too_short"
            )

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnifiedResponse.not_found(
                message="用户不存在",
                error_type="user_not_found"
            )

        # 更新密码哈希
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()

        db.commit()

        return UnifiedResponse.success(
            message="密码更新成功",
            data={
                "user_id": user_id,
                "updated_at": user.updated_at.isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户密码失败: {str(e)}")
        db.rollback()
        raise UnifiedResponse.internal_error(
            message="更新用户密码失败",
            error_type="update_password_error",
            details=str(e)
        )


@router.post("/fix-role-user-counts", response_model=dict)
async def fix_role_user_counts(
    current_user: dict = Depends(verify_developer_token),
    db: Session = Depends(get_db)
):
    """
    修复角色用户数量统计
    重新计算所有角色的用户数量并更新到数据库
    """
    try:
        logger.info("开始修复角色用户数量统计...")

        # 获取所有角色
        roles = db.query(RoleDBModel).all()
        fixed_roles = []

        for role in roles:
            # 计算该角色的实际用户数量
            actual_user_count = db.query(func.count(User.id)).filter(User.role_id == role.id).scalar()

            # 如果实际数量与记录的数量不一致，则更新
            if role.user_count != actual_user_count:
                old_count = role.user_count
                role.user_count = actual_user_count
                fixed_roles.append({
                    "role_id": role.id,
                    "role_name": role.name,
                    "old_count": old_count,
                    "new_count": actual_user_count
                })

        db.commit()

        logger.info(f"角色用户数量统计修复完成，共修复 {len(fixed_roles)} 个角色")

        return UnifiedResponse.success(
            message=f"角色用户数量统计修复完成，共修复 {len(fixed_roles)} 个角色",
            data={
                "fixed_roles": fixed_roles,
                "total_fixed": len(fixed_roles)
            }
        )

    except Exception as e:
        logger.error(f"修复角色用户数量统计失败: {str(e)}")
        db.rollback()
        raise UnifiedResponse.internal_error(
            message="修复角色用户数量统计失败",
            error_type="fix_counts_error",
            details=str(e)
        )


@router.get("/fix-role-user-counts-simple")
async def fix_role_user_counts_simple():
    """
    简单的修复角色用户数量统计（不需要认证，用于测试）
    """
    try:
        from app.core.database import get_db_session
        from sqlalchemy import func

        logger.info("开始修复角色用户数量统计...")

        with get_db_session() as db:
            # 获取所有角色
            roles = db.query(RoleDBModel).all()
            fixed_roles = []

            for role in roles:
                # 计算该角色的实际用户数量
                actual_user_count = db.query(func.count(User.id)).filter(User.role_id == role.id).scalar()

                # 如果实际数量与记录的数量不一致，则更新
                if role.user_count != actual_user_count:
                    old_count = role.user_count
                    role.user_count = actual_user_count
                    fixed_roles.append({
                        "role_id": role.id,
                        "role_name": role.name,
                        "old_count": old_count,
                        "new_count": actual_user_count
                    })

            db.commit()

            logger.info(f"角色用户数量统计修复完成，共修复 {len(fixed_roles)} 个角色")

            return UnifiedResponse.success(
                message=f"角色用户数量统计修复完成，共修复 {len(fixed_roles)} 个角色",
                data={
                    "fixed_roles": fixed_roles,
                    "total_fixed": len(fixed_roles)
                }
            )

    except Exception as e:
        logger.error(f"修复角色用户数量统计失败: {str(e)}")
        raise UnifiedResponse.internal_error(
            message="修复角色用户数量统计失败",
            error_type="fix_counts_simple_error",
            details=str(e)
        )
