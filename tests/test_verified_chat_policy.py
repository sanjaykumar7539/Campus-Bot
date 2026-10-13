from fastapi.testclient import TestClient

from src.api import routes
from src.api.main import app
from config import config


def test_chat_uses_verified_answer_without_model_readiness(monkeypatch):
    logged = {}
    monkeypatch.setattr(routes.chat_logger, 'log', lambda **kwargs: logged.update(kwargs) or 1)
    monkeypatch.setattr(routes.session_manager, 'add_message', lambda *args: None)
    monkeypatch.setattr(
        routes,
        'check_readiness',
        lambda: (_ for _ in ()).throw(AssertionError('model readiness must not be required')),
    )

    response = TestClient(app).post(
        '/api/v1/chat',
        json={'session_id': 'verified-session', 'message': 'What is EGSPEC?'},
    )

    assert response.status_code == 200
    result = response.json()
    assert result['answer'] == 'EGSPEC is E. G. S. Pillay Engineering College.'
    assert result['is_grounded'] is True
    assert result['sources'] == []
    assert logged['sources'][0]['document'] == 'https://egspec.org/about/history'


def test_chat_unknown_question_returns_only_admissions_contact(monkeypatch):
    monkeypatch.setattr(routes.chat_logger, 'log', lambda **kwargs: 2)
    monkeypatch.setattr(routes.session_manager, 'add_message', lambda *args: None)
    monkeypatch.setattr(config, 'ESCALATION_EMAIL', '')
    monkeypatch.setattr(config, 'ESCALATION_PHONE', '')
    monkeypatch.setattr(config, 'ADMISSIONS_CONTACT_URL', 'https://admissions.egspgroup.in/')

    response = TestClient(app).post(
        '/api/v1/chat',
        json={'session_id': 'unknown-session', 'message': 'What is the weather tomorrow?'},
    )

    assert response.status_code == 200
    result = response.json()
    assert result['is_grounded'] is False
    assert result['answer'] == (
        'I do not have verified information about that in the institute records.\n\n'
        'For admissions assistance, contact the institute:\n'
        'Admissions information: https://admissions.egspgroup.in/'
    )
    assert result['quick_replies'] == []
    assert result['visuals'] == []
