from src.utils.translator import detect_language, resolve_language, translate_text
from src.core.campus_operational_answers import operational_answer

def test_tamil_script_detection():
    assert detect_language('கட்டணம் எவ்வளவு?') == 'ta'

def test_thanglish_detection():
    assert detect_language('exam eppo iruku') == 'tanglish'

def test_explicit_language_wins():
    assert resolve_language('hello', 'ta') == 'ta'

def test_thanglish_translation_is_offline_safe():
    assert translate_text('exam eppo', 'en', 'tanglish') == 'exam eppo'


def test_operational_answer_uses_the_users_thanglish_style():
    result = operational_answer('Naalaiku Mechanical ku Model Exams irukka?')
    assert result is not None
    assert 'Ketta event:' in result['answer']
    assert 'confirm pannunga' in result['answer'].casefold()


def test_operational_answer_uses_tamil_for_tamil_question():
    result = operational_answer('நாளைக்கு model exams இருக்கா?')
    assert result is not None
    assert 'தற்போதைய நிலை:' in result['answer']
