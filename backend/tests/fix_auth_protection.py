#!/usr/bin/env python3
"""
批量修复API认证保护脚本
为所有开发者API添加token认证保护
"""

import os
import re
from pathlib import Path

# 需要修复的API文件列表
API_FILES = [
    "backend/app/api/v1/entity.py",
    "backend/app/api/v1/relationship.py", 
    "backend/app/api/config.py",
    "backend/app/api/role.py",
    "backend/app/api/permission_control.py",
    "backend/app/api/workflow.py",
    "backend/app/api/form.py",
    "backend/app/api/business.py"
]

def add_auth_import(file_path):
    """添加认证导入"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经导入了认证模块
    if 'from app.core.auth import verify_developer_token' in content:
        print(f"✅ {file_path} 已经有认证导入")
        return content
    
    # 查找FastAPI导入行
    fastapi_import_pattern = r'from fastapi import ([^)]+)'
    match = re.search(fastapi_import_pattern, content)
    
    if match:
        imports = match.group(1)
        if 'Depends' not in imports:
            # 添加Depends到导入
            new_imports = imports.rstrip() + ', Depends'
            content = content.replace(match.group(0), f'from fastapi import {new_imports}')
        
        # 在FastAPI导入后添加认证导入
        insert_pos = match.end()
        lines = content[:insert_pos].split('\n')
        lines.append('from app.core.auth import verify_developer_token')
        content = '\n'.join(lines) + content[insert_pos:]
        
        print(f"✅ 已为 {file_path} 添加认证导入")
    else:
        print(f"❌ 无法找到FastAPI导入行: {file_path}")
    
    return content

def add_auth_to_endpoints(content, file_path):
    """为API端点添加认证保护"""
    # 查找所有API端点函数
    endpoint_pattern = r'async def ([^(]+)\(([^)]*)\):'
    
    def replace_func(match):
        func_name = match.group(1)
        params = match.group(2).strip()
        
        # 跳过已经有认证保护的函数
        if '_: dict = Depends(verify_developer_token)' in params:
            return match.group(0)
        
        # 添加认证参数
        if params:
            if not params.endswith(','):
                params += ','
            params += '\n    _: dict = Depends(verify_developer_token)'
        else:
            params = '_: dict = Depends(verify_developer_token)'
        
        result = f'async def {func_name}(\n    {params}\n):'
        print(f"  ✅ 已为函数 {func_name} 添加认证保护")
        return result
    
    # 只处理路由装饰器后的函数
    router_pattern = r'@router\.(get|post|put|delete|patch)\([^)]*\)\s*\n(.*?\n)*?async def ([^(]+)\(([^)]*)\):'
    
    def replace_router_func(match):
        decorator = match.group(0)
        # 提取函数定义部分
        func_match = re.search(r'async def ([^(]+)\(([^)]*)\):', decorator)
        if func_match:
            func_name = func_match.group(1)
            params = func_match.group(2).strip()
            
            # 跳过已经有认证保护的函数
            if '_: dict = Depends(verify_developer_token)' in params:
                return decorator
            
            # 添加认证参数
            if params:
                if not params.endswith(','):
                    params += ','
                params += '\n    _: dict = Depends(verify_developer_token)'
            else:
                params = '_: dict = Depends(verify_developer_token)'
            
            # 重构函数定义
            new_func_def = f'async def {func_name}(\n    {params}\n):'
            result = decorator.replace(func_match.group(0), new_func_def)
            print(f"  ✅ 已为路由函数 {func_name} 添加认证保护")
            return result
        
        return decorator
    
    modified_content = re.sub(router_pattern, replace_router_func, content, flags=re.MULTILINE | re.DOTALL)
    
    return modified_content

def fix_file(file_path):
    """修复单个文件"""
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    print(f"\n🔧 修复文件: {file_path}")
    
    try:
        # 添加认证导入
        content = add_auth_import(file_path)
        
        # 为端点添加认证保护
        content = add_auth_to_endpoints(content, file_path)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 文件修复完成: {file_path}")
        
    except Exception as e:
        print(f"❌ 修复文件失败 {file_path}: {e}")

def main():
    """主函数"""
    print("🚀 开始批量修复API认证保护...")
    
    for file_path in API_FILES:
        fix_file(file_path)
    
    print("\n🎉 批量修复完成！")
    print("\n📋 修复总结:")
    print("- 已为所有开发者API添加token认证保护")
    print("- 添加了必要的导入语句")
    print("- 确保未认证用户无法访问开发者功能")

if __name__ == "__main__":
    main()
