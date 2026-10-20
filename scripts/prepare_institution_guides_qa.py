"""Build source-labelled overview/scope examples for bounded local LoRA training."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.core.institution_guides import GUIDES

DEST = ROOT / 'training' / 'institution-guides-20261019'
NAMES = {
    'engineering_overview': 'EGS Pillay Engineering College',
    'arts_science_overview': 'EGS Pillay Arts and Science College',
    'pharmacy_overview': 'EGS Pillay College of Pharmacy',
    'nursing_overview': 'EGS Pillay College of Nursing',
    'polytechnic_overview': 'EGS Pillay Polytechnic College',
    'education_overview': 'EGS Pillay College of Education',
    'naturopathy_overview': 'EGS Pillay Naturopathy and Yoga Medical College',
    'school_overview': 'EGS Pillay International School',
}


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for split, template in (
        ('train', 'Tell me what {name} studies, its verified history and leadership, and career scope.'),
        ('validation', '{name} pathi, history, courses and future scope point wise sollu.'),
    ):
        rows = []
        for fact_id, name in NAMES.items():
            rows.append({
                'question': template.format(name=name),
                'answer': GUIDES[fact_id],
                'fact_id': fact_id,
                'college': name,
                'source_url': 'https://' + GUIDES[fact_id].split('https://', 1)[1].split(' ', 1)[0],
            })
        (DEST / f'{split}.jsonl').write_text(
            ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows),
            encoding='utf-8',
        )
    print(f'Prepared {len(NAMES)} training and {len(NAMES)} validation guides at {DEST}')


if __name__ == '__main__':
    main()
