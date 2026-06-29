"""
纯 LLM 训练脚本 V11
基于 dataset_v11.jsonl 的两轮对话架构训练

核心特点：
1. 移除 GNN/图谱相关代码，纯 LLM 微调
2. 支持 3 消息（单轮）和 5 消息（两轮）样本
3. Loss Masking：只计算 assistant 回复部分的 loss
4. 使用 LoRA + 4-bit 量化高效微调

数据格式：
- 两轮样本 (5 messages): system→user→assistant(选择)→system(详情)→assistant(AMIS)
- 单轮样本 (3 messages): system→user→assistant(AMIS)
"""

import os
import json
import random
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split, Subset
from torch.optim import AdamW
from torch.amp import autocast, GradScaler

# 设置 HuggingFace 国内镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    get_cosine_schedule_with_warmup,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from typing import List, Dict, Optional, Any, Tuple
from tqdm import tqdm
import logging
from torch.utils.tensorboard import SummaryWriter

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if logger.hasHandlers():
    logger.handlers.clear()

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.propagate = False


# ============================================================================
# 1. Dataset & Collator
# ============================================================================

class PureLLMDataset(Dataset):
    """
    纯 LLM 数据集
    
    支持两种样本格式：
    - 5 messages (两轮对话): system→user→assistant→system→assistant
    - 3 messages (单轮对话): system→user→assistant
    
    Loss Masking: 只计算 assistant 部分的 loss
    """
    def __init__(
        self, 
        data_path: str, 
        tokenizer, 
        max_length: int = 2048,
        filter_domain: Optional[str] = None,
        filter_sample_type: Optional[str] = None
    ):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []
        
        # 统计信息
        domain_stats = {}
        sample_type_stats = {}
        message_count_stats = {}
        
        logger.info(f"正在加载数据集: {data_path}")
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    
                    # 提取 metadata
                    metadata = item.get('metadata', {})
                    domain = metadata.get('domain', 'unknown')
                    sample_type = metadata.get('sample_type', 'unknown')
                    
                    # 统计消息数量
                    messages = item.get('messages', [])
                    msg_count = len(messages)
                    message_count_stats[msg_count] = message_count_stats.get(msg_count, 0) + 1
                    
                    # 统计
                    domain_stats[domain] = domain_stats.get(domain, 0) + 1
                    sample_type_stats[sample_type] = sample_type_stats.get(sample_type, 0) + 1
                    
                    # 按条件过滤
                    if filter_domain and domain != filter_domain:
                        continue
                    if filter_sample_type and sample_type != filter_sample_type:
                        continue
                    
                    self.data.append(item)
        
        logger.info(f"数据集加载完成，共 {len(self.data)} 条样本")
        logger.info(f"📊 领域分布: {domain_stats}")
        logger.info(f"📊 样本类型分布: {sample_type_stats}")
        logger.info(f"📊 消息数量分布: {message_count_stats}")

        # 保留原始样本，便于评估第一轮选择准确率
        self.raw_items = self.data
    
    def __len__(self):
        return len(self.data)
    
    def _encode_messages(self, messages: List[Dict]) -> Dict:
        """
        将对话编码为 Causal LM 格式，并实现 Loss Masking
        
        格式: <|im_start|>role\ncontent<|im_end|>\n...
        
        关键: 只计算 assistant 回复部分的 loss，system 和 user 部分 mask 为 -100
        """
        # 构建完整对话文本 (Qwen Chat Template)
        conversation = []
        role_sections = []  # 记录每个角色的文本段
        
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            msg_text = f"<|im_start|>{role}\n{content}<|im_end|>"
            conversation.append(msg_text)
            role_sections.append((role, msg_text))
        
        # 拼接所有消息
        full_text = "\n".join(conversation)
        
        # Tokenize 完整文本
        encoded = self.tokenizer(
            full_text,
            truncation=True,
            max_length=self.max_length,
            return_tensors='pt',
            add_special_tokens=True
        )
        
        input_ids = encoded['input_ids'].squeeze(0)
        attention_mask = encoded['attention_mask'].squeeze(0)
        
        # 创建 labels，初始为 input_ids
        labels = input_ids.clone()
        
        # 🔥 关键: Mask 掉 system 和 user 部分，只保留 assistant 的 loss
        current_pos = 0
        for role, msg_text in role_sections:
            # Tokenize 当前段落
            msg_encoded = self.tokenizer(
                msg_text,
                add_special_tokens=False
            )['input_ids']
            msg_len = len(msg_encoded)
            
            # 如果不是 assistant，mask 掉这部分的 loss
            if role != 'assistant':
                end_pos = min(current_pos + msg_len, len(labels))
                labels[current_pos:end_pos] = -100
            
            current_pos += msg_len
            # 加上换行符的 token
            if current_pos < len(labels) - 1:
                current_pos += 1  # \n 的 token
        
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'labels': labels
        }
    
    def __getitem__(self, idx: int) -> Dict:
        """返回一个样本"""
        item = self.data[idx]
        
        # 处理对话数据
        messages = item.get('messages', [])
        text_data = self._encode_messages(messages)
        
        # 提取 metadata
        metadata = item.get('metadata', {})
        
        return {
            'text': text_data,
            'idx': idx,
            'metadata': metadata
        }

    def get_raw(self, idx: int) -> Dict:
        """获取原始样本（包含 messages）"""
        return self.data[idx]


