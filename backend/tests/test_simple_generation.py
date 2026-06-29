#!/usr/bin/env python3
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
简单代码生成测试
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def get_auth_headers():
    try:
        with open("dev_token.txt", "r") as f:
            token = f.read().strip()
        return {"Authorization": f"Bearer {token}"}
    except FileNotFoundError:
        return {}

def test_simple_generation():
    headers = get_auth_headers()
    
    # 简单的生成请求
    data = {
        "project_name": "test_simple",
        "description": "简单测试项目",
        "entities": [
            {
                "name": "User",
                "description": "用户",
                "fields": [
                    {"name": "name", "type": "string", "required": True, "description": "姓名"},
                    {"name": "email", "type": "string", "required": True, "description": "邮箱"}
                ]
            }
        ],
        "options": {
            "include_tests": True,
            "include_docs": True,
            "framework": "fastapi"
        }
    }
    
    print("发送生成请求...")
    print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/generate-complete", json=data, headers=headers, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"异常: {e}")

if __name__ == "__main__":
    test_simple_generation()
