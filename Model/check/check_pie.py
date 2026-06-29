import json

with open('Model/dataset_v8.jsonl', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'pie' in line:
            sample = json.loads(line)
            amis = json.loads(sample['messages'][2]['content'])
            print(f"样本 {i+1}:")
            print(json.dumps(amis, ensure_ascii=False, indent=2))
            print()
            break
