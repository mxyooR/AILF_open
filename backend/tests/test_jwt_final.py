#!/usr/bin/env python3
"""
测试JWT验证逻辑
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.auth.jwt_handler import verify_token
from app.api.v1.ai import get_current_user_optional
from app.core.database import get_db

def test_jwt_verification():
    """测试JWT验证"""
    # 测试token（从浏览器获取）
    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMiwidXNlcm5hbWUiOiJwbGF5d3JpZ2h0X3Rlc3RfdXNlciIsInJvbGVfaWQiOiJyb2xlXzE3NTMzNjIyMTA1ODJfMzM5MCIsInJvbGVfY29kZSI6InJlZ3VsYXJfdXNlciIsInVzZXJfdHlwZSI6InVzZXIiLCJpYXQiOjE3NTQzMjMxMjIsImV4cCI6MTc1NDMyNjcyMn0.nOPOUIZYI8NMcXy6mZO8pkkZ9TaPStFsPWsF6Zi53-U"

    print("🔍 测试JWT验证逻辑")
    print("-" * 50)

    # 1. 测试基础JWT验证
    try:
        print("1️⃣ 测试基础JWT验证...")
        payload = verify_token(test_token)
        print(f"✅ JWT验证成功: {payload}")
    except Exception as e:
        print(f"❌ JWT验证失败: {e}")
        return

    # 2. 测试get_current_user_optional函数
    try:
        print("\n2️⃣ 测试get_current_user_optional函数...")
        db = next(get_db())
        user_info = get_current_user_optional(test_token, db)

        if user_info:
            print(f"✅ 用户验证成功:")
            print(f"   用户ID: {user_info.get('user_id')}")
            print(f"   用户名: {user_info.get('username')}")
            print(f"   角色: {user_info.get('role', {}).get('name')}")
            print(f"   权限: {user_info.get('permissions')}")
        else:
            print("❌ 用户验证失败: 返回None")

    except Exception as e:
        print(f"❌ 用户验证异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_jwt_verification()