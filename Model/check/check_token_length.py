"""检查数据集 token 长度分布"""
import json
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3-4B', trust_remote_code=True)

with open('Model/dataset_v8.jsonl', 'r', encoding='utf-8') as f:
    samples = [json.loads(line) for line in f if line.strip()]

lengths = []
for sample in samples:
    text = ''
    for msg in sample['messages']:
        text += f"<|im_start|>{msg['role']}\n{msg['content']}<|im_end|>\n"
    tokens = tokenizer.encode(text, add_special_tokens=False)
    lengths.append(len(tokens))

lengths.sort()
print(f'样本数: {len(lengths)}')
print(f'最小长度: {min(lengths)}')
print(f'最大长度: {max(lengths)}')
print(f'平均长度: {sum(lengths)/len(lengths):.0f}')
print(f'中位数: {lengths[len(lengths)//2]}')
print(f'90%分位: {lengths[int(len(lengths)*0.9)]}')
print(f'95%分位: {lengths[int(len(lengths)*0.95)]}')
print(f'99%分位: {lengths[int(len(lengths)*0.99)]}')
print(f'\nMAX_LENGTH=1024 时:')
print(f'  超过1024的样本: {sum(1 for l in lengths if l > 1024)} ({sum(1 for l in lengths if l > 1024)/len(lengths)*100:.1f}%)')
print(f'  平均padding比例: {(1024 - sum(lengths)/len(lengths))/1024*100:.1f}%')
