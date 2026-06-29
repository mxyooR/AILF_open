"""
随机抽取数据集样本查看器
"""

import json
import random
import argparse
from pathlib import Path


def load_samples(file_path: str):
    """加载 JSONL 文件"""
    samples = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))
    return samples


def format_sample(sample: dict, index: int) -> str:
    """格式化单个样本为可读文本"""
    output = []
    output.append("=" * 80)
    output.append(f"样本 #{index + 1}")
    output.append(f"类型: {sample.get('metadata', {}).get('sample_type', 'unknown')}")
    output.append(f"领域: {sample.get('metadata', {}).get('domain', 'unknown')}")
    output.append("=" * 80)
    
    messages = sample.get("messages", [])
    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        
        # 角色标签
        role_label = {
            "system": "🔧 SYSTEM",
            "user": "👤 USER",
            "assistant": "🤖 ASSISTANT"
        }.get(role, role.upper())
        
        output.append(f"\n--- {role_label} [{i+1}/{len(messages)}] ---")
        
        # 尝试格式化 JSON
        if role == "assistant" and content.startswith("{"):
            try:
                parsed = json.loads(content)
                content = json.dumps(parsed, ensure_ascii=False, indent=2)
            except:
                pass
        
        output.append(content)
    
    output.append("\n")
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="随机抽取数据集样本")
    parser.add_argument("--file", type=str, default="Model/dataset_v9_test.jsonl", help="数据集文件路径")
    parser.add_argument("--count", type=int, default=5, help="抽取样本数量")
    parser.add_argument("--type", type=str, default=None, help="指定样本类型（如 api_only, workflow_step）")
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    
    args = parser.parse_args()
    
    if args.seed is not None:
        random.seed(args.seed)
    
    # 加载样本
    samples = load_samples(args.file)
    print(f"📂 加载了 {len(samples)} 条样本")
    
    # 按类型筛选
    if args.type:
        samples = [s for s in samples if s.get("metadata", {}).get("sample_type") == args.type]
        print(f"📋 筛选类型 '{args.type}': {len(samples)} 条")
    
    if not samples:
        print("❌ 没有找到符合条件的样本")
        return
    
    # 随机抽取
    count = min(args.count, len(samples))
    selected = random.sample(samples, count)
    
    print(f"\n🎲 随机抽取 {count} 条样本:\n")
    
    for i, sample in enumerate(selected):
        print(format_sample(sample, i))


if __name__ == "__main__":
    main()
