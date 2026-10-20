"""Replace stale generated QA contacts from the verified source-of-truth facts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRAINING = ROOT / 'training'
SOURCE = TRAINING / 'online-college-qa' / 'train.jsonl'
CONTACT_IDS = {
    'arts_science_admission_contact',
    'polytechnic_admission_contact',
    'pharmacy_admission_contact',
}


def main() -> None:
    facts = {
        row['fact_id']: row
        for line in SOURCE.read_text(encoding='utf-8').splitlines()
        if (row := json.loads(line))['fact_id'] in CONTACT_IDS
    }
    updated = 0
    for path in TRAINING.rglob('*.jsonl'):
        if path == SOURCE:
            continue
        lines = path.read_text(encoding='utf-8').splitlines()
        changed = False
        for index, line in enumerate(lines):
            row = json.loads(line)
            fact = facts.get(row.get('fact_id'))
            if fact is None:
                continue
            for field in ('answer', 'context', 'source_url'):
                if field in row:
                    row[field] = fact[field if field != 'context' else 'answer']
            lines[index] = json.dumps(row, ensure_ascii=False)
            changed = True
            updated += 1
        if changed:
            path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Refreshed {updated} generated contact QA rows')


if __name__ == '__main__':
    main()
