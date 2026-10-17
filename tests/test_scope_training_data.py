import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'training/college-scope-20261017'

def rows(name):
    return [json.loads(line) for line in (ROOT / f'{name}.jsonl').read_text(encoding='utf-8').splitlines()]

def test_scope_training_balances_negative_examples():
    train = rows('train')
    assert len(train) == 88
    assert sum(row['college'] != row['evidence_college'] for row in train) == 42
    assert all(row['answer'] == 'Verified information for the requested college is unavailable.'
               for row in train if row['college'] != row['evidence_college'])

def test_new_evaluation_questions_are_disjoint():
    split = {name: {row['question'].casefold() for row in rows(name)}
             for name in ['train', 'validation', 'test']}
    assert not split['train'] & split['validation']
    assert not split['train'] & split['test']
    assert not split['validation'] & split['test']
    assert len(rows('test')) == 8

def test_matched_training_rows_retain_source_evidence():
    assert all(row['source_url'].startswith('https://egspec.org/') and row['answer'] == row['context']
               for row in rows('train') if row['college'] == row['evidence_college'])
