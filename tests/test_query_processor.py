from src.core.query_processor import QueryProcessor

def test_extracts_intent_and_metadata():
    a = QueryProcessor().analyze('AI&DS regulation 2023 sem 5 exam timetable')
    assert a.intent == 'exam'
    assert a.metadata['department'] == 'AI&DS'
    assert a.metadata['regulation'] == '2023'
    assert a.metadata['semester'] == '5'

def test_normalizes_whitespace():
    assert QueryProcessor().analyze(' fee   structure ').normalized == 'fee structure'
