"""随机抽取数据集样本并格式化显示"""
import json
import random
import sys

def show_raw_samples(dataset_path, count=3):
    """显示原始 JSON 格式样本"""
    with open(dataset_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    samples = random.sample(lines, min(count, len(lines)))
    
    for i, line in enumerate(samples, 1):
        sample = json.loads(line)
        print("=" * 100)
        print(f"样本 {i} - 类型: {sample['metadata']['sample_type']} | 域: {sample['metadata']['domain']}")
        print("=" * 100)
        print(json.dumps(sample, ensure_ascii=False, indent=2))
        print("\n")

def show_samples(dataset_path, count=10):
    with open(dataset_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 随机抽取
    samples = random.sample(lines, min(count, len(lines)))
    
    for i, line in enumerate(samples, 1):
        sample = json.loads(line)
        sample_type = sample["metadata"]["sample_type"]
        domain = sample["metadata"]["domain"]
        
        print("=" * 80)
        print(f"样本 {i} - 类型: {sample_type} | 域: {domain}")
        print("=" * 80)
        
        # System prompt
        print("\n【System】")
        sys_content = sample['messages'][0]['content']
        print(sys_content[:300] + "..." if len(sys_content) > 300 else sys_content)
        
        # User input
        print("\n【User】")
        print(sample['messages'][1]['content'])
        
        # Assistant output (AMIS Schema)
        print("\n【Assistant (AMIS Schema)】")
        amis = json.loads(sample['messages'][2]['content'])
        amis_str = json.dumps(amis, ensure_ascii=False, indent=2)
        print(amis_str[:1500])
        if len(amis_str) > 1500:
            print("... (truncated)")
        
        # Graph input
        print("\n【Graph Input】")
        graph = sample['graph_input']
        nodes = graph.get("nodes", [])
        print(f"  节点数: {len(nodes)}")
        for node in nodes[:3]:
            node_type = node.get("type", "unknown")
            node_name = node.get("name", node.get("id", "unknown"))
            print(f"    - {node_type}: {node_name}")
        if len(nodes) > 3:
            print(f"    ... 还有 {len(nodes) - 3} 个节点")
        
        print("\n")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "Model/dataset_v8.jsonl"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    mode = sys.argv[3] if len(sys.argv) > 3 else "raw"
    
    if mode == "raw":
        show_raw_samples(path, count)
    else:
        show_samples(path, count)
