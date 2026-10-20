import pytest

from src.core.rag_chain import RAGChain


@pytest.mark.parametrize('question,fact_id,expected', [
    ('Naalaiku Mechanical ku Model Exams irukka?', 'operational_event', 'live dated notice'),
    ('What time does the Central Library close?', 'operational_facility', 'exact live opening status'),
    ('Can I meet the Principal morning?', 'operational_person', 'Administrative Office'),
    ('Hall Ticket tholanjiduchu, duplicate epdi vaangarathu?', 'operational_document', 'Controller of Examinations'),
    ('Physics lab manual enga kedaikkum?', 'operational_lab', 'department LMS'),
])
def test_operational_questions_get_specific_safe_guidance(question, fact_id, expected):
    result = RAGChain().invoke(question)
    assert result['fact_id'] == fact_id
    assert result['is_grounded']
    assert expected in result['answer']
    assert 'Admissions information:' not in result['answer']