class PureLLMCollator:
    """自定义 Collator，用于批处理文本数据"""
    
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.pad_token_id = tokenizer.pad_token_id
    
    def __call__(self, batch: List[Dict]) -> Dict:
        """批处理数据"""
        text_input_ids = [item['text']['input_ids'] for item in batch]
        text_attention_mask = [item['text']['attention_mask'] for item in batch]
        text_labels = [item['text']['labels'] for item in batch]
        
        # Padding
        max_len = max(len(ids) for ids in text_input_ids)
        
        padded_input_ids = []
        padded_attention_mask = []
        padded_labels = []
        
        for ids, mask, labels in zip(text_input_ids, text_attention_mask, text_labels):
            padding_len = max_len - len(ids)
            
            # Pad input_ids
            padded_ids = torch.cat([
                ids,
                torch.full((padding_len,), self.pad_token_id, dtype=torch.long)
            ])
            padded_input_ids.append(padded_ids)
            
            # Pad attention_mask
            padded_mask = torch.cat([
                mask,
                torch.zeros(padding_len, dtype=torch.long)
            ])
            padded_attention_mask.append(padded_mask)
            
            # Pad labels (用 -100 mask 掉 padding 部分)
            padded_label = torch.cat([
                labels,
                torch.full((padding_len,), -100, dtype=torch.long)
            ])
            padded_labels.append(padded_label)
        
        # Stack
        return {
            'input_ids': torch.stack(padded_input_ids),
            'attention_mask': torch.stack(padded_attention_mask),
            'labels': torch.stack(padded_labels)
        }


# ============================================================================
# 2. Model Wrapper
# ============================================================================

class PureLLMModel(nn.Module):
    """
    纯 LLM 模型包装器
    使用 LoRA + 4-bit 量化进行高效微调
    """
    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-4B",
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        use_4bit: bool = True
    ):
        super().__init__()
        
        logger.info(f"正在加载模型: {model_name}")
        
        # 1. 加载 Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        # 设置 padding token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 2. 配置量化 (4-bit)
        if use_4bit:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
            )
        else:
            bnb_config = None
        
        # 3. 加载 LLM
        self.llm = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16 if use_4bit else torch.float16
        )
        
        # 4. 准备 LoRA 训练
        if use_4bit:
            self.llm = prepare_model_for_kbit_training(self.llm)
        
        # 5. 配置 LoRA
        lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=[
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ],
            lora_dropout=lora_dropout,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        self.llm = get_peft_model(self.llm, lora_config)
        self.llm.print_trainable_parameters()
        
        logger.info("模型初始化完成")
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: Optional[torch.Tensor] = None
    ) -> Dict:
        """前向传播"""
        outputs = self.llm(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
            return_dict=True
        )
        
        return {
            'loss': outputs.loss,
            'logits': outputs.logits
        }


# ============================================================================
# 3. Training Loop
# ============================================================================

