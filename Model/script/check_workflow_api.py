"""检查 workflow_step 和 workflow entry 的 API 提交地址"""
import json
import re

# 统计
workflow_step_urls = {}
workflow_entry_urls = {}
api_only_urls = {}

with open('Model/dataset_v9_train.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        sample_type = data.get('metadata', {}).get('sample_type', '')
        
        # 获取最后一个 assistant 消息（AMIS Schema）
        messages = data.get('messages', [])
        last_assistant = None
        for msg in reversed(messages):
            if msg['role'] == 'assistant':
                last_assistant = msg['content']
                break
        
        if not last_assistant:
            continue
        
        # 提取所有 URL
        urls = re.findall(r'"url":\s*"([^"]+)"', last_assistant)
        
        if sample_type == 'workflow_step':
            for url in urls:
                workflow_step_urls[url] = workflow_step_urls.get(url, 0) + 1
        elif sample_type in ['contrastive_workflow', 'contrastive_workflow_only']:
            for url in urls:
                workflow_entry_urls[url] = workflow_entry_urls.get(url, 0) + 1
        elif sample_type in ['api_only', 'contrastive_api']:
            for url in urls:
                api_only_urls[url] = api_only_urls.get(url, 0) + 1

print("=== Workflow Step 样本的 URL ===")
for url, count in sorted(workflow_step_urls.items(), key=lambda x: -x[1]):
    print(f"  {url}: {count}")

print("\n=== Workflow Entry 样本的 URL ===")
for url, count in sorted(workflow_entry_urls.items(), key=lambda x: -x[1]):
    print(f"  {url}: {count}")

print("\n=== API Only 样本的 URL (前10) ===")
for url, count in sorted(api_only_urls.items(), key=lambda x: -x[1])[:10]:
    print(f"  {url}: {count}")

# 检查是否有非 /api/v1/workflow/state 的 workflow URL
print("\n=== 检查 ===")
non_state_workflow_step = [url for url in workflow_step_urls if '/api/v1/workflow/state' not in url]
non_state_workflow_entry = [url for url in workflow_entry_urls if '/api/v1/workflow/state' not in url]

if non_state_workflow_step:
    print(f"⚠️ Workflow Step 中有非 /api/v1/workflow/state 的 URL:")
    for url in non_state_workflow_step:
        print(f"  - {url}")
else:
    print("✅ Workflow Step 全部使用 /api/v1/workflow/state")

if non_state_workflow_entry:
    print(f"⚠️ Workflow Entry 中有非 /api/v1/workflow/state 的 URL:")
    for url in non_state_workflow_entry:
        print(f"  - {url}")
else:
    print("✅ Workflow Entry 全部使用 /api/v1/workflow/state")
