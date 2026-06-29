#!/usr/bin/env python3
"""
批量修复实体管理API认证保护脚本
"""

import re

def fix_entity_auth():
    """修复实体管理API的认证保护"""
    file_path = "backend/app/api/v1/entity.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有需要修复的函数
    functions_to_fix = [
        "create_entity",
        "get_entity_detail", 
        "update_entity",
        "delete_entity",
        "get_entity_records",
        "create_entity_record",
        "update_entity_record", 
        "delete_entity_record",
        "get_entity_relationships",
        "create_entity_relationship",
        "delete_entity_relationship"
    ]
    
    for func_name in functions_to_fix:
        # 查找函数定义
        pattern = rf'async def {func_name}\(([^)]*)\):'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            params = match.group(1).strip()
            
            # 检查是否已经有认证保护
            if '_: dict = Depends(verify_developer_token)' not in params:
                # 添加认证参数
                if params:
                    if not params.endswith(','):
                        params += ','
                    params += '\n    _: dict = Depends(verify_developer_token)'
                else:
                    params = '_: dict = Depends(verify_developer_token)'
                
                # 替换函数定义
                new_func_def = f'async def {func_name}(\n    {params}\n):'
                content = content.replace(match.group(0), new_func_def)
                print(f"✅ 已为函数 {func_name} 添加认证保护")
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("🎉 实体管理API认证保护修复完成！")

if __name__ == "__main__":
    fix_entity_auth()
