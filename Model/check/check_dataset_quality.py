"""
数据集质量检查脚本
检查唯一率和 AMIS 格式合规性
"""

import json
from collections import Counter
import hashlib
from pathlib import Path


def check_amis_schema(schema):
    """检查 AMIS Schema 是否符合标准"""
    errors = []
    
    # 1. 必须有 type 字段
    if 'type' not in schema:
        errors.append('缺少 type 字段')
        return errors
    
    # 2. 顶级 type 必须是 page
    if schema.get('type') != 'page':
        errors.append(f'顶级 type 应为 page，实际为 {schema.get("type")}')
    
    # 3. 必须有 body 字段
    if 'body' not in schema:
        errors.append('缺少 body 字段')
        return errors
    
    body = schema.get('body', {})
    
    # 4. 检查 body 结构
    if isinstance(body, dict):
        # 单个组件
        if body.get('type') == 'form':
            # 表单必须有 api 或 body
            if 'api' not in body and 'body' not in body:
                errors.append('form 缺少 api 或 body')
            
            # 检查 api 结构
            api = body.get('api', {})
            if isinstance(api, dict):
                if 'url' not in api:
                    errors.append('form.api 缺少 url')
                if 'method' not in api:
                    errors.append('form.api 缺少 method')
        
        elif body.get('type') == 'alert':
            # 拒绝响应
            if 'body' not in body:
                errors.append('alert 缺少 body')
    
    elif isinstance(body, list):
        # 多个组件
        for i, item in enumerate(body):
            if not isinstance(item, dict):
                errors.append(f'body[{i}] 不是对象')
            elif 'type' not in item:
                errors.append(f'body[{i}] 缺少 type')
    
    return errors


