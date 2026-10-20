import json
from pathlib import Path

import pytest

from src.core.rag_chain import RAGChain


@pytest.mark.parametrize('query,fact_id,phrase', [
    ('sports', 'engineering_sports', 'Mr. D. Velavan'),
    ('extra curricular activities enna', 'engineering_extracurricular', 'Fine Arts Club'),
    ('endha season la events vaipanga', 'engineering_event_timing', '27 March 2025'),
    ('nss social service', 'engineering_social_service', 'Plastic-Free Awareness'),
    ('yaru kuda collaboration la irukanga', 'engineering_collaborations', 'Oracle Academy'),
    ('club la epadi join pannalam', 'engineering_clubs_join', 'Mrs. M. Kavitha'),
])
def test_student_life_questions_use_source_backed_fact(query, fact_id, phrase):
    result = RAGChain().invoke(query)
    assert result['is_grounded']
    assert result['fact_id'] == fact_id
    assert phrase in result['answer']
    assert result['sources']


def test_student_life_facts_have_verified_scope_and_no_fixed_season_claim():
    path = Path(__file__).resolve().parents[1] / 'training' / 'student-life-20261019' / 'train.jsonl'
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    assert len(rows) == 6
    assert len({row['fact_id'] for row in rows}) == 6
    assert all(row['college'] == 'engineering' for row in rows)
    assert all(row['source_url'].startswith('https://') for row in rows)
    season = next(row for row in rows if row['fact_id'] == 'engineering_event_timing')
    assert 'no verified fixed annual' in season['answer']
    assert 'not future promises' in season['answer']


def test_sports_season_followup_uses_dated_event_fact():
    result = RAGChain().invoke('endha season la vaipanga?', context_fact_id='engineering_sports')
    assert result['fact_id'] == 'engineering_event_timing'
    assert 'no verified fixed annual sports or cultural season' in result['answer']
