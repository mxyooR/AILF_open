"""
调试 label masking 逻辑
检查有多少 token 被 mask 掉了
"""
import json
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-4B", trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# 读取一条样本
with open('dataset_v5.jsonl', 'r', encoding='utf-8') as f:
    sample = json.loads(f.readline())

messages = sample['messages']

# 模拟 _encode_messages 逻辑
conversation = []
role_sections = []

for msg in messages:
    role = msg['role']
    content = msg['content']
    msg_text = f"<|im_start|>{role}\n{content}<|im_end|>"
    conversation.append(msg_text)
    role_sections.append((role, msg_text))

full_text = "\n".join(conversation)

# Tokenize
encoded = tokenizer(
    full_text,
    truncation=True,
    max_length=2048,
    return_tensors='pt',
    add_special_tokens=True
)

input_ids = encoded['input_ids'].squeeze(0)
labels = input_ids.clone()

print(f"Total tokens: {len(input_ids)}")

# Mask 非 assistant 部分
current_pos = 0
for role, msg_text in role_sections:
    msg_encoded = tokenizer(msg_text, add_special_tokens=False)['input_ids']
    msg_len = len(msg_encoded)
    
    print(f"\nRole: {role}, msg_len: {msg_len}, current_pos: {current_pos}")
    
    if role != 'assistant':
        end_pos = min(current_pos + msg_len, len(labels))
        labels[current_pos:end_pos] = -100
        print(f"  Masked tokens: {current_pos} to {end_pos}")
    else:
        print(f"  NOT masked (assistant): {current_pos} to {current_pos + msg_len}")
    
    current_pos += msg_len
    if current_pos < len(labels) - 1:
        current_pos += 1

# 统计
masked_count = (labels == -100).sum().item()
unmasked_count = (labels != -100).sum().item()

print(f"\n{'='*50}")
print(f"Total tokens: {len(labels)}")
print(f"Masked tokens (-100): {masked_count}")
print(f"Unmasked tokens (for loss): {unmasked_count}")
print(f"Unmasked ratio: {unmasked_count / len(labels) * 100:.1f}%")
