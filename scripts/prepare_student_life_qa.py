"""Prepare source-grounded student-life QA for continued local adapter training."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'training' / 'student-life-20261019' / 'train.jsonl'
OUTPUT = ROOT / 'training' / 'student-life-grounded-20261019'


def main():
    rows = [json.loads(line) for line in SOURCE.read_text(encoding='utf-8').splitlines() if line.strip()]
    train, validation = [], []
    for row in rows:
        fields = {
            'answer': row['answer'], 'context': row['answer'],
            'source_url': row['source_url'], 'fact_id': row['fact_id'],
            'college': row['college'], 'evidence_college': row['college'],
        }
        train.append({**fields, 'question': row['question']})
        validation.append({**fields, 'question': f"EGSPEC pathi {row['fact_id'].replace('_', ' ')} details point wise ah sollu"})
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, records in (('train', train), ('validation', validation)):
        (OUTPUT / f'{name}.jsonl').write_text(
            ''.join(json.dumps(record, ensure_ascii=False) + '\n' for record in records),
            encoding='utf-8',
        )
    print(f'Prepared {len(train)} training and {len(validation)} validation rows')


if __name__ == '__main__':
    main()
