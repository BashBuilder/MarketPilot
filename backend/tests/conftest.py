"""PostgreSQL fixtures: migrate the test database and isolate each test."""

import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.api.helpers import Harness, make_settings

BACKEND_ROOT = Path(__file__).resolve().parents[1]

# Keep imports of the configured application working without a developer `.env`.
os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://user:pass@localhost:5432/marketpilot",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

TABLES = (
    "agent_outputs",
    "approvals",
    "assets",
    "campaign_versions",
    "campaigns",
    "compliance_reports",
    "creative_scores",
    "policy_documents",
    "tool_calls",
    "workflow_checkpoints",
    "workflow_runs",
)


@pytest.fixture(scope="session")
def test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set; skipping PostgreSQL tests")
    return url


@pytest.fixture(scope="session")
def migrated_database(test_database_url: str) -> str:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", test_database_url)
    command.upgrade(config, "head")
    return test_database_url


@pytest_asyncio.fixture
async def db_factory(
    migrated_database: str,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Provide independent sessions for background tasks, sharing one clean DB."""
    engine = create_async_engine(migrated_database, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))
        await session.commit()
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(migrated_database: str) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(migrated_database, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))
        await session.commit()
        try:
            yield session
        finally:
            await session.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def fake_harness(
    db_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> AsyncIterator[Harness]:
    """Fake-mode app with the real launcher and independent background sessions."""
    from app.api.deps import get_app_settings, get_session
    from app.events.bus import InMemoryEventBus
    from app.main import create_app
    from app.runs.launcher import WorkflowRunLauncher

    settings = make_settings(app_mode="fake", asset_dir=tmp_path / "assets")
    bus = InMemoryEventBus()
    launcher = WorkflowRunLauncher(settings, bus, session_factory=db_factory)
    app = create_app(settings=settings, launcher=launcher, bus=bus)

    async def override_session() -> AsyncIterator[AsyncSession]:
        session = db_factory()
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise
        finally:
            await session.close()

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_app_settings] = lambda: settings
    yield Harness(app=app, launcher=launcher, bus=bus, settings=settings)
    await launcher.shutdown()
    app.dependency_overrides.clear()
    await bus.close()


@pytest_asyncio.fixture
async def fake_client(fake_harness: Harness) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=fake_harness.app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=30) as http:
        yield http