def train_epoch(
    model: PureLLMModel,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler,
    scaler: GradScaler,
    device: torch.device,
    epoch: int,
    gradient_accumulation_steps: int = 4,
    max_grad_norm: float = 1.0
) -> float:
    """训练一个 epoch"""
    model.train()
    total_loss = 0
    step = 0
    
    progress_bar = tqdm(dataloader, desc=f"Epoch {epoch}")
    
    for batch_idx, batch in enumerate(progress_bar):
        # 获取数据
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)
        
        # 混合精度训练
        with autocast('cuda', dtype=torch.bfloat16):
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            loss = outputs['loss']
            
            # 梯度累积
            loss = loss / gradient_accumulation_steps
        
        # 反向传播
        scaler.scale(loss).backward()
        
        # 更新参数
        if (batch_idx + 1) % gradient_accumulation_steps == 0:
            # 梯度裁剪
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
            
            # 优化器步进
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            optimizer.zero_grad()
            
            step += 1
        
        # 记录 loss
        total_loss += loss.item() * gradient_accumulation_steps
        
        # 更新进度条
        progress_bar.set_postfix({
            'loss': f"{loss.item() * gradient_accumulation_steps:.4f}",
            'lr': f"{scheduler.get_last_lr()[0]:.2e}"
        })
    
    avg_loss = total_loss / len(dataloader)
    return avg_loss


@torch.no_grad()
def evaluate(
    model: PureLLMModel,
    dataloader: DataLoader,
    device: torch.device,
    desc: str = "Validation"
) -> float:
    """在验证集上评估模型"""
    model.eval()
    total_loss = 0
    num_batches = 0
    
    progress_bar = tqdm(dataloader, desc=desc)
    
    for batch in progress_bar:
        # 获取数据
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)
        
        # 前向传播（无梯度）
        with autocast('cuda', dtype=torch.bfloat16):
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            loss = outputs['loss']
        
        total_loss += loss.item()
        num_batches += 1
        
        progress_bar.set_postfix({'loss': f"{loss.item():.4f}"})
    
    avg_loss = total_loss / num_batches if num_batches > 0 else 0
    return avg_loss


def _get_raw_item(dataset, idx: int) -> Optional[Dict]:
    if isinstance(dataset, Subset):
        base = dataset.dataset
        real_idx = dataset.indices[idx]
        return _get_raw_item(base, real_idx)
    if hasattr(dataset, "get_raw"):
        return dataset.get_raw(idx)
    if hasattr(dataset, "data"):
        return dataset.data[idx]
    return None


def _parse_selection(text: str) -> Tuple[Optional[str], Optional[str]]:
    if not text:
        return None, None
    line = text.strip().splitlines()[0]
    if line.upper().startswith("HELP") or line.startswith("帮助"):
        return "HELP", None
    if line.startswith("REJECT"):
        return "REJECT", None
    if line.startswith("API:") or line.startswith("API："):
        name = line.split(":", 1)[1].strip() if ":" in line else line.split("：", 1)[1].strip()
        return "API", name
    if line.startswith("WORKFLOW:") or line.startswith("WORKFLOW："):
        name = line.split(":", 1)[1].strip() if ":" in line else line.split("：", 1)[1].strip()
        return "WORKFLOW", name
    return None, None


