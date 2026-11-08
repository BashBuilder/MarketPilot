"""Shared API-test harness type."""

from dataclasses import dataclass

from fastapi import FastAPI

from app.core.config import Settings
from app.events.bus import InMemoryEventBus
from app.runs.launcher import RunLauncher


@dataclass
class Harness:
    app: FastAPI
    launcher: RunLauncher
    bus: InMemoryEventBus
    settings: Settings


def make_settings(**updates: object) -> Settings:
    """Build isolated API-test settings without reading a developer `.env`."""
    values: dict[str, object] = {
        "deepseek_api_key": "test-key",
        "database_url": "postgresql+asyncpg://user:pass@localhost:5432/marketpilot",
        "redis_url": "redis://localhost:6379/0",
        "frontend_origin": "http://localhost:3000,https://demo.example",
        "_env_file": None,
        **updates,
    }
    return Settings(**values)
