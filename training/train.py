"""Reproducible small LoRA run; logs real before/after held-out loss."""
import argparse
import json
import os
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('HF_HOME', str(ROOT / '.cache' / 'huggingface'))
from core import BASE_MODEL, SYSTEM
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
from peft import LoraConfig, get_peft_model

def encode(tokenizer, row):
    messages = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': row['prompt']}]
    prefix = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
    ids = tokenizer.apply_chat_template(messages + [{'role': 'assistant', 'content': row['response']}], tokenize=True)
    if len(ids) > 512:
        raise ValueError('Example exceeds 512 tokens. Shorten it or explicitly change the sequence limit.')
    labels = [-100] * len(prefix) + ids[len(prefix):]
    if len(prefix) >= len(ids):
        raise ValueError('Example has no assistant tokens.')
    return {'input_ids': torch.tensor([ids]), 'labels': torch.tensor([labels])}

def evaluate(model, rows, device):
    model.eval()
    total, tokens = 0.0, 0
    with torch.no_grad():
        for row in rows:
            batch = {k: v.to(device) for k, v in row.items()}
            n = (batch['labels'][:, 1:] != -100).sum().item()
            total += model(**batch).loss.item() * n
            tokens += n
    return total / tokens

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--steps', type=int, default=120)
    args = parser.parse_args()
    if args.steps < 1:
        parser.error('--steps must be positive')
    set_seed(42)
    torch.set_num_threads(4)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    dtype = torch.bfloat16 if device == 'cuda' else torch.float32
    print('Device:', device, flush=True)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    base = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=dtype, attn_implementation='sdpa').to(device)
    base.config.use_cache = False
    revision = base.config._commit_hash
    model = get_peft_model(base, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05, target_modules=['q_proj', 'v_proj'], task_type='CAUSAL_LM'))
    model.print_trainable_parameters()
    data = {}
    for split in ['train', 'validation']:
        rows = [json.loads(line) for line in (ROOT / 'training' / (split + '.jsonl')).read_text(encoding='utf-8').splitlines() if line.strip()]
        data[split] = [encode(tokenizer, row) for row in rows]
    before = evaluate(model, data['validation'], device)
    print('Validation before:', before, flush=True)
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)
    history = []
    started = time.time()
    order = list(range(len(data['train'])))
    random.shuffle(order)
    model.train()
    for step in range(args.steps):
        optimizer.zero_grad(set_to_none=True)
        loss_sum = 0.0
        for micro in range(2):
            index = (step * 2 + micro) % len(order)
            if index == 0:
                random.shuffle(order)
            batch = {k: v.to(device) for k, v in data['train'][order[index]].items()}
            loss = model(**batch).loss
            (loss / 2).backward()
            loss_sum += loss.item() / 2
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        history.append({'step': step + 1, 'loss': loss_sum})
        if (step + 1) % 5 == 0:
            print(f'Step {step + 1}/{args.steps}: loss={loss_sum:.4f}', flush=True)
    after = evaluate(model, data['validation'], device)
    output = ROOT / 'adapter'
    model.save_pretrained(output, safe_serialization=True)
    # Pin the base checkpoint used by this adapter.
    config_path = output / 'adapter_config.json'
    config = json.loads(config_path.read_text())
    config['revision'] = revision
    config_path.write_text(json.dumps(config, indent=2) + '\n')
    report = {
        'base_model': BASE_MODEL, 'base_revision': revision, 'method': 'LoRA', 'rank': 8,
        'steps': args.steps, 'seed': 42, 'learning_rate': 0.0001, 'effective_batch_size': 2,
        'train_examples': len(data['train']), 'validation_examples': len(data['validation']),
        'train_tasks': 20, 'validation_tasks': 4,
        'trainable_parameters': sum(p.numel() for p in model.parameters() if p.requires_grad),
        'device': torch.cuda.get_device_name(0) if device == 'cuda' else 'CPU',
        'validation_loss_before': before, 'validation_loss_after': after,
        'training_seconds': round(time.time() - started, 2), 'history': history,
        'limitations': 'Small synthetic dataset: 20 training tasks, 4 held-out tasks, each with 3 prompt variants. Loss is not a code-correctness benchmark. General coding improvement is not established.',
    }
    (ROOT / 'docs' / 'training-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'history'}, indent=2), flush=True)

if __name__ == '__main__':
    main()
