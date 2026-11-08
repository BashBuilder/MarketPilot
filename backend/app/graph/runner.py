"""Run, resume and continue a workflow run through the compiled graph."""

import uuid
from collections.abc import Mapping

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.supervisor import route_revision
from app.core.config import Settings, get_settings
from app.database.models import ApprovalDecision, RunStatus
from app.database.repositories import VersionRepository
from app.graph.execution import build_runtime, current_state, resume_state
from app.graph.node_runtime import Agent, NodeRuntime, event_data
from app.graph.routing import LINEAR_NODES
from app.graph.state import WorkflowState
from app.harness.checkpoint_support import get_run, use_session
from app.harness.checkpoints import DONE, save_checkpoint, submit_decision
from app.harness.verification import EventCallback
from app.llm.base import LLMClient


async def run_pipeline(
    state: WorkflowState,
    runtime: NodeRuntime,
    agents: Mapping[str, Agent] | None = None,
) -> WorkflowState:
    """Run the compiled graph from the state's target node."""
    from app.graph.workflow import build_workflow

    result = await build_workflow(runtime, agents).ainvoke(state)
    return result if isinstance(result, WorkflowState) else WorkflowState.model_validate(result)


async def run_workflow(
    run_id: uuid.UUID | str,
    *,
    llm: LLMClient | None = None,
    agents: Mapping[str, Agent] | None = None,
    emit: EventCallback | None = None,
    session: AsyncSession | None = None,
    settings: Settings | None = None,
) -> WorkflowState:
    """Resume an unfinished run from its last checkpoint, or start at brief."""
    from app.graph.workflow import build_agents

    resolved = settings or get_settings()
    async with use_session(session) as db:
        run = await get_run(db, run_id)
        if run.status is RunStatus.COMPLETED:
            return (await current_state(db, run)).model_copy(update={"status": "completed"})
        if run.status is RunStatus.AWAITING_APPROVAL:
            return (await current_state(db, run)).model_copy(update={"status": "awaiting_approval"})
        state, start = await resume_state(db, run)
        if start == DONE:
            return state.model_copy(update={"status": "completed"})
        runtime = build_runtime(run.id, db, resolved, llm=llm, emit=emit)
        initial = state.model_copy(update={"status": "running", "target_node": start})
        return await run_pipeline(initial, runtime, agents or build_agents(resolved))


async def continue_run(
    run_id: uuid.UUID | str,
    decision: ApprovalDecision | str,
    *,
    comment: str | None = None,
    target_node: str | None = None,
    llm: LLMClient | None = None,
    agents: Mapping[str, Agent] | None = None,
    emit: EventCallback | None = None,
    session: AsyncSession | None = None,
    settings: Settings | None = None,
) -> WorkflowState:
    """Approve a gated run, or revise from the target/weakest node onward."""
    from app.graph.workflow import build_agents

    resolved = settings or get_settings()
    async with use_session(session) as db:
        run = await get_run(db, run_id)
        state = await current_state(db, run)
        if run.status is RunStatus.COMPLETED:
            return state.model_copy(update={"status": "completed"})

        choice = ApprovalDecision(decision)
        target = target_node
        if choice is ApprovalDecision.REVISE and target is None:
            routed = route_revision(state).next_node
            target = routed if routed in LINEAR_NODES else None

        runtime = build_runtime(run.id, db, resolved, llm=llm, emit=emit)
        continuation = await submit_decision(run.id, choice, comment, target, session=db)
        if choice is ApprovalDecision.APPROVE:
            completed = state.model_copy(update={"status": "completed"})
            await save_checkpoint(run.id, DONE, completed, session=db)
            version = await VersionRepository(db).latest(run.campaign_id)
            await runtime.emit(
                "completed",
                event_data(
                    runtime,
                    "human",
                    {
                        "version": version.version if version is not None else None,
                        "score": state.score.total if state.score is not None else None,
                    },
                ),
            )
            return completed
        if continuation not in LINEAR_NODES:
            return state.model_copy(update={"status": "awaiting_approval"})
        revised = state.model_copy(
            update={"status": "running", "target_node": continuation, "score": None}
        )
        return await run_pipeline(revised, runtime, agents or build_agents(resolved))
