"""API fixtures: real app with a test-database session and a recording launcher."""

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_session
from app.events.bus import InMemoryEventBus
from app.main import create_app
from app.runs.launcher import RecordingLauncher
from tests.api.helpers import Harness, make_settings


@pytest_asyncio.fixture
async def harness(db_session: AsyncSession) -> AsyncIterator[Harness]:
    settings = make_settings()
    launcher = RecordingLauncher()
    bus = InMemoryEventBus()
    app = create_app(settings=settings, launcher=launcher, bus=bus)

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_app_settings] = lambda: settings
    yield Harness(app=app, launcher=launcher, bus=bus, settings=settings)
    app.dependency_overrides.clear()
    await bus.close()


@pytest_asyncio.fixture
async def client(harness: Harness) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=harness.app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
