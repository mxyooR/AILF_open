"""生成验证集"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from script.dataset_generator_v5 import DatasetGeneratorV5

def main():
    generator = DatasetGeneratorV5()
    
    # 生成 750 条验证集
    output_path = Path(__file__).parent.parent / "dataset_v5_val.jsonl"
    samples = generator.generate_dataset(
        total_samples=750,
        output_path=str(output_path)
    )
    
    # 验证
    stats = generator.validate_dataset(samples)
    print(f"\n验证集统计:")
    print(f"总样本数: {stats['total']}")
    print(f"按类型分布:")
    for t, c in sorted(stats['by_type'].items()):
        print(f"  - {t}: {c} ({c/stats['total']*100:.1f}%)")
    
    print(f"\n按域分布:")
    for d, c in sorted(stats['by_domain'].items()):
        print(f"  - {d}: {c}")

if __name__ == "__main__":
    main()
