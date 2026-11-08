"""Tests for the Research agent, citations and search permissions."""

from collections.abc import AsyncIterator, Mapping

import pytest
import pytest_asyncio
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.agents.outputs import AudienceResearch, AudienceSegment, ResearchSource
from app.agents.prompts.loader import load_prompt
from app.agents.research import ResearchAgent
from app.core.config import Settings
from app.core.errors import GuardrailViolation, ToolError
from app.database.models import Base, Campaign, RunStatus, ToolCall, WorkflowRun
from app.database.repositories import CampaignRepository, RunRepository, ToolCallRepository
from app.harness.guardrails import RunGuardrails
from app.harness.middleware import ToolCallMiddleware
from app.harness.registry import ToolRegistry
from app.harness.tool_runner import ToolRunner
from app.llm.fake import FakeLLMClient
from app.tools.search_tools import FIXED_RESULTS, FakeSearchProvider, register_search_tools
from tests.harness.context_fixtures import make_state


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


def settings(*, attempts: int = 2, search_calls: int = 20) -> Settings:
    return Settings(
        deepseek_api_key="test-key",
        database_url="postgresql+asyncpg://user:pass@localhost:5432/marketpilot",
        redis_url="redis://localhost:6379/0",
        retry_max_attempts=attempts,
        max_search_calls_per_run=search_calls,
        _env_file=None,
    )


def research(*, url: str = str(FIXED_RESULTS[0].url)) -> AudienceResearch:
    return AudienceResearch(
        segments=[
            AudienceSegment(
                name="Busy professionals",
                description="Adults aged 25 to 40 with limited morning time",
            )
        ],
        pain_points=["Frizz returns by midday"],
        messaging_angles=["Low-effort confidence"],
        sources=[ResearchSource(title="Hair care market overview", url=url)],
    )


async def emit(name: str, data: Mapping[str, object]) -> None:
    return None


async def runner(session: AsyncSession, *, search_calls: int = 20) -> tuple[ToolRunner, object]:
    campaign = await CampaignRepository(session).create("Campaign")
    run = await RunRepository(session).create(campaign.id, RunStatus.RUNNING)
    registry = ToolRegistry()
    register_search_tools(registry, FakeSearchProvider())
    middleware = ToolCallMiddleware(
        registry=registry,
        guardrails=RunGuardrails(settings(search_calls=search_calls)),
        repository=ToolCallRepository(session),
    )

    async def call_tool(tool: str, args: BaseModel, *, step: str = "") -> object:
        return await middleware.call_tool(
            run_id=run.id,
            agent="research",
            step=step or "research",
            tool=tool,
            args=args,
        )

    return call_tool, run


async def test_valid_cited_output_passes_and_records_one_search(
    session: AsyncSession,
) -> None:
    call_tool, _ = await runner(session)
    expected = research()
    llm = FakeLLMClient([expected])

    result = await ResearchAgent(settings=settings()).run(make_state(), llm, emit, call_tool)

    assert result is expected
    assert str(FIXED_RESULTS[0].url) in llm.calls[0][1]["content"]
    rows = list(await session.scalars(select(ToolCall)))
    assert [(row.tool, row.status) for row in rows] == [("search_tools", "success")]


async def test_invented_url_retries_with_the_offending_url_in_feedback(
    session: AsyncSession,
) -> None:
    invented = "https://invented.example/study"
    call_tool, _ = await runner(session)
    llm = FakeLLMClient([research(url=invented), research()])
    events: list[str] = []

    async def collect(name: str, data: Mapping[str, object]) -> None:
        events.append(name)

    result = await ResearchAgent(settings=settings()).run(make_state(), llm, collect, call_tool)

    assert str(result.sources[0].url) == str(FIXED_RESULTS[0].url)
    assert events == ["validation_failed", "retrying"]
    feedback = llm.calls[1][-1]["content"]
    assert invented in feedback
    assert "not returned by the search tool" in feedback


async def test_search_call_cap_is_respected(session: AsyncSession) -> None:
    call_tool, _ = await runner(session, search_calls=0)
    llm = FakeLLMClient([research()])

    with pytest.raises(GuardrailViolation, match="search call cap of 0"):
        await ResearchAgent(settings=settings()).run(make_state(), llm, emit, call_tool)

    assert llm.calls == []


async def test_missing_tool_runner_is_a_tool_error() -> None:
    with pytest.raises(ToolError, match="requires the search tool"):
        await ResearchAgent(settings=settings()).run(
            make_state(), FakeLLMClient([research()]), emit, None
        )


def test_only_research_can_call_search() -> None:
    registry = ToolRegistry()
    register_search_tools(registry, FakeSearchProvider())

    assert registry.get_tool("research", "search_tools").name == "search_tools"
    for agent in ("brief", "copywriter", "designer", "compliance"):
        with pytest.raises(GuardrailViolation, match="not allowed"):
            registry.get_tool(agent, "search_tools")


def test_research_prompt_is_versioned() -> None:
    prompt = load_prompt("research")

    assert prompt.version == "1"
    assert "search tool" in prompt.text
