"""检查不符合要求的样本"""
import json
from pathlib import Path

model_dir = Path(__file__).parent.parent

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

def get_api_url(schema):
    """从 schema 中提取 api url"""
    url, _ = get_api_info(schema)
    return url

# 检查 workflow_step 中不符合要求的样本
print('检查 workflow_step 中不使用 /api/v1/workflow/state 的样本:')
print('-' * 60)

with open(model_dir / 'dataset_v7.jsonl', 'r', encoding='utf-8') as f:
    count = 0
    for i, line in enumerate(f):
        sample = json.loads(line)
        if sample['metadata']['sample_type'] == 'workflow_step':
            schema = json.loads(sample['messages'][2]['content'])
            url = get_api_url(schema)
            body = schema.get('body', {})
            
            if url != '/api/v1/workflow/state':
                count += 1
                if count <= 3:
                    print(f'样本 {i}:')
                    print(f'  URL: {url}')
                    body_type = body.get("type") if isinstance(body, dict) else "list"
                    print(f'  body type: {body_type}')
                    user_content = sample['messages'][1]['content']
                    print(f'  用户输入: {user_content[:100]}...')
                    print()

print(f'总计: {count} 个不符合的 workflow_step 样本')
print()

# 检查 workflow_entry 中不符合要求的样本
print('检查 workflow_entry 中不使用 /api/v1/workflow/state 的样本:')
print('-' * 60)

with open(model_dir / 'dataset_v7.jsonl', 'r', encoding='utf-8') as f:
    count = 0
    for i, line in enumerate(f):
        sample = json.loads(line)
        if sample['metadata']['sample_type'] == 'workflow_entry':
            schema = json.loads(sample['messages'][2]['content'])
            url = get_api_url(schema)
            body = schema.get('body', {})
            
            if url != '/api/v1/workflow/state':
                count += 1
                if count <= 3:
                    print(f'样本 {i}:')
                    print(f'  URL: {url}')
                    body_type = body.get("type") if isinstance(body, dict) else "list"
                    print(f'  body type: {body_type}')
                    user_content = sample['messages'][1]['content']
                    print(f'  用户输入: {user_content[:100]}...')
                    print()

print(f'总计: {count} 个不符合的 workflow_entry 样本')


# 更详细的检查
print('\n' + '=' * 60)
print('详细检查 workflow_step 样本的 api.data 字段:')
print('=' * 60)

with open(model_dir / 'dataset_v7.jsonl', 'r', encoding='utf-8') as f:
    missing_fields = {'workflow_id': 0, 'node_id': 0, 'action': 0, 'ampersand': 0}
    total_wf_step = 0
    
    for i, line in enumerate(f):
        sample = json.loads(line)
        if sample['metadata']['sample_type'] == 'workflow_step':
            total_wf_step += 1
            schema = json.loads(sample['messages'][2]['content'])
            url, data = get_api_info(schema)
            
            if 'workflow_id' not in data:
                missing_fields['workflow_id'] += 1
            if 'node_id' not in data:
                missing_fields['node_id'] += 1
            if 'action' not in data:
                missing_fields['action'] += 1
            if '&' not in data:
                missing_fields['ampersand'] += 1

print(f'workflow_step 总数: {total_wf_step}')
print(f'缺少 workflow_id: {missing_fields["workflow_id"]}')
print(f'缺少 node_id: {missing_fields["node_id"]}')
print(f'缺少 action: {missing_fields["action"]}')
print(f'缺少 ampersand: {missing_fields["ampersand"]}')

# 检查一个正常的样本
print('\n' + '=' * 60)
print('示例 workflow_step 样本:')
print('=' * 60)

with open(model_dir / 'dataset_v7.jsonl', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        sample = json.loads(line)
        if sample['metadata']['sample_type'] == 'workflow_step':
            schema = json.loads(sample['messages'][2]['content'])
            url, data = get_api_info(schema)
            print(f'URL: {url}')
            print(f'Data keys: {list(data.keys())}')
            print(f'Data: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}')
            break
