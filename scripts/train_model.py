"""CPU/CUDA LoRA domain adaptation; base weights are never overwritten."""
import argparse
import hashlib
import math
import json
import sys
from contextlib import nullcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import config
from scripts.training_examples import messages_for


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default=config.MODEL_PATH)
    parser.add_argument('--data', type=Path, default=ROOT / 'training')
    parser.add_argument('--output', type=Path, default=ROOT / '.venv/models/phi3-college-adapter')
    parser.add_argument('--epochs', type=int, default=1)
    parser.add_argument('--max-length', type=int, default=512)
    parser.add_argument('--device', choices=['auto', 'cpu', 'cuda'], default='auto')
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--cpu-dtype', choices=['bfloat16', 'float32'], default='bfloat16')
    parser.add_argument('--learning-rate', type=float, default=2e-5)
    parser.add_argument('--shuffle', action='store_true')
    parser.add_argument('--answer-only', action='store_true', help='Train only assistant answer tokens for Q&A rows')
    parser.add_argument('--max-steps', type=int, default=0)
    parser.add_argument('--eval-examples', type=int, default=0)
    parser.add_argument('--resume-from', type=Path)
    parser.add_argument('--skip-steps', type=int, default=0)
    args = parser.parse_args()
    import torch
    device = ('cuda' if torch.cuda.is_available() else 'cpu') if args.device == 'auto' else args.device
    if device == 'cuda' and not torch.cuda.is_available():
        parser.error('CUDA GPU unavailable; use --device cpu')
    if args.threads < 1 or args.max_steps < 0 or args.eval_examples < 0 or args.skip_steps < 0:
        parser.error('Invalid thread, step or evaluation limits')
    if args.skip_steps and not args.resume_from:
        parser.error('--skip-steps requires --resume-from')
    if args.resume_from and not args.resume_from.is_dir():
        parser.error(f'Resume checkpoint does not exist: {args.resume_from}')
    if not math.isfinite(args.learning_rate) or args.learning_rate <= 0:
        parser.error('learning-rate must be positive and finite')
    if args.shuffle and args.skip_steps:
        parser.error('Shuffled runs cannot resume using skip-steps')
    torch.set_num_threads(args.threads)
    # Keep CPU training in the base model's compact BF16 format; loading this
    # 7+ GiB checkpoint as FP32 would require more RAM than the model itself.
    dtype = getattr(torch, args.cpu_dtype) if device == 'cpu' else torch.float16
    print(f'Training on {device}; dtype={dtype}; threads={args.threads}', flush=True)
    if args.epochs < 1 or args.max_length < 2:
        parser.error('epochs must be positive and max-length must be at least 2')
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft.mapping import get_peft_model
    from peft.peft_model import PeftModel
    from peft.tuners.lora.config import LoraConfig
    from peft.utils.peft_types import TaskType
    torch.manual_seed(42)
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=dtype,
        trust_remote_code=True, low_cpu_mem_usage=True, attn_implementation='eager').to(device)
    model.config.use_cache = False
    available_modules = {name.rsplit('.', 1)[-1] for name, _ in model.named_modules()}
    target_modules = [
        name for name in ('qkv_proj', 'q_proj', 'k_proj', 'v_proj', 'o_proj')
        if name in available_modules
    ]
    if not target_modules:
        raise RuntimeError('Could not find supported attention projection modules for LoRA.')
    if args.resume_from:
        model = PeftModel.from_pretrained(model, args.resume_from, is_trainable=True)
    else:
        model = get_peft_model(model, LoraConfig(task_type=TaskType.CAUSAL_LM, r=8,
            lora_alpha=16, lora_dropout=0.05, target_modules=target_modules))
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.learning_rate)
    scaler = torch.cuda.amp.GradScaler(enabled=device == 'cuda')

    def batches(name):
        lines = (args.data / f'{name}.jsonl').read_text(encoding='utf-8').splitlines()
        if name == 'train' and args.shuffle:
            lines = [lines[index] for index in torch.randperm(len(lines)).tolist()]
        for index, line in enumerate(lines):
            if name == 'validation' and args.eval_examples and index >= args.eval_examples:
                break
            row = json.loads(line)
            if 'question' in row and 'answer' in row:
                text = tokenizer.apply_chat_template(
                    messages_for(row) + [{'role': 'assistant', 'content': row['answer']}],
                    tokenize=False,
                    add_generation_prompt=False,
                )
                if tokenizer.eos_token and not text.endswith(tokenizer.eos_token):
                    text += tokenizer.eos_token
            else:
                text = row['text'] + tokenizer.eos_token
            batch = tokenizer(text, return_tensors='pt', truncation=True, max_length=args.max_length).to(device)
            labels = batch['input_ids'].clone()
            if args.answer_only and 'question' in row:
                prompt = tokenizer.apply_chat_template(messages_for(row), tokenize=False, add_generation_prompt=True)
                if not text.startswith(prompt):
                    raise RuntimeError('Prompt/answer token boundary is incompatible with this tokenizer')
                prompt_tokens = tokenizer(prompt, return_tensors='pt')['input_ids'].shape[1]
                labels[:, :prompt_tokens] = -100
                if not (labels[:, 1:] != -100).any():
                    raise RuntimeError('Sequence truncation removed the answer; increase --max-length')
            batch['labels'] = labels
            if batch['input_ids'].shape[1] > 1:
                yield batch

    def evaluate():
        model.eval()
        total = count = 0
        with torch.no_grad(), (torch.autocast(device_type=device, dtype=dtype)
                               if device == 'cuda' else nullcontext()):
            for batch in batches('validation'):
                loss = model(**batch).loss
                tokens = (batch['labels'][:, 1:] != -100).sum().item()
                total += loss.item() * tokens
                count += tokens
        if not count:
            raise RuntimeError('Validation dataset is empty')
        return total / count

    print('Evaluating baseline...', flush=True)
    before = evaluate()
    print(f'Baseline validation loss: {before:.4f}', flush=True)
    steps = args.skip_steps
    for epoch in range(args.epochs):
        model.train()
        for batch_index, batch in enumerate(batches('train')):
            if epoch == 0 and batch_index < args.skip_steps:
                continue
            optimizer.zero_grad(set_to_none=True)
            with (torch.autocast(device_type=device, dtype=dtype)
                  if device == 'cuda' else nullcontext()):
                loss = model(**batch).loss
            if not torch.isfinite(loss):
                raise RuntimeError('Non-finite training loss')
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            steps += 1
            print(f'epoch={epoch + 1} step={steps} loss={loss.item():.4f}', flush=True)
            if steps % 10 == 0 or steps == 1:
                model.save_pretrained(args.output / f'checkpoint-{steps}')
            if args.max_steps and steps >= args.max_steps:
                break
        if args.max_steps and steps >= args.max_steps:
            break
    if steps == args.skip_steps:
        raise RuntimeError('Training dataset is empty')
    after = evaluate()
    args.output.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)
    metrics = {'steps': steps, 'device': device, 'dtype': str(dtype), 'max_length': args.max_length,
               'answer_only_loss': args.answer_only,
               'learning_rate': args.learning_rate, 'shuffle': args.shuffle, 'epochs': args.epochs,
               'starting_adapter': str(args.resume_from) if args.resume_from else None,
               'dataset_sha256': {name: hashlib.sha256((args.data / f'{name}.jsonl').read_bytes()).hexdigest()
                                  for name in ['train', 'validation']},
               'eval_examples_limit': args.eval_examples, 'validation_loss_before': before, 'validation_loss_after': after,
               'base_model': args.model, 'automatic_activation': False}
    (args.output / 'training_metrics.json').write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()
