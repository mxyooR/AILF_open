"""验证 AMIS Schema 是否符合标准"""
import json
import sys

def validate_amis_schema(dataset_path):
    with open(dataset_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    errors = []
    warnings = []
    
    # 有效的顶级 type
    valid_top_types = ['page']
    
    # 有效的 body 组件类型
    valid_body_types = ['form', 'crud', 'table', 'chart', 'service', 'panel', 'grid', 'flex', 
                        'tpl', 'container', 'list', 'cards', 'wrapper', 'divider', 'alert']
    
    # 有效的表单字段类型
    valid_field_types = ['input-text', 'input-number', 'input-email', 'input-password', 'textarea', 
                         'select', 'checkboxes', 'radios', 'switch', 'input-date', 'input-datetime',
                         'input-date-range', 'input-file', 'input-image', 'input-time', 'hidden',
                         'input-rich-text', 'input-color', 'input-rating', 'input-range', 'input-tag',
                         'input-tree', 'input-table', 'combo', 'group', 'fieldset', 'static', 'tpl',
                         'button', 'submit', 'reset', 'action', 'divider', 'alert', 'card', 'grid']
    
    # 有效的图表类型
    valid_chart_series_types = ['pie', 'line', 'bar', 'scatter', 'radar', 'gauge', 'funnel']
    
    for i, line in enumerate(lines):
        sample = json.loads(line)
        amis_str = sample['messages'][2]['content']
        sample_type = sample['metadata']['sample_type']
        
        try:
            amis = json.loads(amis_str)
        except:
            errors.append(f'样本 {i+1} ({sample_type}): AMIS Schema 不是有效 JSON')
            continue
        
        # 1. 检查顶级 type 必须是 page
        if amis.get('type') != 'page':
            errors.append(f'样本 {i+1} ({sample_type}): 顶级 type 不是 page，而是 {amis.get("type")}')
        
        # 2. 检查 body 存在
        body = amis.get('body')
        if body is None:
            errors.append(f'样本 {i+1} ({sample_type}): 缺少 body')
            continue
        
        # 3. 检查 body 类型
        if isinstance(body, dict):
            body_type = body.get('type')
            if body_type not in valid_body_types:
                warnings.append(f'样本 {i+1} ({sample_type}): body type "{body_type}" 不在常见类型中')
            
            # 4. 如果是 form，检查 api 配置
            if body_type == 'form':
                api = body.get('api')
                if api:
                    if isinstance(api, dict):
                        if 'url' not in api:
                            errors.append(f'样本 {i+1} ({sample_type}): form.api 缺少 url')
                        if 'method' not in api:
                            warnings.append(f'样本 {i+1} ({sample_type}): form.api 缺少 method')
                        
                        # 检查 data 中是否有 "&": "$"
                        data = api.get('data', {})
                        if isinstance(data, dict):
                            if '&' not in data:
                                warnings.append(f'样本 {i+1} ({sample_type}): form.api.data 缺少 "&": "$"')
                
                # 检查表单字段
                form_body = body.get('body', [])
                if isinstance(form_body, list):
                    for field in form_body:
                        if isinstance(field, dict):
                            field_type = field.get('type')
                            if field_type and field_type not in valid_field_types:
                                warnings.append(f'样本 {i+1} ({sample_type}): 表单字段 type "{field_type}" 不在常见类型中')
            
            # 5. 如果是 chart，检查 config
            if body_type == 'chart':
                config = body.get('config')
                api = body.get('api')
                if not config:
                    errors.append(f'样本 {i+1} ({sample_type}): chart 缺少 config')
                if not api:
                    errors.append(f'样本 {i+1} ({sample_type}): chart 缺少 api')
                if config:
                    series = config.get('series', [])
                    for s in series:
                        if isinstance(s, dict):
                            chart_type = s.get('type')
                            if chart_type and chart_type not in valid_chart_series_types:
                                warnings.append(f'样本 {i+1} ({sample_type}): 图表 series type "{chart_type}" 不在常见类型中')
        
        elif isinstance(body, list):
            # body 是数组，检查每个元素
            for j, item in enumerate(body):
                if isinstance(item, dict):
                    item_type = item.get('type')
                    if item_type and item_type not in valid_body_types + ['card', 'tpl', 'button', 'action', 'service']:
                        warnings.append(f'样本 {i+1} ({sample_type}): body[{j}] type "{item_type}" 不在常见类型中')
    
    print(f'总样本数: {len(lines)}')
    print(f'错误数: {len(errors)}')
    print(f'警告数: {len(warnings)}')
    
    if errors:
        print(f'\n❌ 错误 (前 20 个):')
        for e in errors[:20]:
            print(f'  - {e}')
    
    if warnings:
        print(f'\n⚠️ 警告 (前 20 个):')
        for w in warnings[:20]:
            print(f'  - {w}')
    
    if not errors:
        print('\n✅ 所有样本的 AMIS Schema 基本结构正确')
    
    return errors, warnings

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "Model/dataset_v8.jsonl"
    validate_amis_schema(path)
