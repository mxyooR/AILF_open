"""
Analyze Dataset - 分析数据集统计信息
"""

import json
from collections import Counter


def analyze_dataset(filepath="dataset_final.jsonl"):
    """分析数据集"""
    print(f"分析数据集: {filepath}\n")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        samples = [json.loads(line) for line in f]
    
    print(f"总样本数: {len(samples)}\n")
    
    task_types = []
    node_types = []
    edge_relations = []
    domains = []
    amis_types = []
    nodes_per_sample = []
    edges_per_sample = []
    
    for sample in samples:
        user_content = sample['messages'][1]['content']
        
        if "Global_Routing" in user_content:
            task_types.append("Global_Routing")
        elif "Workflow_Input" in user_content:
            task_types.append("Workflow_Input")
        elif "Workflow_Execute" in user_content:
            task_types.append("Workflow_Execute")
        else:
            task_types.append("Unknown")
        
        graph_nodes = sample['graph_input']['nodes']
        graph_edges = sample['graph_input']['edges']
        
        nodes_per_sample.append(len(graph_nodes))
        edges_per_sample.append(len(graph_edges))
        
        for node in graph_nodes:
            node_types.append(node['type'])
            domains.append(node.get('domain', 'unknown'))
        
        for edge in graph_edges:
            edge_relations.append(edge['relation'])
        
        assistant_content = sample['messages'][2]['content']
        try:
            assistant_json = json.loads(assistant_content)
            amis_types.append(assistant_json.get('type', 'unknown'))
        except:
            amis_types.append('parse_error')
    
    print("=== 任务类型分布 ===")
    task_counter = Counter(task_types)
    for task_type, count in task_counter.most_common():
        percentage = (count / len(samples)) * 100
        print(f"  {task_type}: {count} ({percentage:.1f}%)")
    
    print("\n=== 节点类型分布 ===")
    node_counter = Counter(node_types)
    for node_type, count in node_counter.most_common():
        print(f"  {node_type}: {count}")
    
    print("\n=== 域分布 ===")
    domain_counter = Counter(domains)
    for domain, count in domain_counter.most_common():
        print(f"  {domain}: {count}")
    
    if edge_relations:
        print("\n=== 边关系分布 ===")
        edge_counter = Counter(edge_relations)
        for relation, count in edge_counter.most_common():
            print(f"  {relation}: {count}")
    
    print("\n=== AMIS Schema 类型分布 ===")
    amis_counter = Counter(amis_types)
    for amis_type, count in amis_counter.most_common():
        print(f"  {amis_type}: {count}")
    
    print("\n=== 图谱规模统计 ===")
    avg_nodes = sum(nodes_per_sample) / len(nodes_per_sample)
    avg_edges = sum(edges_per_sample) / len(edges_per_sample)
    min_nodes = min(nodes_per_sample)
    max_nodes = max(nodes_per_sample)
    min_edges = min(edges_per_sample)
    max_edges = max(edges_per_sample)
    
    print(f"  平均节点数: {avg_nodes:.2f}")
    print(f"  节点数范围: {min_nodes} - {max_nodes}")
    print(f"  平均边数: {avg_edges:.2f}")
    print(f"  边数范围: {min_edges} - {max_edges}")
    
    print("\n=== 混合图谱验证 ===")
    mixed_samples = 0
    for sample in samples:
        nodes = sample['graph_input']['nodes']
        node_types_in_sample = set(n['type'] for n in nodes)
        domains_in_sample = set(n.get('domain', 'unknown') for n in nodes)
        
        if len(node_types_in_sample) > 1 or len(domains_in_sample) > 1:
            mixed_samples += 1
    
    mixed_percentage = (mixed_samples / len(samples)) * 100
    print(f"  混合图谱样本: {mixed_samples}/{len(samples)} ({mixed_percentage:.1f}%)")
    
    print("\n=== 数据质量检查 ===")
    valid_samples = 0
    issues = []
    
    for i, sample in enumerate(samples):
        try:
            assert 'messages' in sample, "缺少 messages 字段"
            assert 'graph_input' in sample, "缺少 graph_input 字段"
            assert len(sample['messages']) == 3, "messages 数量不正确"
            assert 'nodes' in sample['graph_input'], "缺少 nodes 字段"
            assert 'edges' in sample['graph_input'], "缺少 edges 字段"
            assert len(sample['graph_input']['nodes']) > 0, "节点数为0"
            
            assistant_content = sample['messages'][2]['content']
            assistant_json = json.loads(assistant_content)
            assert 'type' in assistant_json, "AMIS Schema 缺少 type 字段"
            
            valid_samples += 1
        except Exception as e:
            issues.append((i, str(e)))
    
    print(f"  有效样本: {valid_samples}/{len(samples)} ({(valid_samples/len(samples)*100):.1f}%)")
    
    if issues:
        print(f"\n  发现 {len(issues)} 个问题:")
        for idx, issue in issues[:5]:
            print(f"    样本 {idx}: {issue}")
        if len(issues) > 5:
            print(f"    ... 还有 {len(issues) - 5} 个问题")
    else:
        print("\n  ✅ 所有样本都通过质量检查！")


if __name__ == "__main__":
    analyze_dataset()
