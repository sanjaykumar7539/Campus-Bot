"""Create evidence-grounded training and separate unseen-phrasing evaluations."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FALLBACK = 'Verified information for the requested college is unavailable.'


def main():
    source = ROOT / 'training/online-college-qa/train.jsonl'
    original = [json.loads(line) for line in source.read_text(encoding='utf-8').splitlines()]
    facts = {}
    train = []
    for row in original:
        facts.setdefault(row['fact_id'], row)
        train.append({**row, 'context': row['answer'], 'college': 'engineering', 'evidence_college': 'engineering'})
        train.append({**row, 'question': 'Please tell me: ' + row['question'],
                      'context': row['answer'], 'college': 'engineering', 'evidence_college': 'engineering'})
    for college in ['pharmacy', 'nursing', 'polytechnic', 'school', 'arts & science', 'education', 'naturopathy']:
        train.append({'question': f'When was the {college} college established?',
                      'answer': FALLBACK, 'context': facts['established']['answer'],
                      'college': college, 'evidence_college': 'engineering',
                      'fact_id': 'scope_' + college, 'source_url': ''})
    training_ids = {row['question'].casefold() for row in train}
    phrasing = {
        'established': ('Which year did engineering college open?', 'Engineering college started in which year?'),
        'college_name': ('Tell me the expanded college name for EGSPEC.', 'What do the letters EGSPEC stand for?'),
        'autonomous': ('When did engineering college get autonomy?', 'Which year marks autonomous status for engineering?'),
        'program_counts': ('How many UG and PG degrees are recorded for engineering?', 'Give the recorded undergraduate and postgraduate totals for engineering.'),
    }
    evaluation = {'validation': [], 'test': []}
    for fact_id, questions in phrasing.items():
        fact = facts[fact_id]
        for split, question in zip(evaluation, questions):
            evaluation[split].append({**fact, 'question': question, 'context': fact['answer'],
                'college': 'engineering', 'evidence_college': 'engineering'})
    for split, questions in [('validation', ['How old is the nursing college?', 'Give pharmacy founding year.']),
                             ('test', ['When did the pharmacy institution first open?', 'Tell me when nursing was founded.'])]:
        for question, college in zip(questions, ['nursing', 'pharmacy'] if split == 'validation' else ['pharmacy', 'nursing']):
            evaluation[split].append({'question': question, 'answer': FALLBACK,
                'context': facts['established']['answer'], 'college': college,
                'evidence_college': 'engineering', 'fact_id': 'scope_' + college, 'source_url': ''})
    out = ROOT / 'training/grounded-nlp'
    out.mkdir(exist_ok=True)
    splits = {'train': train, **evaluation}
    for name, rows in splits.items():
        if name != 'train' and any(row['question'].casefold() in training_ids for row in rows):
            raise RuntimeError('Question phrasing leaked into training')
        (out / f'{name}.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
    report = {'counts': {name: len(rows) for name, rows in splits.items()},
        'task': 'Evidence-grounded answers and college-scope fallback',
        'split': 'Unseen question phrasing; facts and supplied evidence may overlap',
        'languages': ['English'], 'source': str(source), 'fresh_source_verification': False}
    (out / 'manifest.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
