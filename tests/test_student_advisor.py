import pytest

from src.core.rag_chain import RAGChain
from src.core.institution_guides import GUIDES
from src.utils.answer_presentation import display_answer, LOCALIZED


class NeverRetrieve:
    def retrieve_bundle(self, *args, **kwargs):
        raise AssertionError('Bounded student guidance should not search the entire corpus')


@pytest.mark.parametrize('question', [
    'I finished 12th. Help me choose a suitable course',
    'I am a new student and want to join nursing',
    'Which course is best for me?',
])
def test_adviser_requests_decision_inputs(question):
    answer = RAGChain(NeverRetrieve()).invoke(question)['answer']
    assert all(word in answer.lower() for word in ('qualification', 'interests', 'budget'))


def test_compound_question_keeps_all_requested_topics():
    result = RAGChain(NeverRetrieve()).invoke(
        'What documents and scholarships do I need to apply to EGSPEC?')
    assert all(word in result['answer'] for word in ('Admissions', 'Documents', 'Scholarships', '3806'))
    assert len(result['sources']) == 2
    assert 'general preparation guidance' in result['answer']


@pytest.mark.parametrize('question', [
    'Is a nursing degree an assured job?',
    'Will CSE definitely get me a job?',
    'Does a Pharmacy degree guarantee employment?',
])
def test_job_guarantees_are_explained_without_irrelevant_retrieval(question):
    result = RAGChain(NeverRetrieve()).invoke(question)
    assert 'does not guarantee a job' in result['answer']


def test_cutoff_does_not_become_a_promised_seat():
    result = RAGChain(NeverRetrieve()).invoke('With cutoff 180 can I definitely get IT in EGSPEC?')
    assert 'cannot guarantee admission' in result['answer']
    assert 'not an official closing cutoff' in result['answer']


def test_nursing_fee_is_not_answered_using_engineering_facts():
    result = RAGChain(NeverRetrieve()).invoke('exact nursing tuition for 2027')
    assert 'nursing' in result['answer'].lower()
    assert 'could not verify' in result['answer']
    assert '3806' not in result['answer']


def test_short_season_question_keeps_sports_topic():
    result = RAGChain(NeverRetrieve()).invoke('which month?', context_fact_id='engineering_sports')
    assert result['fact_id'] == 'engineering_event_timing'


@pytest.mark.parametrize('fact_id', list(GUIDES))
@pytest.mark.parametrize('language', ['ta', 'tanglish'])
def test_each_institution_has_real_localized_intro(fact_id, language):
    rendered, actual = display_answer({'answer': GUIDES[fact_id], 'fact_id': fact_id}, language)
    assert actual == language
    assert rendered != GUIDES[fact_id]
    assert 'http' not in rendered
    assert rendered == LOCALIZED[fact_id][language] or fact_id == 'engineering_overview'


def test_fee_followup_is_never_replaced_with_translated_pharmacy_overview():
    result = RAGChain(NeverRetrieve()).invoke('what about its fees?', context_fact_id='pharmacy_overview')
    rendered, language = display_answer(result, 'ta')
    assert 'உறுதிப்படுத்தப்படவில்லை' in rendered
    assert language == 'ta'
    assert 'D.Pharm — 2' not in rendered


def test_display_hides_source_footer_but_preserves_internal_evidence():
    result = {'answer': GUIDES['arts_science_overview'], 'fact_id': 'arts_science_overview',
              'sources': [{'document': 'https://egspasc.ac.in/about/history'}]}
    rendered, language = display_answer(result, 'en')
    assert 'https://' not in rendered
    assert result['sources'][0]['document'].startswith('https://')


def test_retrieved_privacy_and_marketing_text_is_not_student_advice():
    text = ('Related Tags: #Education\n'
            'Right to limit use and disclosure of sensitive personal data under California privacy law.\n'
            'Professional or employment-related information Business contact details.\n'
            'Mechanical Engineering laboratory has a CNC machine.')
    lines = RAGChain._clean_evidence(text)
    assert lines == ['Mechanical Engineering laboratory has a CNC machine.']
