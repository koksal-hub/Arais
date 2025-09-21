from __future__ import annotations

import os

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app


def test_health_endpoint_returns_ok(tmp_path, monkeypatch):
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "environment" in payload


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("APP_NAME", "Test Uygulama")
    monkeypatch.setenv("DEFAULT_LOCALE", "tr_TR")
    # clear cache
    get_settings.cache_clear()  # type: ignore[attr-defined]
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.app_name == "Test Uygulama"
    assert settings.default_locale == "tr_TR"


def test_utf8_content(tmp_path):
    text = "İzmir, Buca – Çeşme arasında hızlı test"
    file_path = tmp_path / "utf8.txt"
    file_path.write_text(text, encoding="utf-8")
    loaded = file_path.read_text(encoding="utf-8")
    assert loaded == text
