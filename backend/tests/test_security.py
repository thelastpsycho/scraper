"""Verify the API fails closed and protects writes."""
import pytest

from app import create_app


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_PIN", "123456")
    monkeypatch.setenv("APP_SESSION_SECRET", "b" * 48)
    monkeypatch.delenv("ALLOW_INSECURE_LOCAL_DEV", raising=False)
    monkeypatch.setenv("APP_HOST", "127.0.0.1")
    application = create_app()
    application.testing = True
    return application


def sign_in(client):
    result = client.post("/api/auth/login", json={"pin": "123456"})
    assert result.status_code == 200
    return result.get_json()["csrf_token"]


def test_api_locked_when_unconfigured(monkeypatch):
    for name in ("APP_ACCESS_PIN", "APP_SESSION_SECRET", "ALLOW_INSECURE_LOCAL_DEV"):
        monkeypatch.delenv(name, raising=False)
    application = create_app()
    application.testing = True
    client = application.test_client()
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/pipeline/status").status_code == 503
    assert client.post("/api/auth/login", json={"pin": "anything"}).status_code == 503


def test_login_csrf_logout_and_protected_get(app):
    client = app.test_client()
    assert client.get("/api/pipeline/status").status_code == 401
    assert client.post("/api/auth/login", json={"pin": "000000"}).status_code == 401
    csrf = sign_in(client)
    assert client.get("/api/pipeline/status").status_code == 200
    assert client.post("/api/auth/logout").status_code == 403
    response = client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
    assert response.status_code == 200
    assert client.get("/api/pipeline/status").status_code == 401


def test_non_six_digit_pin_rejected(monkeypatch):
    monkeypatch.setenv("APP_ACCESS_PIN", "12345")
    monkeypatch.setenv("APP_SESSION_SECRET", "b" * 48)
    monkeypatch.delenv("ALLOW_INSECURE_LOCAL_DEV", raising=False)
    with pytest.raises(RuntimeError):
        create_app()


def test_unsafe_dev_requires_explicit_local_flag(monkeypatch):
    monkeypatch.delenv("APP_ACCESS_PIN", raising=False)
    monkeypatch.delenv("APP_SESSION_SECRET", raising=False)
    monkeypatch.setenv("ALLOW_INSECURE_LOCAL_DEV", "1")
    monkeypatch.setenv("APP_HOST", "0.0.0.0")
    remote = create_app().test_client()
    assert remote.get("/api/pipeline/status").status_code == 503
    monkeypatch.setenv("APP_HOST", "127.0.0.1")
    local = create_app().test_client()
    assert local.get("/api/pipeline/status").status_code == 200
