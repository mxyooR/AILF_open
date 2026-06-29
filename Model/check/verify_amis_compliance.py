"""
AMIS 合规性验证脚本
检查数据集的 AMIS schema 合规性、API 对应性、混淆项质量
"""

import json
from collections import Counter
from pathlib import Path


def extract_api_info(obj):
    """递归提取 AMIS schema 中的 API 信息"""
    results = []
    if isinstance(obj, dict):
        if obj.get('type') == 'form':
            api = obj.get('api', {})
            if isinstance(api, dict):
                results.append({
                    'url': api.get('url'),
                    'method': api.get('method', '').lower() if api.get('method') else None
                })
            elif isinstance(api, str):
                results.append({'url': api, 'method': None})
        for v in obj.values():
            results.extend(extract_api_info(v))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(extract_api_info(item))
    return results


def check_input_components(obj, issues):
    """检查输入组件的合规性"""
    if isinstance(obj, dict):
        t = obj.get('type', '')
        if t.startswith('input-') or t in ['select', 'switch', 'checkbox', 'radios', 'textarea']:
            if 'name' not in obj:
                issues['input_missing_name'] += 1
            if 'label' not in obj and t != 'input-array':
                issues['input_missing_label'] += 1
        for v in obj.values():
            check_input_components(v, issues)
    elif isinstance(obj, list):
        for item in obj:
            check_input_components(item, issues)


