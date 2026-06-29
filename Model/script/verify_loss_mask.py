"""
验证 Loss Mask 是否正确
检查多轮对话中，只有 assistant 部分计算 loss
"""

import json
import os
from pathlib import Path
from transformers import AutoTokenizer

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'


def verify_loss_mask(data_path: str, model_name: str = "Qwen/Qwen3-4B"):
    """验证 loss mask 是否正确"""
    
    print(f"📂 加载 tokenizer: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    
    # 读取一个 5 消息样本（两轮对话）
    print(f"📂 读取数据集: {data_path}")
    
    sample = None
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                s = json.loads(line)
                if len(s.get('messages', [])) == 5:
                    sample = s
                    break
    
    if not sample:
        print("❌ 找不到 5 消息样本")
        return
    
    messages = sample['messages']
    print(f"\n📊 样本类型: {sample.get('metadata', {}).get('sample_type')}")
    print(f"📊 消息数量: {len(messages)}")
    
    # 构建完整对话
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
    encoded = tokenizer(full_text, add_special_tokens=True, return_tensors='pt')
    input_ids = encoded['input_ids'].squeeze(0)
    labels = input_ids.clone()
    
    # 应用 loss mask
    current_pos = 0
    section_info = []
    
    for role, msg_text in role_sections:
        msg_encoded = tokenizer(msg_text, add_special_tokens=False)['input_ids']
        msg_len = len(msg_encoded)
        
        end_pos = min(current_pos + msg_len, len(labels))
        
        # 记录每个 section 的信息
        section_info.append({
            'role': role,
            'start': current_pos,
            'end': end_pos,
            'len': msg_len,
            'masked': role != 'assistant'
        })
        
        if role != 'assistant':
            labels[current_pos:end_pos] = -100
        
        current_pos += msg_len
        if current_pos < len(labels) - 1:
            current_pos += 1  # \n
    
    # 输出验证结果
    print("\n" + "=" * 70)
    print("📊 Loss Mask 验证")
    print("=" * 70)
    
    print(f"\n总 token 数: {len(input_ids)}")
    print(f"被 mask 的 token 数: {(labels == -100).sum().item()}")
    print(f"计算 loss 的 token 数: {(labels != -100).sum().item()}")
    
    print("\n各 section 详情:")
    for i, info in enumerate(section_info):
        status = "❌ MASKED" if info['masked'] else "✅ COMPUTE LOSS"
        print(f"  [{i}] {info['role']:10} | pos {info['start']:4}-{info['end']:4} | {info['len']:4} tokens | {status}")
    
    # 可视化 mask
    print("\n" + "=" * 70)
    print("📊 Token 级别可视化 (前 200 tokens)")
    print("=" * 70)
    
    tokens = tokenizer.convert_ids_to_tokens(input_ids[:200])
    labels_preview = labels[:200].tolist()
    
    print("\n格式: [token] = masked(-100) 或 compute_loss")
    print("-" * 70)
    
    current_section = 0
    for i, (tok, lab) in enumerate(zip(tokens, labels_preview)):
        # 找到当前 section
        while current_section < len(section_info) - 1 and i >= section_info[current_section + 1]['start']:
            current_section += 1
        
        role = section_info[current_section]['role'] if current_section < len(section_info) else '?'
        
        if tok in ['<|im_start|>', '<|im_end|>'] or 'system' in tok or 'user' in tok or 'assistant' in tok:
            status = "MASKED" if lab == -100 else "LOSS"
            print(f"[{i:3}] {role:10} | {tok:20} | {status}")
    
    # 验证 assistant 内容
    print("\n" + "=" * 70)
    print("📊 Assistant 回复内容验证")
    print("=" * 70)
    
    for i, info in enumerate(section_info):
        if info['role'] == 'assistant':
            start, end = info['start'], min(info['end'], len(input_ids))
            assistant_tokens = tokenizer.decode(input_ids[start:end])
            loss_tokens = labels[start:end]
            computed = (loss_tokens != -100).sum().item()
            print(f"\n第 {i//2 + 1} 轮 Assistant:")
            print(f"  位置: {start}-{end}")
            print(f"  计算 loss 的 token: {computed}/{end-start}")
            print(f"  内容预览: {assistant_tokens[:100]}...")


if __name__ == "__main__":
    script_dir = Path(__file__).parent.parent
    data_path = script_dir / "dataset_v9.jsonl"
    
    if not data_path.exists():
        print(f"❌ 找不到数据集: {data_path}")
        exit(1)
    
    verify_loss_mask(str(data_path))
