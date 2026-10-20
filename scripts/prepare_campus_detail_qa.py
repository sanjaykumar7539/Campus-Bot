"""Combine new official campus details with previous institution guides for LoRA."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'training' / 'campus-detail-grounded-20261019'
SOURCE_FILES = (
    ROOT / 'training' / 'campus-details-20261019' / 'train.jsonl',
    ROOT / 'training' / 'institution-guides-20261019' / 'train.jsonl',
    ROOT / 'training' / 'campus-details-20261019' / 'goal.jsonl',
)


def main():
    rows = []
    for path in SOURCE_FILES:
        rows.extend(json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip())
    training = []
    validation = []
    for row in rows:
        college = row['college']
        common = {
            'college': college,
            'evidence_college': college,
            'context': row['answer'],
            'answer': row['answer'],
            'fact_id': row['fact_id'],
            'source_url': row['source_url'],
        }
        training.append({**common, 'question': row['question']})
        validation.append({**common, 'question': f"{college} pathi {row['fact_id'].replace('_', ' ')} details points la sollu"})
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for split, records in (('train', training), ('validation', validation)):
        (OUTPUT / f'{split}.jsonl').write_text(
            ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in records),
            encoding='utf-8',
        )
    print(f'Prepared {len(training)} training and {len(validation)} validation rows')


if __name__ == '__main__':
    main()
