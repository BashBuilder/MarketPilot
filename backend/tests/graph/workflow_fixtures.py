"""Offline wiring fixtures for workflow integration tests."""

import uuid
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel

from app.core.config import Settings
from app.harness.middleware import ToolCallMiddleware
from app.harness.tool_runner import ToolRunner
from app.tools.image_tools import FakeImageGenerator, GeneratedImage
from app.tools.policy_tools import PolicyMatch
from tests.graph.workflow_outputs import NEGATIVE, PROMPT

ToolResolver = Callable[[str], ToolRunner | None]


class FakePolicySearcher:
    async def search(self, query: str, top_k: int) -> list[PolicyMatch]:
        return [
            PolicyMatch(
                id=uuid.uuid4(),
                title="Health and beauty claims",
                source="internal://policies/health-beauty-claims",
                content="Do not promise medical outcomes for cosmetic products.",
                distance=0.0,
            )
        ]


def settings(
    asset_dir: Path,
    *,
    retry_attempts: int = 3,
    max_loops: int = 2,
) -> Settings:
    return Settings(
        deepseek_api_key="test-key",
        database_url="postgresql+asyncpg://user:pass@localhost:5432/marketpilot",
        redis_url="redis://localhost:6379/0",
        asset_dir=asset_dir,
        retry_max_attempts=retry_attempts,
        max_auto_loops=max_loops,
        _env_file=None,
    )


def tools_for(run_id: uuid.UUID, middleware: ToolCallMiddleware) -> ToolResolver:
    def resolve(agent: str) -> ToolRunner | None:
        if agent not in {"research", "designer", "compliance"}:
            return None

        async def call(tool: str, args: BaseModel, *, step: str = "") -> object:
            return await middleware.call_tool(
                run_id=run_id,
                agent=agent,
                step=step or agent,
                tool=tool,
                args=args,
            )

        return call

    return resolve


async def generated_asset(asset_dir: Path) -> GeneratedImage:
    return await FakeImageGenerator(asset_dir).generate(PROMPT, NEGATIVE, 0, (64, 64))
