"""Inspect saved training artifacts and capture held-out model answers."""
import argparse
import json
import math
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.training_examples import messages_for


def accuracy_score(outcomes):
    """Fraction of correct answers; no score can be inferred for an empty set."""
    if not outcomes:
        raise ValueError('At least one answer is required for accuracy')
    if any(type(outcome) is not bool for outcome in outcomes):
        raise ValueError('Accuracy requires explicit correct/incorrect judgments')
    return sum(outcomes) / len(outcomes)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adapter', type=Path)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--data', type=Path, default=Path('training/online-college-qa'))
    parser.add_argument('--output', type=Path, default=Path('training/verification-20261013.json'))
    parser.add_argument('--split', choices=['validation', 'test'], default='validation')
    parser.add_argument('--limit', type=int, default=0,
                        help='Evaluate at most this many held-out rows (0 evaluates all)')
    parser.add_argument('--one-per-college', action='store_true',
                        help='Select one held-out row for each institution')
    parser.add_argument('--max-new-tokens', type=int, default=256,
                        help='Generation cap; keep long point-wise answers from being cut off')
    args = parser.parse_args()
    if args.max_new_tokens < 1:
        parser.error('--max-new-tokens must be positive')
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    from safetensors import safe_open
    metrics = None
    keys = []
    if args.adapter:
        metrics = json.loads((args.adapter / 'training_metrics.json').read_text())
        if metrics['steps'] < 1 or not all(math.isfinite(metrics[key]) for key in
            ['validation_loss_before', 'validation_loss_after']):
            raise RuntimeError('Invalid training metrics')
        with safe_open(str(args.adapter / 'adapter_model.safetensors'), framework='pt') as weights:
            keys = list(weights.keys())
            if not keys or not all(torch.isfinite(weights.get_tensor(key)).all().item() for key in keys):
                raise RuntimeError('Invalid adapter weights')
    train = [json.loads(line) for line in (args.data / 'train.jsonl').read_text(encoding='utf-8').splitlines()]
    validation = [json.loads(line) for line in (args.data / f'{args.split}.jsonl').read_text(encoding='utf-8').splitlines()]
    if args.one_per_college:
        selected = {}
        for row in validation:
            selected.setdefault(row.get('college', 'engineering'), row)
        validation = list(selected.values())
    if args.limit:
        if args.limit < 1:
            parser.error('--limit must be positive')
        validation = validation[:args.limit]
    overlap = {row['fact_id'] for row in train} & {row['fact_id'] for row in validation}
    grounded = all('context' in row for row in train + validation)
    if overlap and not grounded:
        raise RuntimeError(f'Validation fact leakage: {overlap}')
    if {row['question'].casefold() for row in train} & {row['question'].casefold() for row in validation}:
        raise RuntimeError('Evaluation question phrasing leaked into training')
    torch.set_num_threads(4)
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.float32,
        low_cpu_mem_usage=True, local_files_only=True, attn_implementation='eager')
    if args.adapter:
        model = PeftModel.from_pretrained(model, args.adapter)
    model.eval()
    answers = []
    for row in validation:
        prompt = tokenizer.apply_chat_template(messages_for(row),
            tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors='pt')
        with torch.inference_mode():
            result = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False,
                pad_token_id=tokenizer.eos_token_id)
        answer = tokenizer.decode(result[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        record = {'question': row['question'], 'expected': row['answer'], 'generated': answer,
                  'source_url': row['source_url'], 'exact_match': answer.strip() == row['answer'].strip()}
        answers.append(record)
        print(json.dumps(record, ensure_ascii=False), flush=True)
    report = {'metrics': metrics, 'adapter_tensor_count': len(keys), 'weights_finite': True,
        'evaluation_split': args.split, 'evidence_grounded_task': grounded,
        'validation_fact_overlap': sorted(overlap), 'answers': answers,
        'exact_match_accuracy': accuracy_score([row['exact_match'] for row in answers]),
        'answer_accuracy': None,
        'accuracy_definition': 'correct answers divided by evaluated answers, from 0 to 1; factual review required',
        'manual_factual_review_required': True, 'automatic_activation': False}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
