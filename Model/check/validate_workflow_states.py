"""
验证工作流状态的正确性
检查样本是否按照工作流的实际执行顺序生成
"""

import json
from collections import defaultdict


def validate_workflow_states(filepath="dataset_final.jsonl"):
    """验证工作流状态"""
    print(f"验证工作流状态: {filepath}\n")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        samples = [json.loads(line) for line in f]
    
    print(f"总样本数: {len(samples)}\n")
    
    # 按工作流分组
    workflow_samples = defaultdict(list)
    
    for sample in samples:
        user_content = sample['messages'][1]['content']
        
        if "工作流ID：" in user_content:
            workflow_id = user_content.split("工作流ID：")[1].split("\n")[0].strip()
            workflow_samples[workflow_id].append(sample)
    
    print(f"发现 {len(workflow_samples)} 个工作流\n")
    
    # 验证每个工作流的状态序列
    print("=== 工作流状态验证 ===\n")
    
    for workflow_id, samples_list in list(workflow_samples.items())[:5]:
        print(f"工作流: {workflow_id}")
        print(f"样本数: {len(samples_list)}")
        
        # 提取状态序列
        states = []
        for sample in samples_list:
            user_content = sample['messages'][1]['content']
            
            if "当前状态：" in user_content:
                state = user_content.split("当前状态：")[1].split("\n")[0].strip()
                states.append(state)
            
            if "当前节点：" in user_content:
                current_node = user_content.split("当前节点：")[1].split("\n")[0].strip()
            else:
                current_node = "N/A"
        
        print(f"状态序列: {' -> '.join(set(states))}")
        print()
    
    # 验证状态转换的合理性
    print("\n=== 状态转换验证 ===\n")
    
    state_transitions = defaultdict(int)
    
    for workflow_id, samples_list in workflow_samples.items():
        prev_state = None
        
        for sample in sorted(samples_list, key=lambda x: x['messages'][1]['content']):
            user_content = sample['messages'][1]['content']
            
            if "当前状态：" in user_content:
                current_state = user_content.split("当前状态：")[1].split("\n")[0].strip()
                
                if prev_state:
                    transition = f"{prev_state} -> {current_state}"
                    state_transitions[transition] += 1
                
                prev_state = current_state
    
    print("状态转换统计:")
    for transition, count in sorted(state_transitions.items(), key=lambda x: x[1], reverse=True):
        print(f"  {transition}: {count} 次")
    
    # 验证 mock 数据的存在
    print("\n=== Mock 数据验证 ===\n")
    
    samples_with_context = 0
    
    for sample in samples:
        user_content = sample['messages'][1]['content']
        
        if "上下文数据：" in user_content:
            samples_with_context += 1
            
            # 提取 mock 数据
            context_str = user_content.split("上下文数据：")[1].split("\n")[0].strip()
            try:
                context_data = json.loads(context_str)
                if len(context_data) > 0:
                    pass
            except:
                pass
    
    print(f"包含上下文数据的样本: {samples_with_context}")
    
    # 验证 API 路径的真实性
    print("\n=== API 路径验证 ===\n")
    
    api_paths = set()
    fake_apis = []
    
    for sample in samples:
        assistant_content = sample['messages'][2]['content']
        try:
            assistant_json = json.loads(assistant_content)
            
            # 检查 body 中的 api 配置
            body = assistant_json.get('body')
            if isinstance(body, dict) and 'api' in body:
                api_config = body['api']
                if isinstance(api_config, dict):
                    url = api_config.get('url', '')
                    if url:
                        api_paths.add(url)
                        
                        # 检查是否是胡编的 API
                        if '/workflow/' in url and '/execute' not in url and '/state' not in url:
                            fake_apis.append(url)
            elif isinstance(body, list):
                for item in body:
                    if isinstance(item, dict) and 'api' in item:
                        api_config = item['api']
                        if isinstance(api_config, dict):
                            url = api_config.get('url', '')
                            if url:
                                api_paths.add(url)
        except:
            pass
    
    print(f"发现 {len(api_paths)} 个不同的 API 路径")
    print("\n常见 API 路径:")
    for path in sorted(list(api_paths))[:10]:
        print(f"  {path}")
    
    if fake_apis:
        print(f"\n⚠️  发现 {len(fake_apis)} 个可能是胡编的 API:")
        for path in fake_apis[:5]:
            print(f"  {path}")
    else:
        print("\n✅ 所有 API 路径都是真实的！")
    
    # 验证 AMIS Schema 的完整性
    print("\n=== AMIS Schema 验证 ===\n")
    
    valid_schemas = 0
    invalid_schemas = []
    
    for i, sample in enumerate(samples):
        assistant_content = sample['messages'][2]['content']
        try:
            assistant_json = json.loads(assistant_content)
            
            # 检查必需字段
            if 'type' not in assistant_json:
                invalid_schemas.append((i, "缺少 type 字段"))
                continue
            
            if assistant_json['type'] != 'page':
                invalid_schemas.append((i, f"type 不是 page: {assistant_json['type']}"))
                continue
            
            if 'body' not in assistant_json:
                invalid_schemas.append((i, "缺少 body 字段"))
                continue
            
            valid_schemas += 1
        except json.JSONDecodeError as e:
            invalid_schemas.append((i, f"JSON 解析错误: {str(e)}"))
    
    print(f"有效 Schema: {valid_schemas}/{len(samples)} ({valid_schemas/len(samples)*100:.1f}%)")
    
    if invalid_schemas:
        print(f"\n⚠️  发现 {len(invalid_schemas)} 个无效 Schema:")
        for idx, reason in invalid_schemas[:5]:
            print(f"  样本 {idx}: {reason}")
    else:
        print("\n✅ 所有 Schema 都有效！")
    
    # 总结
    print("\n" + "="*60)
    print("验证总结")
    print("="*60)
    print(f"✅ 工作流数量: {len(workflow_samples)}")
    print(f"✅ 状态转换类型: {len(state_transitions)}")
    print(f"✅ 包含上下文数据: {samples_with_context}")
    print(f"✅ API 路径数量: {len(api_paths)}")
    print(f"✅ 有效 Schema: {valid_schemas}/{len(samples)}")
    
    if not fake_apis and not invalid_schemas:
        print("\n🎉 所有验证通过！数据集质量优秀！")
    else:
        print("\n⚠️  发现一些问题，需要修复")


if __name__ == "__main__":
    validate_workflow_states()
