"""
数据库初始化脚本
创建数据库和表结构
"""
import sys
import os

# 添加app目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

import pymysql
from app.config import settings
from app.core.database import init_database, create_tables, engine
from app.models.scenario import ScenarioDBModel  # 导入模型以确保表被创建
from app.models.entity import EntityDBModel, EntityFieldDBModel, EntityRelationshipDBModel  # 导入实体模型（不再需要EntityRecordDBModel）


def create_database_if_not_exists():
    """创建数据库（如果不存在）"""
    try:
        # 连接到MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ 数据库 '{settings.DB_NAME}' 创建成功或已存在")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 创建数据库失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始初始化AILF数据库...")
    print("=" * 50)
    
    # 显示数据库配置
    print(f"数据库主机: {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"数据库名称: {settings.DB_NAME}")
    print(f"数据库用户: {settings.DB_USER}")
    print("-" * 50)
    
    # 1. 创建数据库
    print("📝 步骤1: 创建数据库...")
    if not create_database_if_not_exists():
        print("❌ 数据库创建失败，退出")
        return False
    
    # 2. 初始化数据库连接和表结构
    print("📝 步骤2: 初始化表结构...")
    if not init_database():
        print("❌ 表结构初始化失败，退出")
        return False
    
    # 3. 验证表是否创建成功
    print("📝 步骤3: 验证表结构...")
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # 检查表是否存在（不再检查entity_records和form相关表）
            tables_to_check = [
                'scenarios', 'entities', 'entity_fields',
                'entity_relationships'
            ]

            for table_name in tables_to_check:
                result = conn.execute(text(f"SHOW TABLES LIKE '{table_name}'"))
                if result.fetchone():
                    print(f"✅ {table_name}表创建成功")
                else:
                    print(f"❌ {table_name}表未找到")
                    return False

            # 显示scenarios表结构
            result = conn.execute(text("DESCRIBE scenarios"))
            columns = result.fetchall()
            print("📋 scenarios表结构:")
            for column in columns:
                print(f"  - {column[0]}: {column[1]}")

            # 显示entities表结构
            result = conn.execute(text("DESCRIBE entities"))
            columns = result.fetchall()
            print("📋 entities表结构:")
            for column in columns:
                print(f"  - {column[0]}: {column[1]}")

    except Exception as e:
        print(f"❌ 验证表结构失败: {e}")
        return False
    
    print("=" * 50)
    print("🎉 数据库初始化完成！")
    print("💡 现在可以启动AILF后端服务了")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
