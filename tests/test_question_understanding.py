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

@pytest.mark.parametrize('question', [
    'details', 'anything special', 'any thing special', 'environment',
    'enviroment', 'give the environment',
])
def test_vague_request_asks_question_without_loading_retrieval(question):
    class NeverRetrieve:
        def retrieve_bundle(self, *args, **kwargs):
            raise AssertionError('Vague question must not search unrelated records')
    result = RAGChain(NeverRetrieve()).invoke(question)
    assert result['reason'] == 'Clarification needed'
    answer = FallbackHandler().handle(question, result['reason'])
    assert 'Which college' in answer


def test_misspelled_vague_request_asks_for_a_topic():
    result = RAGChain().invoke('tell about somwthig', context_fact_id='engineering_overview')
    assert result['reason'] == 'Clarification needed'
    assert 'Which college' in result['answer']

def test_tanglish_establishment_question_uses_verified_fact(monkeypatch):
    # This phrasing matches a verified alias after conservative normalization.
    result = RAGChain().invoke('When did it open?')
    assert result['is_grounded']
    assert result['fact_id'] == 'established'

def test_vague_follow_up_uses_existing_verified_topic():
    result = RAGChain().invoke('adhu', context_fact_id='established')
    assert result['fact_id'] == 'established'


@pytest.mark.parametrize('query,fact_id', [
    ('give the placement detials da', 'placements'),
    ('ok good what is the highest placement', 'placements'),
    ('gieve the infrastucture', 'infrastructure'),
    ('ok which is most deserving course in this collage', 'nba_programs_scope'),
    ('give the student feedback', 'student_feedback'),
    ('tel me abot espec', 'engineering_overview'),
    ('pharmasy course detials', 'pharmacy_overview'),
    ('nursng college corses', 'nursing_overview'),
    ('politechnic diploma corses', 'polytechnic_overview'),
    ('arts and scince college courses', 'arts_science_overview'),
])
def test_common_misspellings_route_to_verified_answers(query, fact_id):
    result = RAGChain().invoke(query)
    assert result['is_grounded']
    assert result['fact_id'] == fact_id


@pytest.mark.parametrize('query,fact_id,expected', [
    ('polytecnic join panna enna qualification', 'polytechnic_admission', '35%'),
    ('arts clg la hostel library iruka', 'arts_science_facilities', '30,000'),
    ('pharmasy admision contact', 'pharmacy_admission_contact', '99768 88999'),
    ('nurshing admision contact', 'nursing_admission_contact', '99768 88999'),
    ('b ed intake evlo', 'education_overview', '100'),
])
def test_new_student_typos_route_to_institution_specific_fact(query, fact_id, expected):
    result = RAGChain().invoke(query)
    assert result['is_grounded']
    assert result['fact_id'] == fact_id
    assert expected in result['answer']
