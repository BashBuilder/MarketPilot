"""Tests for environment-backed application settings."""

from collections.abc import Iterator

import pytest

from app.core.config import Settings, SettingsError, get_settings

REQUIRED_ENV = {
    "DEEPSEEK_API_KEY": "test-key",
    "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/marketpilot",
    "REDIS_URL": "redis://localhost:6379/0",
}


@pytest.fixture(autouse=True)
def clear_settings_cache() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_settings_loads_required_values_and_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)

    settings = Settings(_env_file=None)

    assert settings.deepseek_api_key == "test-key"
    assert settings.database_url == REQUIRED_ENV["DATABASE_URL"]
    assert settings.redis_url == REQUIRED_ENV["REDIS_URL"]
    assert settings.deepseek_base_url == "https://api.deepseek.com"
    assert settings.image_provider == "fake"
    assert settings.cost_cap_per_run == 2.0
    assert settings.max_image_calls_per_run == 8
    assert settings.max_search_calls_per_run == 20
    assert settings.retry_max_attempts == 3
    assert settings.frontend_origins == [
        "http://localhost:3000",
        "https://marketpilot-demo-frontend.vercel.app",
    ]


def test_missing_required_values_fail_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in REQUIRED_ENV:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(SettingsError) as excinfo:
        Settings(_env_file=None)

    message = str(excinfo.value)
    assert "Missing required configuration" in message
    for name in REQUIRED_ENV:
        assert name in message


def test_invalid_image_provider_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("IMAGE_PROVIDER", "midjourney")

    with pytest.raises(SettingsError, match="Invalid configuration"):
        Settings(_env_file=None)


def test_frontend_origins_are_parsed(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("FRONTEND_ORIGIN", " https://a.example ,, https://b.example ")

    settings = Settings(_env_file=None)

    assert settings.frontend_origins == [
        "https://a.example",
        "https://b.example",
    ]


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)

    first = get_settings()
    second = get_settings()

    assert first is second
