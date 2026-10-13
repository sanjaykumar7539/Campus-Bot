from fastapi.testclient import TestClient
from src.api.main import app
from config import config

client = TestClient(app)


def test_product_api():
    r = client.get('/api/v1/product')
    assert r.status_code == 200
    assert r.json()['product_name'] == config.PRODUCT_NAME


def test_product_status_api():
    r = client.get('/api/v1/product/status')
    assert r.status_code == 200
    assert 'components' in r.json()


def test_admin_analytics_disabled_by_default(monkeypatch):
    monkeypatch.setattr(config, 'ADMIN_API_KEY', '')
    r = client.get('/api/v1/admin/analytics')
    assert r.status_code == 404


def test_admin_analytics_rejects_wrong_key(monkeypatch):
    monkeypatch.setattr(config, 'ADMIN_API_KEY', 'secret')
    r = client.get('/api/v1/admin/analytics', headers={'X-Admin-Key': 'wrong'})
    assert r.status_code == 401
