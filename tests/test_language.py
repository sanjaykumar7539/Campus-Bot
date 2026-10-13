from src.utils.translator import detect_language, resolve_language, translate_text

def test_tamil_script_detection():
    assert detect_language('கட்டணம் எவ்வளவு?') == 'ta'

def test_thanglish_detection():
    assert detect_language('exam eppo iruku') == 'tanglish'

def test_explicit_language_wins():
    assert resolve_language('hello', 'ta') == 'ta'

def test_thanglish_translation_is_offline_safe():
    assert translate_text('exam eppo', 'en', 'tanglish') == 'exam eppo'
