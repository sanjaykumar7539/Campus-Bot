import pytest
from src.core.college_scope import requested_colleges, mentioned_colleges, filter_college_evidence
from src.core.rag_chain import RAGChain
from src.core.verified_college_answers import lookup_verified_answer
from src.chatbot.fallback_handler import FallbackHandler


@pytest.mark.parametrize('college', ['engineering', 'pharmacy', 'nursing', 'polytechnic', 'school', 'arts & science', 'education', 'naturopathy'])
def test_single_college_rejects_other_college_details(college):
    headings = {'education': 'EGS Pillay College of Education', 'school': 'EGS Pillay International School'}
    lines = '\n'.join(f'{headings.get(name, name + " college")} offers verified programs.'
                      for name in ['engineering', 'pharmacy', 'nursing', 'polytechnic', 'school', 'arts & science', 'education', 'naturopathy'])
    query = headings.get(college, college) + ' details'
    result = filter_college_evidence(query, [{'text': lines, 'source_url': 'https://admissions.egspgroup.in/'}], RAGChain._clean_evidence)
    assert len(result) == 1
    assert len(result[0]['text'].splitlines()) == 1
    assert mentioned_colleges(result[0]['text']) == {college}


def test_mixed_directory_heading_does_not_transfer_following_facts():
    evidence = [{'text': 'Engineering college\nB.Tech programs.\nPharmacy college\nB.Pharm programs.',
                 'source_url': 'https://egspec.org/engineering'}]
    result = filter_college_evidence('engineering programs', evidence, RAGChain._clean_evidence)
    assert 'B.Tech' in result[0]['text']
    assert 'Pharmacy' not in result[0]['text']
    assert 'B.Pharm' not in result[0]['text']


def test_mixed_college_sentence_is_rejected():
    assert filter_college_evidence('engineering', [{'text': 'Engineering and Pharmacy colleges offer courses.',
        'source_url': 'https://egspec.org/'}], RAGChain._clean_evidence) == []


def test_group_directory_is_only_requested_explicitly():
    assert requested_colleges('all engineering courses') == {'engineering'}
    assert len(requested_colleges('list all colleges')) > 1
    assert requested_colleges('college and school of nursing') == {'nursing'}
    assert len(RAGChain._retrieval_queries('all engineering college details')) == 2


@pytest.mark.parametrize('query,expected', [
    ('M Pharm branches', 'pharmacy'),
    ('B.Pharm eligibility', 'pharmacy'),
    ('Education college subject combinations', 'education'),
    ('BNYS duration', 'naturopathy'),
    ('Arts science departments', 'arts & science'),
])
def test_program_names_and_common_word_orders_preserve_college_scope(query, expected):
    assert requested_colleges(query) == {expected}


def test_foreign_college_cannot_reuse_engineering_verified_fact():
    assert lookup_verified_answer('When was the pharmacy college founded?', context_fact_id='established') is None
    assert lookup_verified_answer('Tell me nursing college NIRF rank') is None


def test_scoped_fallback_does_not_offer_other_college_contact():
    answer = FallbackHandler().handle('What are pharmacy fees?')
    assert 'pharmacy' in answer
    assert 'engineering' not in answer.casefold()
    assert 'admissions.egspgroup.in' not in answer


def test_answer_pipeline_filters_mixed_college_page():
    from tests.test_rag_chain import FakeRetriever
    evidence = [{'text': 'Engineering college offers undergraduate B.Tech programs in civil engineering.\nPharmacy college offers B.Pharm programs.',
                 'source_url': 'https://admissions.egspgroup.in/admissions',
                 'source': 'directory.txt', 'page': '0', 'score': 0.9}]
    result = RAGChain(FakeRetriever(evidence)).invoke('engineering programs')
    assert result['is_grounded']
    assert 'B.Tech' in result['answer']
    assert 'Pharmacy' not in result['answer']
    assert 'B.Pharm' not in result['answer']
