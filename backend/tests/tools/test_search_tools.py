"""Tests for the fake search tool, provenance and per-run caps."""

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.errors import GuardrailViolation
from app.database.models import Base, Campaign, RunStatus, ToolCall, WorkflowRun
from app.database.repositories import CampaignRepository, RunRepository, ToolCallRepository
from app.harness.guardrails import RunGuardrails
from app.harness.middleware import ToolCallMiddleware
from app.harness.registry import ToolRegistry
from app.tools.search_tools import (
    FakeSearchProvider,
    SearchArgs,
    register_search_tools,
    search_tools,
)


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    tables = [Campaign.__table__, WorkflowRun.__table__, ToolCall.__table__]
    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_connection: Base.metadata.create_all(sync_connection, tables=tables)
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db_session:
        yield db_session
    await engine.dispose()


def settings(*, search_calls: int = 20) -> Settings:
    return Settings(
        deepseek_api_key="test-key",
        database_url="postgresql+asyncpg://user:pass@localhost:5432/marketpilot",
        redis_url="redis://localhost:6379/0",
        max_search_calls_per_run=search_calls,
        _env_file=None,
    )


def middleware(session: AsyncSession, *, search_calls: int = 20) -> ToolCallMiddleware:
    registry = ToolRegistry()
    register_search_tools(registry)
    return ToolCallMiddleware(
        registry=registry,
        guardrails=RunGuardrails(settings(search_calls=search_calls)),
        repository=ToolCallRepository(session),
    )


async def test_search_returns_cited_results_in_a_stable_shape() -> None:
    results = await search_tools(SearchArgs(query="hair care", max_results=2))

    assert len(results) == 2
    for result in results:
        assert result.title
        assert result.snippet
        assert result.url.startswith(("http://", "https://"))


async def test_fake_provider_is_deterministic() -> None:
    provider = FakeSearchProvider()

    first = await provider.search("hair care", max_results=5)
    second = await provider.search("different query", max_results=5)

    assert first == second


def test_search_args_reject_empty_queries() -> None:
    with pytest.raises(ValidationError):
        SearchArgs(query="")


def test_search_is_registered_for_research_only() -> None:
    registry = ToolRegistry()
    register_search_tools(registry)

    assert registry.get_tool("research", "search_tools").name == "search_tools"
    with pytest.raises(GuardrailViolation, match="not allowed"):
        registry.get_tool("designer", "search_tools")
    with pytest.raises(GuardrailViolation, match="not allowed"):
        registry.get_tool("brief", "search_tools")


async def test_search_cap_is_enforced_through_the_middleware(
    session: AsyncSession,
) -> None:
    campaign = await CampaignRepository(session).create("Campaign")
    run = await RunRepository(session).create(campaign.id, RunStatus.RUNNING)
    tools = middleware(session, search_calls=1)

    first = await tools.call_tool(
        run_id=run.id,
        agent="research",
        step="research-1",
        tool="search_tools",
        args={"query": "hair care"},
    )

    with pytest.raises(GuardrailViolation, match="search call cap of 1"):
        await tools.call_tool(
            run_id=run.id,
            agent="research",
            step="research-2",
            tool="search_tools",
            args={"query": "hair care"},
        )

    rows = list(await session.scalars(select(ToolCall)))
    assert len(first) == 3
    assert [row.status for row in rows] == ["success", "denied"]
