"""Tests for the Designer agent's image generation and revisions."""

from collections.abc import AsyncIterator, Mapping
from pathlib import Path

import pytest
import pytest_asyncio
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.agents.designer import DesignerAgent
from app.agents.outputs import AssetSet, ComplianceItem, ComplianceReport, GeneratedAsset
from app.core.config import Settings
from app.core.errors import GuardrailViolation
from app.database.models import Base, Campaign, RunStatus, ToolCall, WorkflowRun
from app.database.repositories import CampaignRepository, RunRepository, ToolCallRepository
from app.harness.guardrails import RunGuardrails
from app.harness.middleware import ToolCallMiddleware
from app.harness.registry import ToolRegistry
from app.harness.tool_runner import ToolRunner
from app.llm.fake import FakeLLMClient
from app.tools.image_tools import FakeImageGenerator, GeneratedImage, register_image_tools
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


def settings(*, asset_dir: Path, image_calls: int = 8) -> Settings:
    return Settings(
        deepseek_api_key="test-key",
        database_url="postgresql+asyncpg://user:pass@localhost:5432/marketpilot",
        redis_url="redis://localhost:6379/0",
        asset_dir=asset_dir,
        max_image_calls_per_run=image_calls,
        _env_file=None,
    )


async def runner(session: AsyncSession, asset_dir: Path, *, image_calls: int = 8) -> ToolRunner:
    campaign = await CampaignRepository(session).create("Campaign")
    run = await RunRepository(session).create(campaign.id, RunStatus.RUNNING)
    registry = ToolRegistry()
    register_image_tools(registry, FakeImageGenerator(asset_dir))
    middleware = ToolCallMiddleware(
        registry=registry,
        guardrails=RunGuardrails(settings(asset_dir=asset_dir, image_calls=image_calls)),
        repository=ToolCallRepository(session),
    )

    async def call_tool(tool: str, args: BaseModel, *, step: str = "") -> object:
        return await middleware.call_tool(
            run_id=run.id,
            agent="designer",
            step=step or "designer",
            tool=tool,
            args=args,
        )

    return call_tool


def as_asset(result: GeneratedImage) -> GeneratedAsset:
    return GeneratedAsset(
        uri=result.path,
        checksum=result.checksum,
        model=result.model,
        seed=result.seed,
        prompt=result.prompt,
    )


async def emit(name: str, data: Mapping[str, object]) -> None:
    return None


async def test_normal_run_generates_every_asset(session: AsyncSession, tmp_path: Path) -> None:
    call_tool = await runner(session, tmp_path)
    agent = DesignerAgent(settings=settings(asset_dir=tmp_path))

    result = await agent.run(make_state(), FakeLLMClient([]), emit, call_tool)

    assert len(result.assets) == 1
    asset = result.assets[0]
    assert Path(asset.uri).is_file()
    assert asset.model == "fake"
    rows = list(await session.scalars(select(ToolCall)))
    assert [(row.tool, row.status) for row in rows] == [("generate_image", "success")]


async def test_revision_edits_only_the_flagged_asset(session: AsyncSession, tmp_path: Path) -> None:
    generator = FakeImageGenerator(tmp_path)
    first = as_asset(await generator.generate("first image prompt", "", 1, (8, 8)))
    second = as_asset(await generator.generate("second image prompt", "", 2, (8, 8)))
    previous = AssetSet(assets=[first, second])
    state = make_state()
    state.assets = previous
    state.compliance = ComplianceReport(
        items=[
            ComplianceItem(
                check="Asset brand safety",
                passed=False,
                reason=f"asset {first.uri} shows a brand logo",
            )
        ]
    )
    call_tool = await runner(session, tmp_path)
    agent = DesignerAgent(settings=settings(asset_dir=tmp_path))

    result = await agent.run(state, FakeLLMClient([]), emit, call_tool)

    assert result.assets[0].uri != first.uri
    assert result.assets[1] == second
    rows = list(await session.scalars(select(ToolCall)))
    assert [(row.tool, row.status) for row in rows] == [("edit_image", "success")]


async def test_image_cap_raises_without_retry(session: AsyncSession, tmp_path: Path) -> None:
    call_tool = await runner(session, tmp_path, image_calls=0)
    agent = DesignerAgent(settings=settings(asset_dir=tmp_path, image_calls=0))
    events: list[str] = []

    async def collect(name: str, data: Mapping[str, object]) -> None:
        events.append(name)

    with pytest.raises(GuardrailViolation, match="image call cap of 0"):
        await agent.run(make_state(), FakeLLMClient([]), collect, call_tool)

    rows = list(await session.scalars(select(ToolCall)))
    assert [row.status for row in rows] == ["denied"]
    assert events == []


def test_image_tools_are_designer_only(tmp_path: Path) -> None:
    registry = ToolRegistry()
    register_image_tools(registry, FakeImageGenerator(tmp_path))

    assert registry.get_tool("designer", "generate_image").name == "generate_image"
    with pytest.raises(GuardrailViolation, match="not allowed"):
        registry.get_tool("brief", "generate_image")
    with pytest.raises(GuardrailViolation, match="not allowed"):
        registry.get_tool("research", "edit_image")
