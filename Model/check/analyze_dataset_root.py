"""
分析训练数据集的多样性和潜在问题
"""
import json
from collections import Counter, defaultdict

# 读取数据集
data = []
import sys
dataset_file = sys.argv[1] if len(sys.argv) > 1 else "dataset_v5.jsonl"
with open(dataset_file, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            data.append(json.loads(line))

print(f"总样本数: {len(data)}")
print("=" * 60)

# 1. 分析样本类型分布
sample_types = Counter()
domains = Counter()
for item in data:
    meta = item.get("metadata", {})
    sample_types[meta.get("sample_type", "unknown")] += 1
    domains[meta.get("domain", "unknown")] += 1

print("\n1. 样本类型分布:")
for st, count in sample_types.most_common():
    print(f"   {st}: {count} ({count/len(data)*100:.1f}%)")

print("\n2. 领域分布:")
for domain, count in domains.most_common():
    print(f"   {domain}: {count} ({count/len(data)*100:.1f}%)")

# 2. 分析输出 JSON 的结构多样性
output_structures = Counter()
output_types = Counter()
api_urls = Counter()

for item in data:
    messages = item.get("messages", [])
    for msg in messages:
        if msg["role"] == "assistant":
            content = msg["content"]
            try:
                parsed = json.loads(content)
                # 顶层 type
                output_types[parsed.get("type", "unknown")] += 1
                
                # body 结构
                body = parsed.get("body", {})
                if isinstance(body, dict):
                    body_type = body.get("type", "unknown")
                    output_structures[f"body.type={body_type}"] += 1
                    
                    # API URL
                    api = body.get("api", {})
                    if isinstance(api, dict):
                        url = api.get("url", "")
                        if url:
                            api_urls[url] += 1
                elif isinstance(body, list):
                    output_structures["body=list"] += 1
            except:
                output_structures["parse_error"] += 1

print("\n3. 输出顶层 type 分布:")
for t, count in output_types.most_common():
    print(f"   {t}: {count}")

print("\n4. 输出 body.type 分布:")
for s, count in output_structures.most_common(10):
    print(f"   {s}: {count}")

print("\n5. API URL 分布 (Top 20):")
for url, count in api_urls.most_common(20):
    print(f"   {url}: {count}")

# 3. 分析输入指令的多样性
instructions = []
for item in data:
    messages = item.get("messages", [])
    for msg in messages:
        if msg["role"] == "user":
            content = msg["content"]
            # 提取指令部分
            if "指令：" in content:
                instr = content.split("指令：")[1].split("\n")[0]
                instructions.append(instr)

instruction_counter = Counter(instructions)
print(f"\n6. 唯一指令数: {len(instruction_counter)} / {len(instructions)}")
print("   重复最多的指令 (Top 10):")
for instr, count in instruction_counter.most_common(10):
    print(f"   '{instr}': {count}")

# 4. 分析输出 JSON 的长度分布
output_lengths = []
for item in data:
    messages = item.get("messages", [])
    for msg in messages:
        if msg["role"] == "assistant":
            output_lengths.append(len(msg["content"]))

print(f"\n7. 输出长度统计:")
print(f"   最短: {min(output_lengths)}")
print(f"   最长: {max(output_lengths)}")
print(f"   平均: {sum(output_lengths)/len(output_lengths):.0f}")

# 5. 检查是否有完全相同的样本
seen = set()
duplicates = 0
for item in data:
    key = json.dumps(item["messages"], ensure_ascii=False)
    if key in seen:
        duplicates += 1
    seen.add(key)

print(f"\n8. 完全重复的样本数: {duplicates}")

# 6. 分析 system prompt 的多样性
system_prompts = set()
for item in data:
    messages = item.get("messages", [])
    for msg in messages:
        if msg["role"] == "system":
            # 只取前 100 字符作为特征
            system_prompts.add(msg["content"][:100])

print(f"\n9. 唯一 system prompt 前缀数: {len(system_prompts)}")

print("\n" + "=" * 60)
print("分析完成！")