@torch.no_grad()
def evaluate_selection_accuracy(
    model: PureLLMModel,
    dataset,
    device: torch.device,
    sample_limit: int = 200,
    seed: int = 42
) -> Dict[str, Any]:
    """
    评估第一轮选择准确率（API/WORKFLOW/REJECT）
    只评估 5-message 样本的第 1 轮选择
    """
    model.eval()
    indices = list(range(len(dataset)))
    random.Random(seed).shuffle(indices)
    if sample_limit and sample_limit > 0:
        indices = indices[:sample_limit * 3]

    total = 0
    type_match = 0
    exact_match = 0
    unknown = 0

    for idx in indices:
        item = _get_raw_item(dataset, idx)
        if not item:
            continue
        messages = item.get("messages", [])
        if len(messages) != 5:
            continue
        system_prompt = messages[0].get("content", "")
        user_prompt = messages[1].get("content", "")
        target = messages[2].get("content", "").strip()

        prompt = (
            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        inputs = model.tokenizer(
            prompt,
            return_tensors='pt',
            add_special_tokens=False
        )
        input_ids = inputs['input_ids'].to(device)
        attention_mask = inputs['attention_mask'].to(device)

        generated = model.llm.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=50,
            do_sample=False,
            pad_token_id=model.tokenizer.pad_token_id,
            eos_token_id=model.tokenizer.eos_token_id
        )
        output = model.tokenizer.decode(
            generated[0][input_ids.shape[1]:],
            skip_special_tokens=True
        ).strip()

        pred_type, _ = _parse_selection(output)
        tgt_type, _ = _parse_selection(target)

        if pred_type is None or tgt_type is None:
            unknown += 1
        else:
            if pred_type == tgt_type:
                type_match += 1
            if output.splitlines()[0].strip() == target.splitlines()[0].strip():
                exact_match += 1

        total += 1
        if sample_limit and total >= sample_limit:
            break

    if total == 0:
        return {"type_acc": 0.0, "exact_acc": 0.0, "total": 0, "unknown": unknown}

    return {
        "type_acc": type_match / total,
        "exact_acc": exact_match / total,
        "total": total,
        "unknown": unknown
    }


def save_checkpoint(
    model: PureLLMModel,
    optimizer: torch.optim.Optimizer,
    scheduler,
    epoch: int,
    train_loss: float,
    val_loss: float,
    save_dir: str,
    is_best: bool = False
):
    """保存检查点"""
    os.makedirs(save_dir, exist_ok=True)
    
    checkpoint_path = os.path.join(save_dir, f"checkpoint_epoch_{epoch}")
    
    # 保存 LoRA 权重
    model.llm.save_pretrained(checkpoint_path)
    
    # 保存训练状态
    torch.save({
        'epoch': epoch,
        'optimizer_state_dict': optimizer.state_dict(),
        'scheduler_state_dict': scheduler.state_dict(),
        'train_loss': train_loss,
        'val_loss': val_loss
    }, os.path.join(checkpoint_path, "training_state.pt"))
    
    logger.info(f"检查点已保存: {checkpoint_path}")
    
    # 如果是最佳模型，额外保存一份
    if is_best:
        best_path = os.path.join(save_dir, "best_model")
        model.llm.save_pretrained(best_path)
        logger.info(f"🏆 最佳模型已保存: {best_path}")


