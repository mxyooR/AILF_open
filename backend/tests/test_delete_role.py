#!/usr/bin/env python3
"""
测试删除角色功能的独立脚本
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db_session
from app.models.role import RoleDBModel, role_permissions, user_roles
from sqlalchemy import text

def test_delete_role():
    """测试删除角色功能"""
    print("🔍 开始测试删除角色功能...")
    
    try:
        with get_db_session() as db:
            # 查找普通用户角色
            role = db.query(RoleDBModel).filter(RoleDBModel.code == 'regular_user').first()
            
            if not role:
                print("❌ 未找到普通用户角色")
                return
            
            print(f"✅ 找到角色: {role.name} (ID: {role.id})")
            
            # 检查角色权限关联
            role_perm_count = db.execute(
                text("SELECT COUNT(*) FROM role_permissions WHERE role_id = :role_id"),
                {"role_id": role.id}
            ).scalar()
            print(f"📊 角色权限关联数量: {role_perm_count}")
            
            # 检查用户角色关联
            user_role_count = db.execute(
                text("SELECT COUNT(*) FROM user_roles WHERE role_id = :role_id"),
                {"role_id": role.id}
            ).scalar()
            print(f"👥 用户角色关联数量: {user_role_count}")
            
            # 尝试删除关联记录
            if role_perm_count > 0:
                print("🔗 删除角色权限关联记录...")
                db.execute(
                    text("DELETE FROM role_permissions WHERE role_id = :role_id"),
                    {"role_id": role.id}
                )
                print("✅ 角色权限关联记录删除成功")
            
            if user_role_count > 0:
                print("👥 删除用户角色关联记录...")
                db.execute(
                    text("DELETE FROM user_roles WHERE role_id = :role_id"),
                    {"role_id": role.id}
                )
                print("✅ 用户角色关联记录删除成功")
            
            # 尝试删除角色
            print("🗑️ 删除角色记录...")
            db.delete(role)
            db.commit()
            print("🎉 角色删除成功！")
            
    except Exception as e:
        import traceback
        print(f"❌ 删除失败: {str(e)}")
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    test_delete_role()
