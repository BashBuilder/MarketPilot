"""Per-run runtime construction plus checkpoint state loading."""

import uuid
from collections.abc import Mapping

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.database.models import Campaign, WorkflowRun
from app.database.repositories import CheckpointRepository, ToolCallRepository
from app.graph.node_runtime import NodeRuntime
from app.graph.state import WorkflowState
from app.harness.checkpoint_support import as_uuid, parse_state
from app.harness.checkpoints import resume_point
from app.harness.guardrails import RunGuardrails
from app.harness.middleware import ToolCallMiddleware
from app.harness.pipeline import PIPELINE_NODES
from app.harness.registry import ToolRegistry
from app.harness.tool_runner import ToolRunner
from app.harness.verification import EventCallback
from app.llm.base import LLMClient
from app.llm.deepseek import DeepSeekClient
from app.llm.embeddings import build_embedder
from app.tools.image_tools import FakeImageGenerator, register_image_tools
from app.tools.policy_tools import PolicySearcher, register_policy_tools
from app.tools.search_tools import FakeSearchProvider, register_search_tools


async def _noop(name: str, data: Mapping[str, object]) -> None:
    return None


NO_EVENTS: EventCallback = _noop


def build_runtime(
    run_id: uuid.UUID | str,
    session: AsyncSession,
    settings: Settings,
    *,
    llm: LLMClient | None = None,
    emit: EventCallback | None = None,
) -> NodeRuntime:
    """Build the default tools, guardrails and audit middleware for one run."""
    registry = ToolRegistry()
    register_search_tools(registry, FakeSearchProvider())
    register_image_tools(registry, FakeImageGenerator(settings.asset_dir))
    register_policy_tools(registry, PolicySearcher(session, embedder=build_embedder(settings)))
    middleware = ToolCallMiddleware(
        registry=registry,
        guardrails=RunGuardrails(settings),
        repository=ToolCallRepository(session),
    )
    resolved_id = as_uuid(run_id)

    def tools_for(agent: str) -> ToolRunner | None:
        async def call(tool: str, args: BaseModel, *, step: str = "") -> object:
            return await middleware.call_tool(
                run_id=resolved_id,
                agent=agent,
                step=step or agent,
                tool=tool,
                args=args,
            )

        return call

    return NodeRuntime(
        run_id=resolved_id,
        session=session,
        llm=llm or DeepSeekClient(settings),
        emit=emit or NO_EVENTS,
        tools_for=tools_for,
        settings=settings,
    )


async def current_state(session: AsyncSession, run: WorkflowRun) -> WorkflowState:
    """Load the newest checkpoint state, or a fresh state from the campaign idea."""
    checkpoint = await CheckpointRepository(session).latest_for_run(run.id)
    if checkpoint is not None:
        return parse_state(checkpoint.state)
    campaign = await session.get(Campaign, run.campaign_id)
    if campaign is None:
        raise LookupError(f"campaign {run.campaign_id} not found")
    return WorkflowState(idea=campaign.idea)


async def resume_state(
    session: AsyncSession,
    run: WorkflowRun,
) -> tuple[WorkflowState, str]:
    """Return the checkpoint state and the node a resumed run should start at."""
    checkpoint = await CheckpointRepository(session).latest_for_run(run.id)
    if checkpoint is None:
        return await current_state(session, run), PIPELINE_NODES[0]
    return parse_state(checkpoint.state), await resume_point(run.id, session=session)