def get_sample_hash(sample):
    """计算样本哈希"""
    content = json.dumps(sample['messages'], ensure_ascii=False, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()


def get_api_info(schema):
    """从 schema 中提取 api 信息"""
    body = schema.get('body', {})
    if isinstance(body, list):
        for item in body:
            if isinstance(item, dict) and item.get('type') == 'form':
                api = item.get('api', {})
                if isinstance(api, dict):
                    return api.get('url', ''), api.get('data', {})
        return '', {}
    elif isinstance(body, dict):
        api = body.get('api', {})
        if isinstance(api, dict):
            return api.get('url', ''), api.get('data', {})
    return '', {}


def analyze_dataset(dataset_path):
    """分析数据集"""
    print(f'\n📊 {dataset_path.name}')
    print('-' * 40)
    
    samples = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            samples.append(json.loads(line))
    
    # 1. 唯一率分析
    hashes = [get_sample_hash(s) for s in samples]
    unique_hashes = set(hashes)
    unique_rate = len(unique_hashes) / len(samples) * 100
    
    print(f'  总样本数: {len(samples)}')
    print(f'  唯一样本数: {len(unique_hashes)}')
    print(f'  唯一率: {unique_rate:.1f}%')
    
    # 2. 按类型统计唯一率
    type_samples = {}
    for s in samples:
        t = s['metadata']['sample_type']
        if t not in type_samples:
            type_samples[t] = []
        type_samples[t].append(s)
    
    print(f'\n  按类型唯一率:')
    for t, ss in sorted(type_samples.items()):
        t_hashes = [get_sample_hash(s) for s in ss]
        t_unique = len(set(t_hashes))
        t_rate = t_unique / len(ss) * 100
        print(f'    {t}: {len(ss)} 条, 唯一 {t_unique} 条, 唯一率 {t_rate:.1f}%')
    
    # 3. AMIS 格式检查
    print(f'\n  AMIS 格式检查:')
    amis_errors = Counter()
    valid_count = 0
    
    for i, s in enumerate(samples):
        assistant_content = s['messages'][2]['content']
        try:
            schema = json.loads(assistant_content)
            errors = check_amis_schema(schema)
            if errors:
                for e in errors:
                    amis_errors[e] += 1
            else:
                valid_count += 1
        except json.JSONDecodeError:
            amis_errors['JSON 解析失败'] += 1
    
    valid_rate = valid_count / len(samples) * 100
    print(f'    有效样本: {valid_count}/{len(samples)} ({valid_rate:.1f}%)')
    
    if amis_errors:
        print(f'    错误统计:')
        for err, cnt in amis_errors.most_common(5):
            print(f'      - {err}: {cnt} 次')
    
    # 4. 检查 workflow_step 的特殊要求
    print(f'\n  工作流步骤检查:')
    wf_step_samples = [s for s in samples if s['metadata']['sample_type'] == 'workflow_step']
    
    correct_endpoint = 0
    has_workflow_id = 0
    has_node_id = 0
    has_action = 0
    has_ampersand = 0
    
    for s in wf_step_samples:
        try:
            schema = json.loads(s['messages'][2]['content'])
            url, data = get_api_info(schema)
            
            if url == '/api/v1/workflow/state':
                correct_endpoint += 1
            
            if 'workflow_id' in data:
                has_workflow_id += 1
            if 'node_id' in data:
                has_node_id += 1
            if 'action' in data:
                has_action += 1
            if '&' in data:
                has_ampersand += 1
        except:
            pass
    
    if wf_step_samples:
        print(f'    workflow_step 样本数: {len(wf_step_samples)}')
        print(f'    使用 /api/v1/workflow/state: {correct_endpoint} ({correct_endpoint/len(wf_step_samples)*100:.1f}%)')
        print(f'    包含 workflow_id: {has_workflow_id} ({has_workflow_id/len(wf_step_samples)*100:.1f}%)')
        print(f'    包含 node_id: {has_node_id} ({has_node_id/len(wf_step_samples)*100:.1f}%)')
        print(f'    包含 action: {has_action} ({has_action/len(wf_step_samples)*100:.1f}%)')
        print(f'    包含 ampersand-dollar: {has_ampersand} ({has_ampersand/len(wf_step_samples)*100:.1f}%)')
    
    # 5. 检查 workflow_entry 的特殊要求
    print(f'\n  工作流入口检查:')
    wf_entry_samples = [s for s in samples if s['metadata']['sample_type'] == 'workflow_entry']
    
    entry_correct_endpoint = 0
    entry_has_workflow_id = 0
    entry_has_node_id = 0
    
    for s in wf_entry_samples:
        try:
            schema = json.loads(s['messages'][2]['content'])
            url, data = get_api_info(schema)
            
            if url == '/api/v1/workflow/state':
                entry_correct_endpoint += 1
            
            if 'workflow_id' in data:
                entry_has_workflow_id += 1
            if 'node_id' in data:
                entry_has_node_id += 1
        except:
            pass
    
    if wf_entry_samples:
        print(f'    workflow_entry 样本数: {len(wf_entry_samples)}')
        print(f'    使用 /api/v1/workflow/state: {entry_correct_endpoint} ({entry_correct_endpoint/len(wf_entry_samples)*100:.1f}%)')
        print(f'    包含 workflow_id: {entry_has_workflow_id} ({entry_has_workflow_id/len(wf_entry_samples)*100:.1f}%)')
        print(f'    包含 node_id: {entry_has_node_id} ({entry_has_node_id/len(wf_entry_samples)*100:.1f}%)')
    
    # 6. 检查图表类 Schema
    print(f'\n  图表 Schema 检查:')
    chart_count = 0
    chart_valid = 0
    chart_types = Counter()
    
    for s in samples:
        try:
            schema = json.loads(s['messages'][2]['content'])
            body = schema.get('body', {})
            
            # 检查是否包含 chart 组件
            has_chart = False
            if isinstance(body, dict) and body.get('type') == 'chart':
                has_chart = True
            elif isinstance(body, list):
                for item in body:
                    if isinstance(item, dict):
                        if item.get('type') == 'chart':
                            has_chart = True
                        elif item.get('type') == 'service':
                            # 检查 service 内部是否有 chart
                            service_body = item.get('body', [])
                            if isinstance(service_body, list):
                                for sb in service_body:
                                    if isinstance(sb, dict) and sb.get('type') == 'chart':
                                        has_chart = True
            
            if has_chart:
                chart_count += 1
                # 检查 chart 配置是否有效
                config = None
                if isinstance(body, dict) and body.get('type') == 'chart':
                    config = body.get('config', {})
                elif isinstance(body, list):
                    for item in body:
                        if isinstance(item, dict) and item.get('type') == 'chart':
                            config = item.get('config', {})
                            break
                
                if config and 'series' in config:
                    chart_valid += 1
                    # 统计图表类型
                    series = config.get('series', [])
                    if series and isinstance(series, list):
                        chart_type = series[0].get('type', 'unknown')
                        chart_types[chart_type] += 1
        except:
            pass
    
    print(f'    图表样本数: {chart_count}')
    if chart_count > 0:
        print(f'    有效图表: {chart_valid} ({chart_valid/chart_count*100:.1f}%)')
        print(f'    图表类型分布:')
        for ct, cnt in chart_types.most_common():
            print(f'      - {ct}: {cnt}')
    
    # 7. 检查管理员 API 覆盖率
    print(f'\n  管理员 API 检查:')
    admin_api_count = 0
    admin_api_urls = set()
    
    for s in samples:
        if s['metadata']['sample_type'] == 'api_only':
            try:
                schema = json.loads(s['messages'][2]['content'])
                body = schema.get('body', {})
                
                # 检查是否是管理员 API（路径包含 /admin/）
                url = ''
                if isinstance(body, dict):
                    api = body.get('api', {})
                    if isinstance(api, dict):
                        url = api.get('url', '')
                    elif body.get('type') == 'chart':
                        api = body.get('api', {})
                        if isinstance(api, dict):
                            url = api.get('url', '')
                
                if '/admin/' in url:
                    admin_api_count += 1
                    admin_api_urls.add(url)
            except:
                pass
    
    print(f'    管理员 API 样本数: {admin_api_count}')
    print(f'    唯一管理员 API 数: {len(admin_api_urls)}')


if __name__ == "__main__":
    print('=' * 60)
    print('数据集质量分析报告')
    print('=' * 60)
    
    model_dir = Path(__file__).parent.parent
    
    # 检查 V7 和 V8 数据集
    for dataset_name in ['dataset_v7.jsonl', 'dataset_v8.jsonl', 'dataset_v7_val.jsonl']:
        dataset_path = model_dir / dataset_name
        if dataset_path.exists():
            analyze_dataset(dataset_path)
    
    print('\n' + '=' * 60)
    print('分析完成')
    print('=' * 60)
