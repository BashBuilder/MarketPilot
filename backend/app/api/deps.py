"""Request-scoped dependencies: one session, settings, launcher and bus."""

from collections.abc import AsyncIterator
from typing import cast

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.database.session import session_scope
from app.events.bus import EventBus
from app.runs.launcher import RunLauncher


async def get_session() -> AsyncIterator[AsyncSession]:
    """Open one session per request, committing on success."""
    async with session_scope() as session:
        yield session


def get_app_settings() -> Settings:
    """Return the process settings; tests override this dependency."""
    return get_settings()


def get_launcher(request: Request) -> RunLauncher:
    """Return the launcher installed on the application."""
    return cast(RunLauncher, request.app.state.launcher)


def get_event_bus(request: Request) -> EventBus:
    """Return the event bus installed on the application."""
    return cast(EventBus, request.app.state.event_bus)
