"""Tests for the audited tool-call middleware."""

import logging
from collections.abc import AsyncIterator, Awaitable, Callable

import pytest
import pytest_asyncio
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.errors import GuardrailViolation
from app.core.logging import agent as agent_context
from app.core.logging import run_id as run_id_context
from app.core.logging import step as step_context
from app.database.models import Base, Campaign, RunStatus, ToolCall, WorkflowRun
from app.database.repositories import CampaignRepository, RunRepository, ToolCallRepository
from app.harness.guardrails import RunGuardrails
from app.harness.middleware import ToolCallMiddleware
from app.harness.registry import ToolRegistry, ToolSpec


class SearchArgs(BaseModel):
    query: str


ToolHandler = Callable[[SearchArgs], Awaitable[str]]


async def search(args: SearchArgs) -> str:
    return args.query


async def failing_search(args: SearchArgs) -> str:
    raise RuntimeError("search exploded")


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


def make_middleware(
    session: AsyncSession,
    *,
    handler: ToolHandler = search,
    logger: logging.Logger | None = None,
    search_calls: int = 20,
) -> ToolCallMiddleware:
    registry = ToolRegistry()
    registry.register_tool(
        ToolSpec(
            name="search_tools",
            args_model=SearchArgs,
            handler=handler,
            side_effecting=False,
        )
    )
    return ToolCallMiddleware(
        registry=registry,
        guardrails=RunGuardrails(settings(search_calls=search_calls)),
        repository=ToolCallRepository(session),
        logger=logger,
    )


async def make_run(session: AsyncSession) -> WorkflowRun:
    campaign = await CampaignRepository(session).create("Campaign")
    return await RunRepository(session).create(campaign.id, RunStatus.RUNNING)


async def test_successful_call_writes_one_row(session: AsyncSession) -> None:
    run = await make_run(session)
    middleware = make_middleware(session)

    result = await middleware.call_tool(
        run_id=run.id,
        agent="research",
        step="research-1",
        tool="search_tools",
        args={"query": "hair care"},
        cost=0.25,
    )

    rows = list(await session.scalars(select(ToolCall)))
    assert result == "hair care"
    assert len(rows) == 1
    row = rows[0]
    assert row.run_id == run.id
    assert row.agent == "research"
    assert row.tool == "search_tools"
    assert len(row.args_hash) == 64
    assert row.duration_ms >= 0
    assert row.cost == 0.25
    assert row.status == "success"
    assert row.error is None


async def test_denied_call_writes_denied_row(session: AsyncSession) -> None:
    run = await make_run(session)
    middleware = make_middleware(session)

    with pytest.raises(GuardrailViolation, match="not allowed"):
        await middleware.call_tool(
            run_id=run.id,
            agent="brief",
            step="brief-1",
            tool="search_tools",
            args={"query": "hair care"},
        )

    row = (await session.scalars(select(ToolCall))).one()
    assert row.status == "denied"
    assert row.cost == 0.0
    assert row.error is not None and "not allowed" in row.error


async def test_guardrail_denial_writes_denied_row(session: AsyncSession) -> None:
    run = await make_run(session)
    middleware = make_middleware(session, search_calls=0)

    with pytest.raises(GuardrailViolation, match="search call cap"):
        await middleware.call_tool(
            run_id=run.id,
            agent="research",
            step="research-1",
            tool="search_tools",
            args={"query": "hair care"},
        )

    row = (await session.scalars(select(ToolCall))).one()
    assert row.status == "denied"
    assert row.error is not None and "call cap" in row.error


async def test_failing_call_writes_failed_row_and_reraises(
    session: AsyncSession,
) -> None:
    run = await make_run(session)
    middleware = make_middleware(session, handler=failing_search)

    with pytest.raises(RuntimeError, match="search exploded"):
        await middleware.call_tool(
            run_id=run.id,
            agent="research",
            step="research-1",
            tool="search_tools",
            args={"query": "hair care"},
        )

    row = (await session.scalars(select(ToolCall))).one()
    assert row.status == "error"
    assert row.error == "search exploded"


class CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.contexts: list[tuple[str, str | None, str | None, str | None]] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.contexts.append(
            (
                record.getMessage(),
                run_id_context.get(),
                agent_context.get(),
                step_context.get(),
            )
        )


async def test_tool_logs_include_run_agent_and_step(session: AsyncSession) -> None:
    run = await make_run(session)
    logger = logging.getLogger("tests.harness.middleware")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    capture = CaptureHandler()
    logger.addHandler(capture)
    try:
        middleware = make_middleware(session, logger=logger)
        await middleware.call_tool(
            run_id=run.id,
            agent="research",
            step="research-1",
            tool="search_tools",
            args={"query": "hair care"},
        )
    finally:
        logger.removeHandler(capture)

    assert capture.contexts == [
        ("tool call succeeded: search_tools", str(run.id), "research", "research-1")
    ]
