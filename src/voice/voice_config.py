"""Supported Indian-language voice locales for the browser voice assistant.

Audio capture and speech synthesis happen in the user's browser. The backend
returns the response language so the frontend can choose an Indian locale voice.
"""
VOICE_LANGUAGES = {
    "auto": {"name": "Auto", "locale": "en-IN"},
    "en": {"name": "English (India)", "locale": "en-IN"},
    "ta": {"name": "Tamil", "locale": "ta-IN"},
    "hi": {"name": "Hindi", "locale": "hi-IN"},
    "te": {"name": "Telugu", "locale": "te-IN"},
    "ml": {"name": "Malayalam", "locale": "ml-IN"},
    "kn": {"name": "Kannada", "locale": "kn-IN"},
    "tanglish": {"name": "Thanglish", "locale": "en-IN"},
}

def get_voice_languages():
    return VOICE_LANGUAGES.copy()
