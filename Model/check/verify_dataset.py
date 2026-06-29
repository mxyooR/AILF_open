"""
验证数据集是否符合后端流程
"""
import json
from pathlib import Path

def verify_dataset():
    # 读取数据集
    dataset_path = Path(__file__).parent.parent / "dataset_v5.jsonl"
    samples = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))

    print(f'总样本数: {len(samples)}')

    # 统计样本类型
    type_counts = {}
    for s in samples:
        t = s.get('metadata', {}).get('sample_type', 'unknown')
        type_counts[t] = type_counts.get(t, 0) + 1

    print(f'\n样本类型分布:')
    for t, c in sorted(type_counts.items()):
        print(f'  - {t}: {c} ({c/len(samples)*100:.1f}%)')

    # 验证 workflow_entry 样本
    print(f'\n验证 workflow_entry 样本:')
    wf_entry_samples = [s for s in samples if s.get('metadata', {}).get('sample_type') == 'workflow_entry']
    valid_wf_entry = 0
    for s in wf_entry_samples[:5]:
        graph_nodes = s.get('graph_input', {}).get('nodes', [])
        wf_nodes = [n for n in graph_nodes if n.get('type') == 'workflow']
        
        # 获取输出中的 workflow_id
        assistant_content = s.get('messages', [{}])[-1].get('content', '{}')
        schema = json.loads(assistant_content)
        body = schema.get('body', {})
        if isinstance(body, list):
            body = body[0] if body else {}
        api_data = body.get('api', {}).get('data', {})
        output_wf_id = api_data.get('workflow_id', '')
        
        # 检查图谱中是否有匹配的 workflow ID
        graph_wf_ids = [n.get('id') for n in wf_nodes]
        
        if output_wf_id in graph_wf_ids:
            valid_wf_entry += 1
            print(f'  [OK] 图谱 Workflow ID 与输出匹配: {output_wf_id}')
        else:
            print(f'  [FAIL] 不匹配: 图谱={graph_wf_ids}, 输出={output_wf_id}')

    # 验证 workflow_step 样本
    print(f'\n验证 workflow_step 样本:')
    wf_step_samples = [s for s in samples if s.get('metadata', {}).get('sample_type') == 'workflow_step']
    valid_wf_step = 0
    for s in wf_step_samples[:5]:
        # 获取用户输入中的 workflow_id
        user_content = s.get('messages', [{}])[1].get('content', '')
        user_wf_id = ''
        for line in user_content.split('\n'):
            if line.startswith('工作流ID：'):
                user_wf_id = line.replace('工作流ID：', '').strip()
                break
        
        # 获取图谱中的节点 ID
        graph_nodes = s.get('graph_input', {}).get('nodes', [])
        wf_node_ids = [n.get('id') for n in graph_nodes if n.get('type') in ('user_input', 'api_call')]
        
        # 检查节点 ID 是否以 workflow_id 开头
        valid = any(nid.startswith(user_wf_id + '_node_') for nid in wf_node_ids)
        
        if valid:
            valid_wf_step += 1
            node_id = wf_node_ids[0] if wf_node_ids else 'N/A'
            print(f'  [OK] 节点 ID 格式正确: {node_id}')
        else:
            print(f'  [FAIL] 格式错误: user_wf_id={user_wf_id}, node_ids={wf_node_ids}')

    # 验证 api_only 样本
    print(f'\n验证 api_only 样本:')
    api_samples = [s for s in samples if s.get('metadata', {}).get('sample_type') == 'api_only']
    valid_api = 0
    for s in api_samples[:5]:
        graph_nodes = s.get('graph_input', {}).get('nodes', [])
        api_paths = [n.get('path') for n in graph_nodes if n.get('type') == 'api']
        
        # 获取输出中的 api.url
        assistant_content = s.get('messages', [{}])[-1].get('content', '{}')
        schema = json.loads(assistant_content)
        body = schema.get('body', {})
        if isinstance(body, list):
            body = body[0] if body else {}
        api_url = body.get('api', {}).get('url', '')
        
        if api_url in api_paths:
            valid_api += 1
            print(f'  [OK] API URL 在图谱中: {api_url}')
        else:
            print(f'  [FAIL] API URL 不在图谱中: {api_url}, 图谱={api_paths[:3]}...')

    # 验证 rejection_mismatch 样本
    print(f'\n验证 rejection_mismatch 样本:')
    mismatch_samples = [s for s in samples if s.get('metadata', {}).get('sample_type') == 'rejection_mismatch']
    valid_mismatch = 0
    for s in mismatch_samples[:5]:
        graph_nodes = s.get('graph_input', {}).get('nodes', [])
        
        # 检查图谱非空
        if len(graph_nodes) > 0:
            # 获取输出标题
            assistant_content = s.get('messages', [{}])[-1].get('content', '{}')
            schema = json.loads(assistant_content)
            title = schema.get('title', '')
            
            if title == '服务不匹配':
                valid_mismatch += 1
                user_content = s.get('messages', [{}])[1].get('content', '')
                instruction = user_content.split('\n')[0].replace('指令：', '')
                graph_domains = set(n.get('domain', '') for n in graph_nodes)
                print(f'  [OK] 图谱非空({len(graph_nodes)}节点), 域={graph_domains}, 指令={instruction[:20]}...')
            else:
                print(f'  [FAIL] 输出标题不正确: {title}')
        else:
            print(f'  [FAIL] 图谱为空')

    # 检查是否有重复节点
    print(f'\n检查重复节点:')
    dup_count = 0
    for s in samples[:100]:
        graph_nodes = s.get('graph_input', {}).get('nodes', [])
        node_ids = [n.get('id') for n in graph_nodes]
        if len(node_ids) != len(set(node_ids)):
            dup_count += 1
            duplicates = [nid for nid in node_ids if node_ids.count(nid) > 1]
            print(f'  [WARN] 发现重复节点: {set(duplicates)}')
    
    if dup_count == 0:
        print(f'  [OK] 前100个样本无重复节点')

    print(f'\n验证完成!')


if __name__ == "__main__":
    verify_dataset()
