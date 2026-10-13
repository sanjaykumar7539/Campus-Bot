from scripts.training_examples import messages_for, GROUNDING_INSTRUCTION
import json
from pathlib import Path


def test_grounded_prompt_keeps_college_ownership_and_evidence():
    row = {'question': 'When did nursing open?', 'context': 'Engineering college opened in 1995.',
           'college': 'nursing', 'evidence_college': 'engineering'}
    messages = messages_for(row)
    assert messages[0]['content'] == GROUNDING_INSTRUCTION
    assert 'Target college: nursing' in messages[1]['content']
    assert 'Evidence college: engineering' in messages[1]['content']
    assert row['context'] in messages[1]['content']


def test_evaluation_phrasings_are_held_out():
    root = Path(__file__).resolve().parents[1] / 'training/grounded-nlp'
    splits = {name: [json.loads(line) for line in (root / f'{name}.jsonl').read_text(encoding='utf-8').splitlines()]
              for name in ['train', 'validation', 'test']}
    questions = {name: {row['question'].casefold() for row in rows} for name, rows in splits.items()}
    assert not questions['train'] & questions['validation']
    assert not questions['train'] & questions['test']
    assert not questions['validation'] & questions['test']
    assert all(any(row['college'] != row['evidence_college'] for row in rows) for rows in splits.values())
