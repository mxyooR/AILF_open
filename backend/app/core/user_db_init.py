"""
用户认证数据库初始化
创建用户相关的数据库表和默认数据
"""
from app.core.logging_config import get_logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.database import get_db_engine, Base
from app.models.user import User, UserSession, UserLoginLog
from app.models.role import RoleDBModel

logger = get_logger(__name__)


def init_user_database():
    """初始化用户认证数据库"""
    try:
        logger.info("初始化用户认证数据库...")
        
        # 1. 创建用户相关表
        logger.info("创建用户数据库表...")
        if not create_user_tables():
            return False
        
        # 2. 初始化默认用户数据
        logger.info("初始化默认用户数据...")
        if not init_default_users():
            return False
        
        logger.info("用户认证数据库初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 用户认证数据库初始化失败: {e}")
        return False


def create_user_tables():
    """创建用户相关的数据库表"""
    try:
        engine = get_db_engine()
        
        # 创建用户相关表
        User.__table__.create(engine, checkfirst=True)
        UserSession.__table__.create(engine, checkfirst=True)
        UserLoginLog.__table__.create(engine, checkfirst=True)
        
        logger.info("✅ 用户数据库表创建成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 用户数据库表创建失败: {e}")
        return False


def init_default_users():
    """初始化默认用户数据"""
    try:
        engine = get_db_engine()
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # 检查是否已有用户数据
            existing_count = db.query(User).count()
            if existing_count > 0:
                logger.info(f"✅ 用户数据已存在 ({existing_count} 个)")
                return True
            
            # 获取默认角色
            default_role = db.query(RoleDBModel).filter(
                RoleDBModel.name.in_(["普通用户", "用户", "user"])
            ).first()
            
            if not default_role:
                # 如果没有找到默认角色，使用第一个可用角色
                default_role = db.query(RoleDBModel).filter(
                    RoleDBModel.status == "active"
                ).first()
            
            if not default_role:
                logger.warning("⚠️ 没有找到可用的角色，跳过默认用户创建")
                return True
            
            # 创建默认测试用户
            import bcrypt
            
            default_users = [
                {
                    "username": "testuser",
                    "email": "test@example.com",
                    "password": "password123",
                    "real_name": "测试用户",
                    "role_id": default_role.id
                },
                {
                    "username": "admin",
                    "email": "admin@example.com", 
                    "password": "admin123",
                    "real_name": "管理员",
                    "role_id": default_role.id
                }
            ]
            
            for user_data in default_users:
                # 检查用户是否已存在
                existing_user = db.query(User).filter(
                    (User.username == user_data["username"]) |
                    (User.email == user_data["email"])
                ).first()
                
                if existing_user:
                    continue
                
                # 创建密码哈希
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(
                    user_data["password"].encode('utf-8'), 
                    salt
                ).decode('utf-8')
                
                # 创建用户
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=password_hash,
                    real_name=user_data["real_name"],
                    role_id=user_data["role_id"],
                    is_active=True,
                    is_verified=True
                )
                
                db.add(user)
            
            db.commit()
            
            # 统计创建的用户数量
            total_users = db.query(User).count()
            logger.info(f"✅ 默认用户数据初始化成功 ({total_users} 个用户)")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ 默认用户数据初始化失败: {e}")
        return False


def check_user_database():
    """检查用户数据库状态"""
    try:
        engine = get_db_engine()
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # 检查表是否存在
            tables_exist = True
            try:
                db.execute(text("SELECT 1 FROM users LIMIT 1"))
                db.execute(text("SELECT 1 FROM user_sessions LIMIT 1"))
                db.execute(text("SELECT 1 FROM user_login_logs LIMIT 1"))
            except Exception:
                tables_exist = False
            
            if not tables_exist:
                logger.warning("⚠️ 用户数据库表不存在")
                return False
            
            # 统计数据
            user_count = db.query(User).count()
            session_count = db.query(UserSession).count()
            log_count = db.query(UserLoginLog).count()
            
            logger.info(f"用户数据库状态:")
            logger.info(f"  用户数量: {user_count}")
            logger.info(f"  会话数量: {session_count}")
            logger.info(f"  登录日志: {log_count}")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ 检查用户数据库状态失败: {e}")
        return False


if __name__ == "__main__":
    # 直接运行时进行初始化
    success = init_user_database()
    if success:
        check_user_database()
    else:
        exit(1)
