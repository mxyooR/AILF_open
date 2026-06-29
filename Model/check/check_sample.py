"""检查训练集样本的详细内容"""
import json
import random

# 读取数据集
samples = []
with open('../dataset_v5.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        samples.append(json.loads(line))

print(f"总样本数: {len(samples)}")

# 统计各类型
type_counts = {}
for s in samples:
    t = s.get('metadata', {}).get('sample_type', 'unknown')
    type_counts[t] = type_counts.get(t, 0) + 1
print("类型分布:", type_counts)

# 每种类型抽取 1 条
random.seed(456)
sample_types = ['api_only', 'workflow_entry', 'workflow_step', 'rejection', 'rejection_mismatch']

for st in sample_types:
    type_samples = [s for s in samples if s.get('metadata', {}).get('sample_type') == st]
    if not type_samples:
        continue
    
    sample = random.choice(type_samples)
    
    print("\n" + "="*70)
    print(f"【{st.upper()}】 域: {sample['metadata']['domain']}")
    print("="*70)
    
    print("\n【用户输入】")
    print(sample['messages'][1]['content'])
    
    print("\n【图谱节点】")
    graph = sample.get('graph_input', {})
    nodes = graph.get('nodes', [])
    edges = graph.get('edges', [])
    
    print(f"节点总数: {len(nodes)}")
    for i, node in enumerate(nodes[:8]):  # 最多显示8个
        node_type = node.get('type', 'unknown')
        node_id = node.get('id', 'N/A')
        if node_type == 'api':
            print(f"  [{i+1}] API: {node.get('path', '')} ({node.get('desc', '')[:25]})")
        elif node_type == 'workflow':
            print(f"  [{i+1}] Workflow: {node_id} - {node.get('name', '')}")
        elif node_type in ('user_input', 'api_call'):
            print(f"  [{i+1}] WorkflowNode({node_type}): {node.get('name', '')}")
        elif node_type == 'field':
            print(f"  [{i+1}] Field: {node.get('name', '')} - {node.get('label', '')}")
        else:
            print(f"  [{i+1}] {node_type}: {node_id}")
    if len(nodes) > 8:
        print(f"  ... 还有 {len(nodes) - 8} 个节点")
    
    print(f"\n边数: {len(edges)}")
    
    print("\n【AMIS Schema (截取)】")
    assistant_content = sample['messages'][2]['content']
    schema = json.loads(assistant_content)
    
    # 提取关键信息
    body = schema.get('body', {})
    if isinstance(body, list):
        for item in body:
            if item.get('type') == 'form':
                api_url = item.get('api', {}).get('url', '')
                print(f"api.url: {api_url}")
                break
    else:
        api_url = body.get('api', {}).get('url', '')
        api_data = body.get('api', {}).get('data', {})
        print(f"api.url: {api_url}")
        if api_data:
            print(f"api.data: {api_data}")
