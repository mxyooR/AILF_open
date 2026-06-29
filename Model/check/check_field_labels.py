"""
检查数据集中的字段标签是否全部为中文
"""
import json
import re
from collections import Counter, defaultdict

def is_chinese(text):
    """检查文本是否包含中文"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def is_pure_english(text):
    """检查文本是否为纯英文（包括下划线）"""
    return bool(re.match(r'^[a-zA-Z_]+$', text))

def check_field_labels(dataset_path):
    """检查数据集中的字段标签"""
    print(f"📊 检查数据集: {dataset_path}\n")
    
    all_labels = []
    chinese_labels = []
    english_labels = []
    mixed_labels = []
    
    label_examples = defaultdict(list)
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            sample = json.loads(line)
            
            # 检查所有消息中的字段标签
            for msg in sample.get('messages', []):
                content = msg.get('content', '')
                
                # 提取所有 field_label_xxx 的值
                matches = re.findall(r'"field_label_(\w+)":\s*"([^"]+)"', content)
                
                for field_name, label_value in matches:
                    all_labels.append(label_value)
                    
                    if is_pure_english(label_value):
                        english_labels.append(label_value)
                        label_examples[label_value].append({
                            'line': line_num,
                            'field': field_name,
                            'domain': sample.get('metadata', {}).get('domain', 'unknown')
                        })
                    elif is_chinese(label_value):
                        chinese_labels.append(label_value)
                    else:
                        mixed_labels.append(label_value)
    
    # 统计结果
    total = len(all_labels)
    chinese_count = len(chinese_labels)
    english_count = len(english_labels)
    mixed_count = len(mixed_labels)
    
    print(f"总字段标签数: {total}")
    print(f"  ✅ 中文标签: {chinese_count} ({chinese_count/total*100:.1f}%)")
    print(f"  ❌ 英文标签: {english_count} ({english_count/total*100:.1f}%)")
    print(f"  ⚠️  混合标签: {mixed_count} ({mixed_count/total*100:.1f}%)")
    print()
    
    if english_labels:
        print("=" * 60)
        print("❌ 发现英文标签！")
        print("=" * 60)
        
        # 统计最常见的英文标签
        english_counter = Counter(english_labels)
        print(f"\n最常见的英文标签 (Top 20):")
        for label, count in english_counter.most_common(20):
            print(f"  {label}: {count} 次")
        
        # 显示示例位置
        print(f"\n英文标签示例位置:")
        for label in list(english_counter.keys())[:5]:
            examples = label_examples[label][:3]
            print(f"\n  标签: '{label}' (共 {english_counter[label]} 次)")
            for ex in examples:
                print(f"    - 行 {ex['line']}, 字段: {ex['field']}, 领域: {ex['domain']}")
    else:
        print("✅ 所有字段标签都是中文！")
    
    if mixed_labels:
        print(f"\n⚠️  混合标签示例:")
        for label in list(set(mixed_labels))[:10]:
            print(f"  - {label}")
    
    return {
        'total': total,
        'chinese': chinese_count,
        'english': english_count,
        'mixed': mixed_count,
        'english_labels': list(set(english_labels))
    }

if __name__ == "__main__":
    # 检查训练集
    print("=" * 60)
    print("检查训练集")
    print("=" * 60)
    train_result = check_field_labels('dataset_v10_train.jsonl')
    
    print("\n" + "=" * 60)
    print("检查验证集")
    print("=" * 60)
    val_result = check_field_labels('dataset_v10_val.jsonl')
    
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    total_english = train_result['english'] + val_result['english']
    total_all = train_result['total'] + val_result['total']
    
    if total_english > 0:
        print(f"❌ 发现 {total_english} 个英文标签 (占比 {total_english/total_all*100:.2f}%)")
        print(f"\n需要修复的英文标签:")
        all_english = set(train_result['english_labels'] + val_result['english_labels'])
        for label in sorted(all_english):
            print(f"  - {label}")
    else:
        print("✅ 所有字段标签都是中文！数据集质量良好！")
