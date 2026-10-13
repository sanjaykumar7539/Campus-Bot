"""Language detection/translation helpers with offline-safe fallbacks."""
import re

SUPPORTED_LANGUAGES = {
    'auto': 'Auto', 'en': 'English', 'ta': 'Tamil', 'tanglish': 'Thanglish',
    'hi': 'Hindi', 'te': 'Telugu', 'ml': 'Malayalam', 'kn': 'Kannada',
}
DEFAULT_LANGUAGE = 'en'
# langdetect is unreliable on short ASCII strings (e.g. "fees", "hi", "hostel");
# below this length, skip detection entirely and assume English.
MIN_LENGTH_FOR_DETECTION = 15

THANGLISH_HINTS = {
    'enna', 'epadi', 'eppadi', 'iruku', 'irukka', 'iruntha', 'venum', 'veenum',
    'sollu', 'solla', 'pannu', 'panna', 'enga', 'eppo', 'yaaru', 'yaru', 'intha',
    'indha', 'adhu', 'athu', 'namma', 'enaku', 'enakku', 'epdi', 'irukku', 'kedaikum',
    'college la', 'fees la', 'exam eppo', 'admission epadi', 'department la',
}


def _has_tamil_script(text: str) -> bool:
    return bool(re.search(r'[\u0B80-\u0BFF]', text or ''))


def _looks_thanglish(text: str) -> bool:
    lowered = (text or '').lower()
    return any(hint in lowered for hint in THANGLISH_HINTS)


def detect_language(text: str) -> str:
    if not text or not text.strip():
        return DEFAULT_LANGUAGE
    if _has_tamil_script(text):
        return 'ta'
    if _looks_thanglish(text):
        return 'tanglish'
    stripped = text.strip()
    if len(stripped) < MIN_LENGTH_FOR_DETECTION and stripped.isascii():
        return DEFAULT_LANGUAGE
    try:
        from langdetect import detect, DetectorFactory, LangDetectException
        DetectorFactory.seed = 0
        try:
            code = detect(text)
            return code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        except LangDetectException:
            return DEFAULT_LANGUAGE
    except ImportError:
        return DEFAULT_LANGUAGE


def resolve_language(text: str, requested: str | None) -> str:
    if requested and requested != 'auto' and requested in SUPPORTED_LANGUAGES:
        return requested
    return detect_language(text)


def translate_text(text: str, target_lang: str, source_lang: str = 'auto') -> str:
    if not text or not text.strip() or target_lang == source_lang:
        return text
    if target_lang == 'tanglish' or source_lang == 'tanglish':
        return text
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        return translated or text
    except Exception:
        return text


def language_instruction(code: str) -> str:
    instructions = {
        'ta': 'Reply in clear conversational Tamil script. Keep college names, codes and technical terms unchanged.',
        'tanglish': 'Reply in natural Thanglish (Tamil written using English letters), simple and easy to understand.',
        'hi': 'Reply in simple Hindi.', 'te': 'Reply in simple Telugu.',
        'ml': 'Reply in simple Malayalam.', 'kn': 'Reply in simple Kannada.',
    }
    return instructions.get(code, 'Reply in clear, simple English.')


def language_name(code: str) -> str:
    return SUPPORTED_LANGUAGES.get(code, code)
