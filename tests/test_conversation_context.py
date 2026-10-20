from src.core.conversation_context import contextualize_question
from src.core.rag_chain import RAGChain


def test_followup_inherits_only_verified_previous_institution():
    assert contextualize_question('what about its fees?', 'pharmacy_overview') == (
        'EGS Pillay College of Pharmacy: what about its fees?'
    )
    assert contextualize_question('and its eligibility?', 'arts_science_overview') == (
        'EGS Pillay Arts and Science College: and its eligibility?'
    )
    assert contextualize_question('and Sirkali timing?', 'engineering_transport') == (
        'EGS Pillay Engineering College: and Sirkali timing?'
    )


def test_explicit_new_institution_and_group_query_override_previous_context():
    assert contextualize_question('What about EGS Pillay Polytechnic?', 'pharmacy_overview') == (
        'What about EGS Pillay Polytechnic?'
    )
    assert contextualize_question('List all colleges under EGS Pillay Group', 'pharmacy_overview') == (
        'List all colleges under EGS Pillay Group'
    )


def test_unrelated_or_vague_query_does_not_inherit_college():
    assert contextualize_question('What is the weather today?', 'pharmacy_overview') == (
        'What is the weather today?'
    )
    assert contextualize_question('details', 'pharmacy_overview') == 'details'
    assert contextualize_question('what about its fees?', 'group_institutions') == 'what about its fees?'


def test_replay_followup_works_for_non_engineering_college():
    result = RAGChain().invoke('adhu', context_fact_id='pharmacy_overview')
    assert result['fact_id'] == 'pharmacy_overview'
    assert 'D.Pharm' in result['answer']


def test_transport_followup_uses_previous_route_fact_not_generic_retrieval():
    class NeverRetrieve:
        def retrieve_bundle(self, *args, **kwargs):
            raise AssertionError('Route follow-up should use the verified route fact')

    result = RAGChain(NeverRetrieve()).invoke('and Sirkali timing?', context_fact_id='engineering_transport')
    assert result['fact_id'] == 'engineering_transport'
    assert 'Sirkali — 7:10 AM' in result['answer']
    assert 'Mannargudi' not in result['answer']


def test_fees_followup_is_scoped_to_previous_college_without_guessing():
    class NeverRetrieve:
        def retrieve_bundle(self, *args, **kwargs):
            raise AssertionError('Missing verified fee must not retrieve unrelated college data')

    result = RAGChain(NeverRetrieve()).invoke('what about its fees?', context_fact_id='pharmacy_overview')
    assert 'EGS Pillay College of Pharmacy' in result['answer']
    assert 'current fee amount' in result['answer']
    assert '₹' not in result['answer']


def test_explicit_new_college_switches_overview():
    result = RAGChain().invoke('What about EGS Pillay Polytechnic?', context_fact_id='pharmacy_overview')
    assert result['fact_id'] == 'polytechnic_overview'
    assert 'What is a Polytechnic?' in result['answer']


def test_short_course_and_facility_followups_keep_arts_context():
    class NeverRetrieve:
        def retrieve_bundle(self, *args, **kwargs):
            raise AssertionError('Verified follow-up should not need corpus retrieval')

    chain = RAGChain(NeverRetrieve())
    courses = chain.invoke('and its courses?', context_fact_id='arts_science_overview')
    facilities = chain.invoke('what about hostel?', context_fact_id='arts_science_overview')
    assert courses['fact_id'] == 'arts_science_overview'
    assert 'What is Arts & Science?' in courses['answer']
    assert facilities['fact_id'] == 'arts_science_facilities'
    assert 'Arts and Science' in facilities['answer']
