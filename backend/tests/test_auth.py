#!/usr/bin/env python3
"""
测试用户认证功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from app.api.v1.user_auth import register_user, login_user
from app.schemas.user_auth import UserRegisterRequest, UserLoginRequest
from app.core.database import get_db_session

async def test_register():
    """测试用户注册"""
    print("🧪 测试用户注册...")
    
    # 创建注册请求
    import time
    timestamp = int(time.time())
    register_data = UserRegisterRequest(
        username=f"testuser{timestamp}",
        email=f"testuser{timestamp}@example.com",
        password="password123",
        confirm_password="password123",
        real_name="测试用户"
    )
    
    try:
        with get_db_session() as db:
            result = await register_user(register_data, db)
            print(f"✅ 注册成功: {result}")
            return result
    except Exception as e:
        print(f"❌ 注册失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_login(username):
    """测试用户登录"""
    print("🧪 测试用户登录...")

    # 创建登录请求
    login_data = UserLoginRequest(
        username=username,
        password="password123"
    )
    
    try:
        with get_db_session() as db:
            result = await login_user(login_data, db)
            print(f"✅ 登录成功: {result}")
            return result
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """主测试函数"""
    print("🚀 开始测试用户认证功能...")
    print("-" * 50)
    
    # 测试注册
    register_result = await test_register()

    print("-" * 50)

    # 测试登录
    if register_result:
        # 从注册结果中获取用户名
        try:
            username = register_result.data.get("username")
            if username:
                login_result = await test_login(username)
            else:
                print("⚠️ 无法获取注册用户名，跳过登录测试")
        except Exception as e:
            print(f"⚠️ 解析注册结果失败: {e}")
            print("⚠️ 跳过登录测试")
    else:
        print("⚠️ 跳过登录测试，因为注册失败")
    
    print("-" * 50)
    print("🎉 测试完成!")

if __name__ == "__main__":
    asyncio.run(main())
