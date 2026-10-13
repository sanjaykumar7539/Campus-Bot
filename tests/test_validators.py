from src.utils.validators import validate_query

def test_empty_query_rejected():
    assert not validate_query('   ')[0]

def test_script_injection_rejected():
    assert not validate_query('<script>alert(1)</script>')[0]

def test_normal_question_allowed():
    assert validate_query('What is the exam timetable?')[0]