def main():
    """
    主训练函数
    """
    print("\n" + "=" * 60)
    print("🚀 纯 LLM 训练启动 (V11 两轮对话架构)")
    print("=" * 60 + "\n")
    
    # 检测 GPU 数量
    gpu_count = torch.cuda.device_count()
    print(f"检测到 {gpu_count} 个 GPU")
    
    # 检测环境
    is_kaggle = os.path.exists("/kaggle")
    
    # ========== 路径配置 ==========
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if is_kaggle:
        # Kaggle 路径
        train_data_path = "/kaggle/input/ailf-pure-llm-dataset/dataset_v11_train.jsonl"
        val_data_path = "/kaggle/input/ailf-pure-llm-dataset/dataset_v11_val.jsonl"
        # 兼容单文件
        if not os.path.exists(train_data_path):
            train_data_path = "/kaggle/input/ailf-pure-llm-dataset/dataset_v11.jsonl"
            val_data_path = None
        save_dir = "/kaggle/working/checkpoints_v11"
    else:
        # 云服务器或本地路径
        local_train_path = os.path.join(script_dir, "dataset_v11_train.jsonl")
        local_val_path = os.path.join(script_dir, "dataset_v11_val.jsonl")
        local_single_path = os.path.join(script_dir, "dataset_v11.jsonl")
        cloud_train_path = "/root/ailf/dataset_v11_train.jsonl"
        cloud_val_path = "/root/ailf/dataset_v11_val.jsonl"
        cloud_single_path = "/root/ailf/dataset_v11.jsonl"
        
        # 自动检测数据集位置
        if os.path.exists(local_train_path) and os.path.exists(local_val_path):
            train_data_path = local_train_path
            val_data_path = local_val_path
        elif os.path.exists(cloud_train_path) and os.path.exists(cloud_val_path):
            train_data_path = cloud_train_path
            val_data_path = cloud_val_path
        elif os.path.exists(local_single_path):
            train_data_path = local_single_path
            val_data_path = None
        elif os.path.exists(cloud_single_path):
            train_data_path = cloud_single_path
            val_data_path = None
        else:
            raise FileNotFoundError("找不到数据集文件！请确保 dataset_v11.jsonl 存在")
        
        save_dir = os.path.join(script_dir, "checkpoints_v11") if os.path.exists(script_dir) else "/root/ailf/checkpoints_v11"
    
    model_name = "Qwen/Qwen3-4B"
    
    # 模型配置
    use_4bit = True
    
    # LoRA 配置
    lora_r = 16
    lora_alpha = 32
    lora_dropout = 0.05
    
    # 训练配置 (根据 GPU 自动调整)
    if is_kaggle:
        batch_size = 1
        gradient_accumulation_steps = 8
        max_length = 1536
        num_workers = 2
    else:
        # 3090 24GB 优化配置
        batch_size = 2
        gradient_accumulation_steps = 4
        max_length = 2048
        num_workers = 4
    
    num_epochs = 3
    learning_rate = 1e-4
    warmup_ratio = 0.1
    max_grad_norm = 1.0
    selection_eval_samples = 200
    
    # ========== 设备 ==========
    print("\n诊断 CUDA 环境:")
    print(f"PyTorch 版本: {torch.__version__}")
    print(f"CUDA 可用: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA 版本: {torch.version.cuda}")
        print(f"cuDNN 版本: {torch.backends.cudnn.version()}")
    
    if not torch.cuda.is_available():
        print("\n❌ CUDA 不可用！请检查 GPU 环境")
        raise RuntimeError("❌ 未检测到 GPU！")
    
    device = torch.device("cuda:0")
    
    logger.info("=" * 60)
    logger.info(f"训练环境: {'Kaggle' if is_kaggle else '云服务器/本地'}")
    logger.info("=" * 60)
    for i in range(gpu_count):
        logger.info(f"GPU {i}: {torch.cuda.get_device_name(i)}")
    logger.info(f"主设备: {device}")
    logger.info(f"模型: {model_name}")
    logger.info(f"Batch Size: {batch_size}")
    logger.info(f"Max Length: {max_length}")
    logger.info(f"有效 Batch: {batch_size * gradient_accumulation_steps}")
    logger.info("=" * 60)
    
    # ========== 加载模型 ==========
    model = PureLLMModel(
        model_name=model_name,
        lora_r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        use_4bit=use_4bit
    )
    
    # ========== 加载数据 ==========
    if val_data_path is not None:
        # 使用预划分的文件
        logger.info(f"📂 使用预划分数据集:")
        logger.info(f"   训练集: {train_data_path}")
        logger.info(f"   验证集: {val_data_path}")
        
        train_dataset = PureLLMDataset(
            data_path=train_data_path,
            tokenizer=model.tokenizer,
            max_length=max_length
        )
        
        val_dataset = PureLLMDataset(
            data_path=val_data_path,
            tokenizer=model.tokenizer,
            max_length=max_length
        )
    else:
        # 使用 random_split
        logger.warning("⚠️ 使用单文件 random_split 划分")
        
        full_dataset = PureLLMDataset(
            data_path=train_data_path,
            tokenizer=model.tokenizer,
            max_length=max_length
        )
        
        train_size = int(0.9 * len(full_dataset))
        val_size = len(full_dataset) - train_size
        train_dataset, val_dataset = random_split(
            full_dataset, 
            [train_size, val_size],
            generator=torch.Generator().manual_seed(42)
        )
    
    logger.info(f"数据集划分: 训练集 {len(train_dataset)} 条, 验证集 {len(val_dataset)} 条")
    
    collator = PureLLMCollator(tokenizer=model.tokenizer)
    
    # DataLoader
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collator,
        num_workers=num_workers,
        pin_memory=True
    )
    
    val_dataloader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collator,
        num_workers=num_workers,
        pin_memory=True
    )
    
    # ========== 优化器和调度器 ==========
    trainable_params = list(filter(lambda p: p.requires_grad, model.parameters()))
    total_trainable = sum(p.numel() for p in trainable_params)
    logger.info(f"📊 可训练参数: {total_trainable:,}")
    
    optimizer = AdamW(
        trainable_params,
        lr=learning_rate,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.01
    )
    
    # 计算总步数
    total_steps = len(train_dataloader) * num_epochs // gradient_accumulation_steps
    warmup_steps = int(total_steps * warmup_ratio)
    
    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps
    )
    
    # ========== 混合精度训练 ==========
    scaler = GradScaler('cuda')
    
    # ========== TensorBoard 日志 ==========
    log_dir = os.path.join(save_dir, "runs")
    writer = SummaryWriter(log_dir)
    logger.info(f"TensorBoard 日志目录: {log_dir}")
    
    # ========== 训练循环 ==========
    logger.info("开始训练...")
    logger.info(f"训练集: {len(train_dataset)} 条, 验证集: {len(val_dataset)} 条")
    logger.info(f"Batch Size: {batch_size}")
    logger.info(f"梯度累积: {gradient_accumulation_steps}")
    logger.info(f"有效 Batch: {batch_size * gradient_accumulation_steps}")
    logger.info(f"总步数: {total_steps}, 预热: {warmup_steps}")
    
    best_val_loss = float('inf')
    
    for epoch in range(1, num_epochs + 1):
        logger.info(f"\n{'='*50}")
        logger.info(f"Epoch {epoch}/{num_epochs}")
        logger.info(f"{'='*50}")
        
        # 训练一个 epoch
        train_loss = train_epoch(
            model=model,
            dataloader=train_dataloader,
            optimizer=optimizer,
            scheduler=scheduler,
            scaler=scaler,
            device=device,
            epoch=epoch,
            gradient_accumulation_steps=gradient_accumulation_steps,
            max_grad_norm=max_grad_norm
        )
        
        logger.info(f"Epoch {epoch} 训练完成，平均 Loss: {train_loss:.4f}")
        
        # 验证
        logger.info("正在验证...")
        val_loss = evaluate(
            model=model,
            dataloader=val_dataloader,
            device=device,
            desc=f"Validation Epoch {epoch}"
        )
        
        logger.info(f"Epoch {epoch} 验证完成，验证 Loss: {val_loss:.4f}")

        # 评估第一轮选择准确率（抽样）
        sel_metrics = evaluate_selection_accuracy(
            model=model,
            dataset=val_dataset,
            device=device,
            sample_limit=selection_eval_samples,
            seed=42
        )
        logger.info(
            f"选择准确率(样本{sel_metrics['total']}): "
            f"type_acc={sel_metrics['type_acc']:.4f}, "
            f"exact_acc={sel_metrics['exact_acc']:.4f}, "
            f"unknown={sel_metrics['unknown']}"
        )
        
        # 记录到 TensorBoard
        writer.add_scalar('Loss/train', train_loss, epoch)
        writer.add_scalar('Loss/val', val_loss, epoch)
        writer.add_scalar('Learning_Rate', scheduler.get_last_lr()[0], epoch)
        writer.add_scalar('Selection/type_acc', sel_metrics['type_acc'], epoch)
        writer.add_scalar('Selection/exact_acc', sel_metrics['exact_acc'], epoch)
        
        # 判断是否是最佳模型
        is_best = val_loss < best_val_loss
        if is_best:
            best_val_loss = val_loss
            logger.info(f"🎉 新的最佳验证 Loss: {val_loss:.4f}")
        
        # 保存检查点
        save_checkpoint(
            model=model,
            optimizer=optimizer,
            scheduler=scheduler,
            epoch=epoch,
            train_loss=train_loss,
            val_loss=val_loss,
            save_dir=save_dir,
            is_best=is_best
        )
    
    writer.close()
    logger.info("\n训练完成!")
    logger.info(f"最佳验证 Loss: {best_val_loss:.4f}")
    logger.info(f"最佳模型保存在: {os.path.join(save_dir, 'best_model')}")
    logger.info("\n" + "=" * 60)
    logger.info("🎉 纯 LLM V11 训练完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
