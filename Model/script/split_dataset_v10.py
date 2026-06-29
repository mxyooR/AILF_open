"""
数据集划分脚本 V10 - No Leak 版本
将 dataset_v10.jsonl 划分为训练集和验证集，避免数据泄漏

划分策略：
- 按 target_api_id / target_workflow_id 分组，确保同一个 API/Workflow 的所有样本
  要么全在训练集，要么全在验证集（防止数据泄漏）
- 跨 sample_type 统一分组：同一个 API 在 api_only 和 contrastive_api 中都算同一组
- 验证集比例: 10%
"""

import json
import random
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Set


def get_group_key(sample: Dict) -> str:
    """
    获取样本的分组 key，用于 no-leak 划分
    
    分组逻辑：
    - api_only, contrastive_api: 按 target_api_id 分组
    - workflow_step: 按 workflow_id 分组（注意不是 target_workflow_id）
    - contrastive_workflow, contrastive_workflow_only: 按 target_workflow_id 分组
    - rejection, mismatch_rejection: 按 domain 分组
    """
    metadata = sample.get('metadata', {})
    sample_type = metadata.get('sample_type', 'unknown')
    
    if sample_type in ('api_only', 'contrastive_api'):
        return f"api_{metadata.get('target_api_id', 'unknown')}"
    
    elif sample_type == 'workflow_step':
        # workflow_step 用的是 workflow_id，不是 target_workflow_id
        return f"wf_{metadata.get('workflow_id', 'unknown')}"
    
    elif sample_type in ('contrastive_workflow', 'contrastive_workflow_only'):
        return f"wf_{metadata.get('target_workflow_id', 'unknown')}"
    
    elif sample_type in ('rejection', 'mismatch_rejection'):
        return f"reject_{metadata.get('domain', 'unknown')}"

    elif sample_type in ('help_intent', 'help_intent_variant'):
        return f"help_{metadata.get('domain', 'unknown')}"
    
    else:
        return f"other_{sample_type}"


