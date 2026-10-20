from fastapi.testclient import TestClient
from pathlib import Path

from src.api.main import app
from src.voice.voice_config import get_voice_languages

def test_indian_voice_languages():
    langs = get_voice_languages()
    assert langs["en"]["locale"] == "en-IN"
    assert langs["ta"]["locale"] == "ta-IN"
    assert langs["hi"]["locale"] == "hi-IN"
    assert langs["te"]["locale"] == "te-IN"
    assert langs["ml"]["locale"] == "ml-IN"
    assert langs["kn"]["locale"] == "kn-IN"

def test_voice_languages_api():
    r = TestClient(app).get("/api/v1/voice/languages")
    assert r.status_code == 200
    body = r.json()
    assert body["engine"] == "browser-web-speech"
    assert "ta" in body["languages"]

def test_frontend_has_voice_assistant():
    html = TestClient(app).get("/").text
    assert 'id="root"' in html

    # The production UI is a React bundle, so its interactive controls are
    # rendered client-side instead of being present in the index shell.
    frontend = Path(__file__).parents[1] / "frontend-react" / "src"
    chat = (frontend / "components" / "Chat.jsx").read_text(encoding="utf-8")
    header = (frontend / "components" / "Header.jsx").read_text(encoding="utf-8")
    voice = (frontend / "hooks" / "useVoice.js").read_text(encoding="utf-8")
    assert 'aria-label="Voice input"' in chat
    assert "Auto-speak" in header
    assert "speechSynthesis" in voice
    assert "localStorage.getItem('egspec_auto_speak') === 'true'" in voice
