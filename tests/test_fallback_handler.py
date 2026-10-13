from src.chatbot.fallback_handler import FallbackHandler
from config import config


def test_fallback_only_offers_admissions_contact_details(monkeypatch):
    monkeypatch.setattr(config, 'ESCALATION_EMAIL', 'admissions@example.edu')
    monkeypatch.setattr(config, 'ESCALATION_PHONE', '+91 1234567890')
    monkeypatch.setattr(config, 'ADMISSIONS_CONTACT_URL', 'https://admissions.egspgroup.in/')

    answer = FallbackHandler().handle('unknown question')

    assert 'admissions@example.edu' in answer
    assert '+91 1234567890' in answer
    assert 'https://admissions.egspgroup.in/' in answer
    assert 'Tip:' not in answer
    assert 'Try asking about' not in answer
