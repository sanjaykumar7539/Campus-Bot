import pytest
from src.core.question_understanding import normalize_question
from src.core.college_scope import requested_colleges
from src.core.rag_chain import RAGChain
from src.chatbot.fallback_handler import FallbackHandler

@pytest.mark.parametrize('query,college,topic', [
    ('engg hostal iruka?', 'engineering', 'hostel'),
    ('pharamcy admissOn details?', 'pharmacy', 'admission'),
    ('nursng hostel details', 'nursing', 'hostel'),
    ('how much would I need to pay for engineering?', 'engineering', 'fees'),
    ('engineering college stay on campus?', 'engineering', 'hostel'),
])
def test_question_normalization_preserves_scope(query, college, topic):
    normalized = normalize_question(query)
    assert requested_colleges(normalized) == {college}
    assert topic in normalized.casefold()

def test_dates_department_and_numbers_are_not_changed():
    question = 'CSE fees 2026 semester 3 Rs 45000'
    assert normalize_question(question) == question

def test_vague_request_asks_question_without_loading_retrieval():
    class NeverRetrieve:
        def retrieve_bundle(self, *args, **kwargs):
            raise AssertionError('Vague question must not search unrelated records')
    result = RAGChain(NeverRetrieve()).invoke('details')
    assert result['reason'] == 'Clarification needed'
    answer = FallbackHandler().handle('details', result['reason'])
    assert 'Which college' in answer

def test_tanglish_establishment_question_uses_verified_fact(monkeypatch):
    # This phrasing matches a verified alias after conservative normalization.
    result = RAGChain().invoke('When did it open?')
    assert result['is_grounded']
    assert result['fact_id'] == 'established'

def test_vague_follow_up_uses_existing_verified_topic():
    result = RAGChain().invoke('adhu', context_fact_id='established')
    assert result['fact_id'] == 'established'
