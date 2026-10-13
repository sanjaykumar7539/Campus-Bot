from fastapi.testclient import TestClient
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
    assert 'id="homeVoiceBtn"' in html
    assert 'id="chatVoiceBtn"' in html
    assert 'id="voiceLanguage"' in html
    assert "speechSynthesis" in html
