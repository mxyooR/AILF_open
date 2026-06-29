#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户数据检查和创建脚本
检查用户111是否存在，如果不存在则创建
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db_session
from app.models.user import User
from app.models.role import RoleDBModel
import bcrypt
from datetime import datetime

def hash_password(password: str) -> str:
    """密码哈希"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_and_create_user():
    """检查并创建用户111"""
    print("🔍 检查用户111...")
    
    try:
        with get_db_session() as db:
            # 1. 检查用户是否存在
            existing_user = db.query(User).filter(User.username == "111").first()
            
            if existing_user:
                print("✅ 用户111已存在")
                print(f"  - ID: {existing_user.id}")
                print(f"  - 用户名: {existing_user.username}")
                print(f"  - 邮箱: {existing_user.email}")
                print(f"  - 真实姓名: {existing_user.real_name}")
                print(f"  - 角色ID: {existing_user.role_id}")
                print(f"  - 激活状态: {existing_user.is_active}")
                print(f"  - 创建时间: {existing_user.created_at}")
                
                # 检查角色信息
                user_role = db.query(RoleDBModel).filter(RoleDBModel.id == existing_user.role_id).first()
                if user_role:
                    print(f"  - 角色名称: {user_role.name} ({user_role.code})")
                    print(f"  - 角色描述: {user_role.description}")
                    print(f"  - 角色状态: {user_role.status}")
                else:
                    print("  - ⚠️  角色信息缺失!")
                
                return existing_user
            else:
                print("❌ 用户111不存在，开始创建...")
                
                # 2. 查找医院管理员角色
                admin_role = db.query(RoleDBModel).filter(
                    RoleDBModel.name.like('%医院%管理%')
                ).first()
                
                if not admin_role:
                    # 查找管理员角色
                    admin_role = db.query(RoleDBModel).filter(
                        RoleDBModel.name.like('%管理员%')
                    ).first()
                
                if not admin_role:
                    # 查找任何可用的角色
                    admin_role = db.query(RoleDBModel).filter(
                        RoleDBModel.status == 'active'
                    ).first()
                
                if not admin_role:
                    print("❌ 未找到合适的管理员角色")
                    return None
                
                print(f"🏷️  使用角色: {admin_role.name} ({admin_role.code})")
                
                # 3. 创建用户
                hashed_password = hash_password("123456")
                
                new_user = User(
                    username="111",
                    email="111@test.com",
                    password_hash=hashed_password,
                    real_name="测试管理员",
                    phone="13800138111",
                    role_id=admin_role.id,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                
                print("✅ 用户111创建成功!")
                print(f"  - ID: {new_user.id}")
                print(f"  - 用户名: {new_user.username}")
                print(f"  - 邮箱: {new_user.email}")
                print(f"  - 角色: {admin_role.name}")
                
                return new_user
                
    except Exception as e:
        print(f"❌ 检查/创建用户失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return None

def check_patient_apis_authorization():
    """检查患者API的权限配置"""
    print("\n🔍 检查患者API权限配置...")
    
    try:
        with get_db_session() as db:
            # 查询所有角色
            roles = db.query(RoleDBModel).all()
            print(f"📊 系统中的角色 ({len(roles)} 个):")
            
            for role in roles:
                print(f"  - {role.name} (code: {role.code}, 状态: {role.status}, 用户数: {role.user_count})")
            
            # 检查动态路由中的患者API
            from app.models.api_route import APIRouteDBModel
            
            patient_apis = db.query(APIRouteDBModel).filter(
                APIRouteDBModel.api_id.like('%patient%')
            ).all()
            
            print(f"\n🏥 患者相关API ({len(patient_apis)} 个):")
            for api in patient_apis:
                print(f"  - {api.name} ({api.api_id}): {api.method} {api.endpoint}")
                print(f"    状态: {api.status}, 调用次数: {api.call_count}")
            
            # 检查是否有权限相关的表
            try:
                from sqlalchemy import text
                result = db.execute(text("SHOW TABLES LIKE '%permission%'"))
                permission_tables = result.fetchall()
                print(f"\n🔐 权限相关表: {[table[0] for table in permission_tables]}")
            except Exception as e:
                print(f"\n🔐 权限配置检查跳过: {e}")
            
    except Exception as e:
        print(f"❌ 检查权限配置失败: {e}")

def main():
    print("=" * 80)
    print("🔧 用户数据检查和创建")
    print("=" * 80)
    
    # 1. 检查/创建用户111
    user = check_and_create_user()
    
    if user:
        # 2. 检查患者API权限配置
        check_patient_apis_authorization()
    else:
        print("❌ 用户创建失败，无法继续检查权限配置")

if __name__ == "__main__":
    main()
