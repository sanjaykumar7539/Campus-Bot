"""Build a college-scope-balanced continuation dataset without changing old data."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FALLBACK = 'Verified information for the requested college is unavailable.'

def build():
    old = ROOT / 'training/grounded-nlp'
    rows = [json.loads(line) for line in (old / 'train.jsonl').read_text(encoding='utf-8').splitlines()]
    positives = [row for row in rows if row['college'] == row['evidence_college']]
    facts = {row['fact_id']: row for row in positives}
    train = list(positives)
    patterns = [
        ('When did the {college} college begin?', 'established'),
        ('Give the recorded founding year for {college}.', 'established'),
        ('What UG and PG totals does {college} have?', 'program_counts'),
        ('Tell me the autonomy year of {college} college.', 'autonomous'),
        ('Explain the {college} institution name.', 'college_name'),
        ('{college} college eppo aarambichanga?', 'established'),
    ]
    for college in ['pharmacy', 'nursing', 'polytechnic', 'school', 'arts & science', 'education', 'naturopathy']:
        for pattern, fact in patterns:
            train.append({'question': pattern.format(college=college), 'answer': FALLBACK,
                'context': facts[fact]['context'], 'college': college, 'evidence_college': 'engineering',
                'fact_id': 'scope_' + college, 'source_url': ''})
    for fact, question in [
        ('established', 'engineering college eppo aarambichanga?'),
        ('college_name', 'EGSPEC full peru enna?'),
        ('autonomous', 'engineering autonomous eppo aachu?'),
        ('program_counts', 'engineering la ethana UG PG courses irukku?'),
    ]:
        train.append({**facts[fact], 'question': question})
    test = []
    for fact, question in [
        ('established', 'State the opening year shown in the engineering evidence.'),
        ('program_counts', 'Give both engineering programme totals from this record.'),
        ('college_name', 'EGSPEC oda full name sollunga.'),
        ('autonomous', 'engineering autonomy vandha varusham sollunga.'),
    ]:
        test.append({**facts[fact], 'question': question})
    for college, question in [
        ('pharmacy', 'Can this engineering record establish when pharmacy opened?'),
        ('nursing', 'Nursing founding year enna, indha record padi?'),
        ('polytechnic', 'Which founding year is verified for the polytechnic here?'),
        ('school', 'Does this evidence verify when the school was founded?'),
    ]:
        test.append({'question': question, 'answer': FALLBACK, 'context': facts['established']['context'],
            'college': college, 'evidence_college': 'engineering', 'fact_id': 'scope_' + college, 'source_url': ''})
    validation = [json.loads(line) for line in (old / 'validation.jsonl').read_text(encoding='utf-8').splitlines()]
    splits = {'train': train, 'validation': validation, 'test': test}
    questions = {name: {row['question'].casefold() for row in values} for name, values in splits.items()}
    assert not questions['train'] & (questions['validation'] | questions['test'])
    assert not questions['validation'] & questions['test']
    out = ROOT / 'training/college-scope-20261017'
    out.mkdir(exist_ok=True)
    for name, values in splits.items():
        (out / f'{name}.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in values), encoding='utf-8')
    manifest = {'counts': {name: len(values) for name, values in splits.items()},
        'languages': ['English', 'Tanglish'], 'fresh_source_verification': False,
        'facts': 'Existing stored reference records, not newly verified current facts',
        'task': 'Answer from matching college evidence; reject evidence from another college',
        'scope': 'Unseen question phrasing; fact identities and evidence can overlap',
        'college_mismatch_training_examples': sum(row['college'] != row['evidence_college'] for row in train)}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest

if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