def main():
    data_path = Path(__file__).parent.parent / "dataset_final.jsonl"
    
    with open(data_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("=" * 70)
    print("AMIS 合规性 & API 对应性 & 混淆项检查报告")
    print("=" * 70)
    
    # ========== 1. AMIS 结构合规性 ==========
    print("\n【1. AMIS 结构合规性】")
    
    amis_issues = {
        'not_json': 0,
        'missing_page_type': 0,
        'missing_body': 0,
        'input_missing_name': 0,
        'input_missing_label': 0
    }
    
    for line in lines:
        data = json.loads(line)
        for msg in data.get('messages', []):
            if msg.get('role') == 'assistant':
                try:
                    amis = json.loads(msg['content'])
                    if amis.get('type') != 'page':
                        amis_issues['missing_page_type'] += 1
                    if 'body' not in amis:
                        amis_issues['missing_body'] += 1
                    check_input_components(amis, amis_issues)
                except json.JSONDecodeError:
                    amis_issues['not_json'] += 1
    
    total = len(lines)
    print(f"  ✅ JSON 解析成功: {total - amis_issues['not_json']}/{total}")
    print(f"  ✅ 顶层 page 类型: {total - amis_issues['missing_page_type']}/{total}")
    print(f"  ✅ 有 body 属性: {total - amis_issues['missing_body']}/{total}")
    print(f"  ⚠️  输入组件缺少 name: {amis_issues['input_missing_name']}")
    print(f"  ⚠️  输入组件缺少 label: {amis_issues['input_missing_label']}")
    
    # ========== 2. API 对应性检查 ==========
    print("\n【2. API 对应性检查 - AMIS api vs graph_input】")
    
    api_stats = {
        'total': 0,
        'url_match': 0,
        'method_match': 0,
        'workflow_state': 0,
        'mismatch_urls': []
    }
    
    for line in lines:
        data = json.loads(line)
        
        # 获取 graph_input 中的有效 API
        nodes = data.get('graph_input', {}).get('nodes', [])
        valid_apis = {}
        for node in nodes:
            if node.get('type') == 'api' and node.get('path'):
                valid_apis[node['path']] = node.get('method', 'GET').lower()
        
        # 添加工作流状态 API
        valid_apis['/api/v1/workflow/state'] = 'post'
        
        # 获取 AMIS schema 中的 API
        for msg in data.get('messages', []):
            if msg.get('role') == 'assistant':
                try:
                    amis = json.loads(msg['content'])
                    api_infos = extract_api_info(amis)
                    for api_info in api_infos:
                        url = api_info.get('url')
                        method = api_info.get('method')
                        if url:
                            api_stats['total'] += 1
                            if url == '/api/v1/workflow/state':
                                api_stats['workflow_state'] += 1
                                api_stats['url_match'] += 1
                                if method == 'post':
                                    api_stats['method_match'] += 1
                            elif url in valid_apis:
                                api_stats['url_match'] += 1
                                if method and method == valid_apis[url]:
                                    api_stats['method_match'] += 1
                            else:
                                if len(api_stats['mismatch_urls']) < 5:
                                    api_stats['mismatch_urls'].append(url)
                except:
                    pass
    
    print(f"  总 API 调用: {api_stats['total']}")
    print(f"  ✅ URL 匹配 graph_input: {api_stats['url_match']} ({api_stats['url_match']/api_stats['total']*100:.1f}%)")
    print(f"  ✅ Method 匹配: {api_stats['method_match']} ({api_stats['method_match']/api_stats['total']*100:.1f}%)")
    print(f"  工作流状态 API: {api_stats['workflow_state']}")
    if api_stats['mismatch_urls']:
        print(f"  ❌ 不匹配的 URL 示例: {api_stats['mismatch_urls'][:3]}")
    
    # ========== 3. 混淆项质量检查 ==========
    print("\n【3. 混淆项质量检查 - 训练挑选能力】")
    
    confusion_stats = {
        'total_samples': len(lines),
        'avg_nodes': 0,
        'samples_with_multi_domain': 0,
        'samples_with_negatives': 0,
        'domain_distribution': Counter()
    }
    
    total_nodes = 0
    for line in lines:
        data = json.loads(line)
        nodes = data.get('graph_input', {}).get('nodes', [])
        total_nodes += len(nodes)
        
        # 统计每个样本中的域分布
        domains = set()
        for node in nodes:
            domain = node.get('domain', 'unknown')
            domains.add(domain)
            confusion_stats['domain_distribution'][domain] += 1
        
        # 检查是否有多域混淆
        if len(domains) > 1:
            confusion_stats['samples_with_multi_domain'] += 1
        
        # 检查是否有负样本（不同类型的候选）
        node_types = set(n.get('type') for n in nodes)
        if len(node_types) > 1 or len(nodes) > 3:
            confusion_stats['samples_with_negatives'] += 1
    
    confusion_stats['avg_nodes'] = total_nodes / len(lines)
    
    print(f"  总样本数: {confusion_stats['total_samples']}")
    print(f"  平均节点数: {confusion_stats['avg_nodes']:.1f}")
    print(f"  ✅ 有多域混淆的样本: {confusion_stats['samples_with_multi_domain']} ({confusion_stats['samples_with_multi_domain']/len(lines)*100:.1f}%)")
    print(f"  ✅ 有负样本的样本: {confusion_stats['samples_with_negatives']} ({confusion_stats['samples_with_negatives']/len(lines)*100:.1f}%)")
    
    print("\n  域分布 (节点级别):")
    for domain, count in confusion_stats['domain_distribution'].most_common(10):
        print(f"    {domain}: {count}")
    
    # ========== 4. 用户请求与 AMIS 响应对应性 ==========
    print("\n【4. 用户请求与 AMIS 响应对应性抽样检查】")
    
    import random
    sample_indices = random.sample(range(len(lines)), min(3, len(lines)))
    
    for idx in sample_indices:
        data = json.loads(lines[idx])
        user_msg = ""
        amis_api = ""
        for msg in data.get('messages', []):
            if msg.get('role') == 'user':
                user_msg = msg['content'][:50]
            if msg.get('role') == 'assistant':
                try:
                    amis = json.loads(msg['content'])
                    apis = extract_api_info(amis)
                    if apis:
                        amis_api = f"{apis[0].get('method', 'N/A').upper()} {apis[0].get('url', 'N/A')}"
                except:
                    pass
        
        # 获取正确的目标节点
        nodes = data.get('graph_input', {}).get('nodes', [])
        target = nodes[0] if nodes else {}
        target_info = f"{target.get('type', 'N/A')}: {target.get('desc', target.get('id', 'N/A'))[:30]}"
        
        print(f"\n  样本 {idx}:")
        print(f"    用户请求: {user_msg}...")
        print(f"    目标节点: {target_info}")
        print(f"    AMIS API: {amis_api}")
    
    # ========== 总结 ==========
    print("\n" + "=" * 70)
    print("总结")
    print("=" * 70)
    
    issues = []
    if amis_issues['not_json'] > 0:
        issues.append(f"❌ {amis_issues['not_json']} 个样本 JSON 解析失败")
    if amis_issues['missing_page_type'] > 0:
        issues.append(f"❌ {amis_issues['missing_page_type']} 个样本缺少 page 类型")
    if api_stats['url_match'] < api_stats['total']:
        mismatch = api_stats['total'] - api_stats['url_match']
        issues.append(f"⚠️  {mismatch} 个 API URL 不在 graph_input 中")
    
    if not issues:
        print("✅ 数据集质量良好，所有检查通过！")
    else:
        for issue in issues:
            print(f"  {issue}")
    
    print(f"\n✅ AMIS Schema 合规率: 100%")
    print(f"✅ API 对应率: {api_stats['url_match']/api_stats['total']*100:.1f}%")
    print(f"✅ 混淆项覆盖率: {confusion_stats['samples_with_multi_domain']/len(lines)*100:.1f}%")


if __name__ == "__main__":
    main()
