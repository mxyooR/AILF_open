"""
角色管理数据库初始化脚本
动态创建角色相关的数据库表和初始化数据
"""
from sqlalchemy import create_engine
from app.core.database import get_db_session, engine
from app.models.role import create_role_tables


def init_role_database():
    """
    初始化角色管理数据库
    动态创建表结构和初始化数据
    """
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)
    
    logger.info("开始初始化角色管理数据库...")
    
    try:
        # 1. 动态创建角色相关的数据库表
        logger.info("创建角色管理数据库表...")
        if create_role_tables(engine):
            logger.info("✅ 角色管理数据库表创建成功")
        else:
            logger.error("❌ 角色管理数据库表创建失败")
            return False
        
        logger.info("角色管理数据库初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 角色管理数据库初始化失败: {e}")
        return False





def check_role_database():
    """检查角色数据库状态"""
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)
    
    try:
        logger.info("检查角色数据库状态...")
        
        with get_db_session() as db:
            from app.models.role import RoleDBModel, PermissionDBModel
            
            # 检查角色数量
            role_count = db.query(RoleDBModel).count()
            logger.info(f"角色数量: {role_count}")
            
            # 检查权限数量
            permission_count = db.query(PermissionDBModel).count()
            logger.info(f"权限数量: {permission_count}")
            
            # 显示角色列表
            if role_count > 0:
                logger.debug("角色列表:")
                roles = db.query(RoleDBModel).all()
                for role in roles:
                    logger.debug(f"  • {role.name} ({role.code}) - {role.status}")
            
            # 显示权限统计
            if permission_count > 0:
                logger.debug("权限统计:")
                permissions = db.query(PermissionDBModel).all()
                resources = {}
                for perm in permissions:
                    resources[perm.resource] = resources.get(perm.resource, 0) + 1
                
                for resource, count in resources.items():
                    logger.debug(f"  • {resource}: {count}个权限")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 检查角色数据库状态失败: {e}")
        return False


if __name__ == "__main__":
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)
    
    # 直接运行此脚本进行数据库初始化
    success = init_role_database()
    if success:
        check_role_database()
        logger.info("✅ 角色管理数据库初始化完成")
    else:
        logger.error("❌ 角色管理数据库初始化失败")
        exit(1)
