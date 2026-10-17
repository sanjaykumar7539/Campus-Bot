import pytest
from src.core.college_topics import topics_for, expand_question
from src.core.college_scope import requested_colleges
from src.core.rag_chain import RAGChain
from tests.test_rag_chain import FakeRetriever

@pytest.mark.parametrize('question,topic', [
    ('hostel irukka?', 'Hostel'), ('விடுதி வசதி இருக்கா?', 'Hostel'),
    ('placement eppadi irukku?', 'Placements'), ('வேலைவாய்ப்பு விவரம்', 'Placements'),
    ('bus route sollu', 'Transport'), ('பேருந்து விவரம்', 'Transport'),
    ('library timings?', 'Facilities'), ('ஆசிரியர் விவரம்', 'Faculty'),
    ('scholarship details?', 'Scholarships'), ('தேர்வு முடிவு?', 'Examinations'),
    ('latest news?', 'Updates'), ('கட்டணம் எவ்வளவு?', 'Fees'),
])
def test_college_topics_across_phrasings(question, topic):
    assert topic in topics_for(question)
    assert topic in topics_for(expand_question(question))

@pytest.mark.parametrize('query,expected', [
    ('மருந்தியல் கல்லூரி கட்டணம்', 'pharmacy'),
    ('செவிலியர் விடுதி விவரம்', 'nursing'),
    ('பொறியியல் கட்டணம்', 'engineering'),
])
def test_tamil_preserves_college_scope(query, expected):
    assert requested_colleges(query) == {expected}

def test_hostel_answer_is_readable_and_excludes_other_colleges():
    evidence = [{
        'text': 'Engineering college hostel provides accommodation and mess facilities for students.\nPharmacy college offers separate hostel accommodation.',
        'source_url': 'https://egspec.org/hostel', 'source': 'hostel.txt',
        'page': '0', 'score': 0.9,
    }]
    result = RAGChain(FakeRetriever(evidence)).invoke('engineering hostel irukka?')
    assert result['is_grounded']
    assert 'accommodation' in result['answer']
    assert 'Pharmacy' not in result['answer']

def test_topic_search_does_not_expand_to_unrelated_courses():
    queries = RAGChain._retrieval_queries('engineering hostel details')
    assert any('accommodation' in query for query in queries)
    assert not any('accreditation ranking admissions' in query for query in queries)

def test_named_college_general_facts_are_not_discarded():
    evidence = [{
        'text': 'Engineering college was founded to provide technical education to rural students.',
        'source_url': 'https://egspec.org/about', 'source': 'about.txt', 'page': '0', 'score': 0.9,
    }]
    result = RAGChain(FakeRetriever(evidence))._answer_from_retrieval('engineering background')
    assert result['is_grounded']
    assert 'rural students' in result['answer']
