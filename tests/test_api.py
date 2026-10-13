from fastapi.testclient import TestClient
from src.api.main import app
import src.api.routes as routes

class FakeLogger:
    def log(self, **kwargs): return 42


def test_frontend_and_api_are_one_server(monkeypatch):
    monkeypatch.setattr(routes, 'chat_logger', FakeLogger())
    client = TestClient(app)
    assert client.get('/').status_code == 200
    r = client.post('/api/v1/chat', json={'session_id':'session123','message':'What is EGSPEC?','language':'en'})
    assert r.status_code == 200
    body = r.json()
    assert body['message_id'] == 42
    assert body['answer'] == 'EGSPEC is E. G. S. Pillay Engineering College.'


def test_health_is_lightweight():
    client = TestClient(app)
    r = client.get('/api/v1/health')
    assert r.status_code == 200
    assert 'model_status' in r.json()
