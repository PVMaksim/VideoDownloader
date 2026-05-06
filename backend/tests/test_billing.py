import sys

sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)

def test_routes_exist():
    """Проверяем, что все эндпоинты биллинга зарегистрированы"""
    from billing.router import router
    paths = [r.path for r in router.routes]
    assert "/billing/subscribe" in paths
    assert "/billing/subscription" in paths
    assert "/billing/cancel" in paths
    assert "/billing/webhook" in paths

def test_subscribe_requires_auth(client):
    """POST /billing/subscribe без токена → 401/403"""
    resp = client.post("/billing/subscribe", json={})
    assert resp.status_code in (401, 403)

def test_webhook_missing_signature(client):
    """Вебхук без заголовка подписи → 400"""
    resp = client.post("/billing/webhook", content=b"{}")
    assert resp.status_code == 400
