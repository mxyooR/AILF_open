#!/usr/bin/env python3
"""
权限矩阵API测试脚本
测试权限矩阵API是否正常工作
"""
import requests
import json
import os
import sys

def test_permission_matrix():
    """测试权限矩阵API"""
    print("🔍 测试权限矩阵API...")
    
    # 读取开发者token
    try:
        with open('dev_token.txt', 'r') as f:
            token = f.read().strip()
        print("✅ 成功读取开发者token")
    except FileNotFoundError:
        print("❌ 未找到dev_token.txt文件")
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        # 调用权限矩阵API
        print("📡 正在调用权限矩阵API...")
        response = requests.get('http://localhost:5000/api/v1/permissions/matrix', headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 成功获取权限矩阵!")
            
            # 检查响应结构
            print(f"响应结构: {list(data.keys())}")
            
            if 'data' in data:
                data_content = data['data']
                print(f"data字段包含: {list(data_content.keys())}")
                
                if 'matrix' in data_content:
                    matrix = data_content['matrix']
                    print(f"matrix包含: {list(matrix.keys())}")
                    
                    # 显示角色信息
                    roles = matrix.get('roles', [])
                    print(f"角色数量: {len(roles)}")
                    if roles:
                        print("角色列表:")
                        for role in roles:
                            print(f"  - {role.get('name', '未知')} (代码: {role.get('code', '未知')})")
                    
                    # 显示API信息
                    apis = matrix.get('apis', [])
                    print(f"API数量: {len(apis)}")
                    if apis:
                        print("API列表:")
                        for api in apis:
                            print(f"  - {api.get('name', '未知')} [{api.get('method', '未知')}] {api.get('endpoint', '未知')}")
                    
                    # 显示权限矩阵
                    permissions = matrix.get('permissions', {})
                    print(f"权限矩阵: {len(permissions)} 个角色的权限配置")
                    
                # 显示统计信息
                if 'statistics' in data_content:
                    stats = data_content['statistics']
                    print("📊 统计信息:")
                    for key, value in stats.items():
                        print(f"  - {key}: {value}")
                
                print("\n完整响应数据:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return True
                
        else:
            print("❌ 请求失败")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败 - 请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("权限矩阵API测试")
    print("=" * 60)
    
    # 切换到正确的目录
    if not os.path.exists('dev_token.txt'):
        if os.path.exists('../dev_token.txt'):
            os.chdir('..')
            print("📁 切换到上级目录")
        else:
            print("❌ 未找到dev_token.txt文件")
            return
    
    success = test_permission_matrix()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 权限矩阵API测试成功!")
    else:
        print("❌ 权限矩阵API测试失败!")
    print("=" * 60)

if __name__ == "__main__":
    main()
