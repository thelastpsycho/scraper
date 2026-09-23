"""Verify the API fails closed, protects writes, and proxies assistant requests."""
import pytest

from app import create_app


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_TOKEN", "a" * 48)
    monkeypatch.setenv("APP_SESSION_SECRET", "b" * 48)
    monkeypatch.delenv("ALLOW_INSECURE_LOCAL_DEV", raising=False)
    monkeypatch.setenv("APP_HOST", "127.0.0.1")
    application = create_app()
    application.testing = True
    return application


def sign_in(client):
    result = client.post("/api/auth/login", json={"token": "a" * 48})
    assert result.status_code == 200
    return result.get_json()["csrf_token"]


def test_api_locked_when_unconfigured(monkeypatch):
    for name in ("APP_ACCESS_TOKEN", "APP_SESSION_SECRET", "ALLOW_INSECURE_LOCAL_DEV"):
        monkeypatch.delenv(name, raising=False)
    application = create_app()
    application.testing = True
    client = application.test_client()
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/pipeline/status").status_code == 503
    assert client.post("/api/auth/login", json={"token": "anything"}).status_code == 503


def test_login_csrf_logout_and_protected_get(app):
    client = app.test_client()
    assert client.get("/api/pipeline/status").status_code == 401
    assert client.post("/api/auth/login", json={"token": "wrong"}).status_code == 401
    csrf = sign_in(client)
    assert client.get("/api/pipeline/status").status_code == 200
    assert client.post("/api/auth/logout").status_code == 403
    response = client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
    assert response.status_code == 200
    assert client.get("/api/pipeline/status").status_code == 401


def test_unsafe_dev_requires_explicit_local_flag(monkeypatch):
    monkeypatch.delenv("APP_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("APP_SESSION_SECRET", raising=False)
    monkeypatch.setenv("ALLOW_INSECURE_LOCAL_DEV", "1")
    monkeypatch.setenv("APP_HOST", "0.0.0.0")
    remote = create_app().test_client()
    assert remote.get("/api/pipeline/status").status_code == 503
    monkeypatch.setenv("APP_HOST", "127.0.0.1")
    local = create_app().test_client()
    assert local.get("/api/pipeline/status").status_code == 200


def test_assistant_key_stays_server_side(app, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only-backend-secret")
    client = app.test_client()
    csrf = sign_in(client)
    seen = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "Inventory available."}}]}

    def fake_post(url, *, json, headers, timeout):
        seen.update(url=url, headers=headers, timeout=timeout, payload=json)
        return FakeResponse()

    monkeypatch.setattr("app.routes.assistant_routes.requests.post", fake_post)
    response = client.post("/api/assistant/chat",
                           json={"messages": [{"role": "user", "content": "Availability?"}]},
                           headers={"X-CSRF-Token": csrf})
    assert response.status_code == 200
    assert response.get_json()["choices"][0]["message"]["content"] == "Inventory available."
    assert seen["headers"]["Authorization"] == "Bearer test-only-backend-secret"
    assert seen["url"] == "https://api.deepseek.com/v1/chat/completions"


def test_assistant_rejects_invalid_payload_and_missing_key(app, monkeypatch):
    client = app.test_client()
    csrf = sign_in(client)
    assert client.post("/api/assistant/chat", json={"messages": [{"role": "admin", "content": "x"}]},
                       headers={"X-CSRF-Token": csrf}).status_code in (400, 503)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    result = client.post("/api/assistant/chat",
                         json={"messages": [{"role": "user", "content": "x"}]},
                         headers={"X-CSRF-Token": csrf})
    assert result.status_code == 503
