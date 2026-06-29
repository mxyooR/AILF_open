"""
权限控制数据库初始化脚本
动态创建权限控制相关的数据库表和初始化数据
"""
from app.core.database import get_db_session, engine
from app.models.permission_control import (
    create_permission_control_tables, init_default_api_endpoints
)


def init_permission_control_database():
    """
    初始化权限控制数据库
    动态创建表结构和初始化数据
    """
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)
    
    logger.info("开始初始化权限控制数据库...")
    
    try:
        # 1. 动态创建权限控制相关的数据库表
        logger.info("创建权限控制数据库表...")
        if create_permission_control_tables(engine):
            logger.info("✅ 权限控制数据库表创建成功")
        else:
            logger.error("❌ 权限控制数据库表创建失败")
            return False
        
        # 2. 初始化默认API端点数据
        logger.info("初始化默认API端点数据...")
        with get_db_session() as db:
            if init_default_api_endpoints(db):
                logger.info("✅ 默认API端点数据初始化成功")
            else:
                logger.error("❌ 默认API端点数据初始化失败")
                return False
        
        logger.info("权限控制数据库初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 权限控制数据库初始化失败: {e}")
        return False


def check_permission_control_database():
    """检查权限控制数据库状态"""
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)
    
    try:
        logger.info("检查权限控制数据库状态...")
        
        with get_db_session() as db:
            from app.models.permission_control import APIEndpointDBModel, PermissionCheckLogDBModel
            
            # 检查API端点数量
            api_count = db.query(APIEndpointDBModel).count()
            logger.info(f"API端点数量: {api_count}")
            
            # 检查权限检查日志数量
            log_count = db.query(PermissionCheckLogDBModel).count()
            logger.info(f"权限检查日志数量: {log_count}")
            
            # 显示API端点列表
            if api_count > 0:
                logger.debug("API端点列表:")
                apis = db.query(APIEndpointDBModel).all()
                for api in apis:
                    logger.debug(f"  • {api.name} ({api.method} {api.endpoint}) - {api.permission}")
            
            # 显示API统计
            if api_count > 0:
                logger.debug("API统计:")
                apis = db.query(APIEndpointDBModel).all()
                resources = {}
                methods = {}
                for api in apis:
                    resources[api.resource] = resources.get(api.resource, 0) + 1
                    methods[api.method] = methods.get(api.method, 0) + 1
                
                logger.debug("  按资源分组:")
                for resource, count in resources.items():
                    logger.debug(f"    • {resource}: {count}个API")
                
                logger.debug("  按HTTP方法分组:")
                for method, count in methods.items():
                    logger.debug(f"    • {method}: {count}个API")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 检查权限控制数据库状态失败: {e}")
        return False


