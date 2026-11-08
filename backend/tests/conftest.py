"""PostgreSQL fixtures: migrate the test database and isolate each test."""

import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

BACKEND_ROOT = Path(__file__).resolve().parents[1]

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