def split_dataset_no_leak(
    input_path: str,
    train_output_path: str,
    val_output_path: str,
    val_ratio: float = 0.1,
    seed: int = 42
):
    """
    No-Leak 数据集划分
    
    确保同一个 API/Workflow 的所有样本不会同时出现在训练集和验证集中
    """
    random.seed(seed)
    
    # 读取所有样本
    all_samples = []
    print(f"📂 读取数据集: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                sample = json.loads(line)
                all_samples.append(sample)
    
    total_samples = len(all_samples)
    print(f"📊 总样本数: {total_samples}")
    
    # 统计样本类型分布
    type_counts = defaultdict(int)
    for sample in all_samples:
        sample_type = sample.get('metadata', {}).get('sample_type', 'unknown')
        type_counts[sample_type] += 1
    
    print(f"📊 样本类型分布:")
    for st, count in sorted(type_counts.items()):
        print(f"   - {st}: {count} ({count/total_samples*100:.1f}%)")
    
    # 🔥 关键：跨类型统一按 group_key 分组
    groups: Dict[str, List[Dict]] = defaultdict(list)
    for sample in all_samples:
        key = get_group_key(sample)
        groups[key].append(sample)
    
    print(f"\n📊 分组统计:")
    api_groups = [k for k in groups.keys() if k.startswith('api_')]
    wf_groups = [k for k in groups.keys() if k.startswith('wf_')]
    reject_groups = [k for k in groups.keys() if k.startswith('reject_')]
    help_groups = [k for k in groups.keys() if k.startswith('help_')]
    print(f"   - API groups: {len(api_groups)}")
    print(f"   - Workflow groups: {len(wf_groups)}")
    print(f"   - Rejection groups: {len(reject_groups)}")
    print(f"   - Help groups: {len(help_groups)}")
    
    # 分别对 API、Workflow、Rejection 进行划分
    def split_groups(group_keys: List[str], target_val_ratio: float) -> Set[str]:
        """选择哪些 group 放入验证集"""
        if not group_keys:
            return set()
        
        random.shuffle(group_keys)
        
        # 计算总样本数和目标验证集样本数
        total = sum(len(groups[k]) for k in group_keys)
        target_val = int(total * target_val_ratio)
        
        # 贪心选择
        val_keys = []
        val_count = 0
        for key in group_keys:
            if val_count >= target_val:
                break
            val_keys.append(key)
            val_count += len(groups[key])
        
        # 确保至少有一个 group 在验证集（如果有多个 group）
        if len(val_keys) == 0 and len(group_keys) > 1:
            val_keys = [group_keys[0]]
        
        return set(val_keys)
    
    # 分别划分
    val_api_keys = split_groups(api_groups, val_ratio)
    val_wf_keys = split_groups(wf_groups, val_ratio)
    val_reject_keys = split_groups(reject_groups, val_ratio)
    val_help_keys = split_groups(help_groups, val_ratio)
    
    val_keys = val_api_keys | val_wf_keys | val_reject_keys | val_help_keys
    
    print(f"\n📊 验证集 groups:")
    print(f"   - API: {len(val_api_keys)} / {len(api_groups)}")
    print(f"   - Workflow: {len(val_wf_keys)} / {len(wf_groups)}")
    print(f"   - Rejection: {len(val_reject_keys)} / {len(reject_groups)}")
    print(f"   - Help: {len(val_help_keys)} / {len(help_groups)}")
    
    # 分配样本
    train_samples = []
    val_samples = []
    
    for key, samples in groups.items():
        if key in val_keys:
            val_samples.extend(samples)
        else:
            train_samples.extend(samples)
    
    # 打乱顺序
    random.shuffle(train_samples)
    random.shuffle(val_samples)
    
    print(f"\n📊 最终划分结果:")
    print(f"   训练集: {len(train_samples)} ({len(train_samples)/total_samples*100:.1f}%)")
    print(f"   验证集: {len(val_samples)} ({len(val_samples)/total_samples*100:.1f}%)")
    
    # 验证 no-leak
    train_keys = set(get_group_key(s) for s in train_samples)
    val_keys_check = set(get_group_key(s) for s in val_samples)
    
    leaked_keys = train_keys & val_keys_check
    if leaked_keys:
        print(f"\n❌ 错误: 发现 {len(leaked_keys)} 个泄漏的 group keys!")
        for key in list(leaked_keys)[:5]:
            print(f"   - {key}")
    else:
        print(f"\n✅ No-Leak 验证通过: 训练集和验证集没有重叠的 API/Workflow")
    
    # 验证集样本类型分布
    print(f"\n📊 训练集样本类型分布:")
    train_type_counts = defaultdict(int)
    for sample in train_samples:
        st = sample.get('metadata', {}).get('sample_type', 'unknown')
        train_type_counts[st] += 1
    for st, count in sorted(train_type_counts.items()):
        print(f"   - {st}: {count}")
    
    print(f"\n📊 验证集样本类型分布:")
    val_type_counts = defaultdict(int)
    for sample in val_samples:
        st = sample.get('metadata', {}).get('sample_type', 'unknown')
        val_type_counts[st] += 1
    for st, count in sorted(val_type_counts.items()):
        print(f"   - {st}: {count}")
    
    # 保存
    with open(train_output_path, 'w', encoding='utf-8') as f:
        for sample in train_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    print(f"\n✅ 训练集已保存: {train_output_path}")
    
    with open(val_output_path, 'w', encoding='utf-8') as f:
        for sample in val_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    print(f"✅ 验证集已保存: {val_output_path}")


if __name__ == "__main__":
    script_dir = Path(__file__).parent.parent
    
    # 自动检测最新版本数据集
    v11_path = script_dir / "dataset_v11.jsonl"
    v10_path = script_dir / "dataset_v10.jsonl"
    
    if v11_path.exists():
        input_path = v11_path
        train_output_path = script_dir / "dataset_v11_train.jsonl"
        val_output_path = script_dir / "dataset_v11_val.jsonl"
        print("📂 检测到 v11 数据集，使用 v11 版本")
    elif v10_path.exists():
        input_path = v10_path
        train_output_path = script_dir / "dataset_v10_train.jsonl"
        val_output_path = script_dir / "dataset_v10_val.jsonl"
        print("📂 检测到 v10 数据集，使用 v10 版本")
    else:
        print(f"❌ 找不到数据集文件: dataset_v11.jsonl 或 dataset_v10.jsonl")
        exit(1)
    
    split_dataset_no_leak(
        input_path=str(input_path),
        train_output_path=str(train_output_path),
        val_output_path=str(val_output_path),
        val_ratio=0.1,
        seed=42
    )