def add_more_api_endpoints():
    """添加更多API端点配置"""
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)
    
    try:
        logger.info("添加更多API端点配置...")
        
        with get_db_session() as db:
            from app.models.permission_control import APIEndpointDBModel
            
            # 检查是否需要添加更多API端点
            existing_count = db.query(APIEndpointDBModel).count()
            if existing_count >= 25:  # 如果已有足够的API端点
                logger.info(f"✅ API端点数据已充足 ({existing_count} 个)")
                return True
            
            # 更多API端点配置
            additional_apis = [
                # 用户管理API
                {
                    "id": "user_list_api",
                    "name": "用户列表API",
                    "endpoint": "/api/users",
                    "method": "GET",
                    "resource": "users",
                    "action": "read",
                    "permission": "users:read",
                    "description": "获取用户列表",
                    "is_public": False,
                    "min_role_level": 5
                },
                {
                    "id": "user_create_api",
                    "name": "创建用户API",
                    "endpoint": "/api/users",
                    "method": "POST",
                    "resource": "users",
                    "action": "create",
                    "permission": "users:create",
                    "description": "创建新用户",
                    "is_public": False,
                    "min_role_level": 7
                },
                {
                    "id": "user_update_api",
                    "name": "更新用户API",
                    "endpoint": "/api/users/{id}",
                    "method": "PUT",
                    "resource": "users",
                    "action": "update",
                    "permission": "users:update",
                    "description": "更新用户信息",
                    "is_public": False,
                    "min_role_level": 7
                },
                {
                    "id": "user_delete_api",
                    "name": "删除用户API",
                    "endpoint": "/api/users/{id}",
                    "method": "DELETE",
                    "resource": "users",
                    "action": "delete",
                    "permission": "users:delete",
                    "description": "删除用户",
                    "is_public": False,
                    "min_role_level": 9
                },
                
                # 角色管理API
                {
                    "id": "role_list_api",
                    "name": "角色列表API",
                    "endpoint": "/api/roles",
                    "method": "GET",
                    "resource": "roles",
                    "action": "read",
                    "permission": "roles:read",
                    "description": "获取角色列表",
                    "is_public": False,
                    "min_role_level": 5
                },
                {
                    "id": "role_create_api",
                    "name": "创建角色API",
                    "endpoint": "/api/roles",
                    "method": "POST",
                    "resource": "roles",
                    "action": "create",
                    "permission": "roles:create",
                    "description": "创建新角色",
                    "is_public": False,
                    "min_role_level": 8
                },
                {
                    "id": "role_update_api",
                    "name": "更新角色API",
                    "endpoint": "/api/roles/{id}",
                    "method": "PUT",
                    "resource": "roles",
                    "action": "update",
                    "permission": "roles:update",
                    "description": "更新角色信息",
                    "is_public": False,
                    "min_role_level": 8
                },
                {
                    "id": "role_delete_api",
                    "name": "删除角色API",
                    "endpoint": "/api/roles/{id}",
                    "method": "DELETE",
                    "resource": "roles",
                    "action": "delete",
                    "permission": "roles:delete",
                    "description": "删除角色",
                    "is_public": False,
                    "min_role_level": 9
                },
                
                # 销售报表API已删除
                {
                    "id": "reports_create_api",
                    "name": "创建报表API",
                    "endpoint": "/api/reports",
                    "method": "POST",
                    "resource": "reports",
                    "action": "create",
                    "permission": "reports:create",
                    "description": "创建自定义报表",
                    "is_public": False,
                    "min_role_level": 6
                },
                {
                    "id": "reports_export_api",
                    "name": "导出报表API",
                    "endpoint": "/api/reports/{id}/export",
                    "method": "POST",
                    "resource": "reports",
                    "action": "export",
                    "permission": "reports:export",
                    "description": "导出报表数据",
                    "is_public": False,
                    "min_role_level": 5
                },
                
                # 分析API
                {
                    "id": "analytics_dashboard_api",
                    "name": "分析仪表板API",
                    "endpoint": "/api/analytics/dashboard",
                    "method": "GET",
                    "resource": "analytics",
                    "action": "read",
                    "permission": "analytics:read",
                    "description": "获取分析仪表板数据",
                    "is_public": False,
                    "min_role_level": 6
                },
                
                # 设置API
                {
                    "id": "settings_read_api",
                    "name": "读取设置API",
                    "endpoint": "/api/settings",
                    "method": "GET",
                    "resource": "settings",
                    "action": "read",
                    "permission": "settings:read",
                    "description": "读取系统设置",
                    "is_public": False,
                    "min_role_level": 5
                },
                {
                    "id": "settings_update_api",
                    "name": "更新设置API",
                    "endpoint": "/api/settings",
                    "method": "PUT",
                    "resource": "settings",
                    "action": "update",
                    "permission": "settings:update",
                    "description": "更新系统设置",
                    "is_public": False,
                    "min_role_level": 8
                }
            ]
            
            # 创建API端点记录
            created_count = 0
            for api_data in additional_apis:
                # 检查是否已存在
                existing = db.query(APIEndpointDBModel).filter(
                    APIEndpointDBModel.id == api_data["id"]
                ).first()
                
                if not existing:
                    api_endpoint = APIEndpointDBModel(**api_data)
                    db.add(api_endpoint)
                    created_count += 1
            
            db.commit()
            logger.info(f"✅ 成功添加 {created_count} 个API端点")
            return True
            
    except Exception as e:
        logger.error(f"❌ 添加API端点失败: {e}")
        return False


if __name__ == "__main__":
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)
    
    # 直接运行此脚本进行数据库初始化
    success = init_permission_control_database()
    if success:
        add_more_api_endpoints()
        check_permission_control_database()
        logger.info("✅ 权限控制数据库初始化完成")
    else:
        logger.error("❌ 权限控制数据库初始化失败")
        exit(1)
