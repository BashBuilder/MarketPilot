"""Durable checkpoints plus framework-independent human-gate primitives."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ApprovalDecision, RunStatus, WorkflowCheckpoint
from app.database.repositories import (
    ApprovalRepository,
    CheckpointRepository,
    RunRepository,
)
from app.graph.state import WorkflowState
from app.harness.checkpoint_support import (
    as_uuid,
    get_run,
    parse_state,
    state_for,
    use_session,
)
from app.harness.gate import ensure_version, next_after_last_agent
from app.harness.pipeline import DONE, HUMAN_GATE, PIPELINE_NODES, next_node

__all__ = [
    "DONE",
    "HUMAN_GATE",
    "PIPELINE_NODES",
    "load_latest_checkpoint",
    "request_approval",
    "resume_point",
    "save_checkpoint",
    "submit_decision",
]


async def save_checkpoint(
    run_id: uuid.UUID | str,
    node_name: str,
    state: WorkflowState,
    *,
    session: AsyncSession | None = None,
) -> WorkflowCheckpoint:
    """Append one validated checkpoint row for ``run_id`` and return it."""
    async with use_session(session) as db:
        return await CheckpointRepository(db).create_next(
            run_id=as_uuid(run_id),
            node=node_name,
            state=state.model_dump(mode="json"),
        )


async def load_latest_checkpoint(
    run_id: uuid.UUID | str,
    *,
    session: AsyncSession | None = None,
) -> WorkflowState | None:
    """Load and re-validate the newest checkpoint, or ``None`` when absent."""
    async with use_session(session) as db:
        checkpoint = await CheckpointRepository(db).latest_for_run(as_uuid(run_id))
    return parse_state(checkpoint.state) if checkpoint is not None else None


async def resume_point(
    run_id: uuid.UUID | str,
    *,
    session: AsyncSession | None = None,
) -> str:
    """Return the next pipeline node after the latest checkpoint and decision."""
    async with use_session(session) as db:
        checkpoint = await CheckpointRepository(db).latest_for_run(as_uuid(run_id))
        if checkpoint is None:
            return PIPELINE_NODES[0]
        state = parse_state(checkpoint.state)
        if state.status == "escalated":
            return HUMAN_GATE
        if checkpoint.node != HUMAN_GATE:
            if checkpoint.node == "supervisor" and state.target_node in PIPELINE_NODES:
                return state.target_node
            return next_node(checkpoint.node)
        approvals = await ApprovalRepository(db).list_for_run(checkpoint.run_id)
        if not approvals:
            return DONE
        decision = approvals[-1]
        if decision.decision is ApprovalDecision.APPROVE:
            return DONE
        return decision.target_node or await next_after_last_agent(db, checkpoint.run_id)


async def request_approval(
    run_id: uuid.UUID | str,
    *,
    session: AsyncSession | None = None,
) -> WorkflowCheckpoint:
    """Set the run to awaiting approval and append a human-gate checkpoint."""
    async with use_session(session) as db:
        run = await get_run(db, run_id)
        state = await state_for(db, run, "awaiting_approval")
        await RunRepository(db).update_status(
            run,
            RunStatus.AWAITING_APPROVAL,
            current_node=HUMAN_GATE,
        )
        return await CheckpointRepository(db).create_next(
            run_id=run.id,
            node=HUMAN_GATE,
            state=state.model_dump(mode="json"),
        )


async def submit_decision(
    run_id: uuid.UUID | str,
    decision: ApprovalDecision | str,
    comment: str | None = None,
    target_node: str | None = None,
    *,
    campaign_version_id: uuid.UUID | None = None,
    session: AsyncSession | None = None,
) -> str:
    """Record an approve/revise decision and return the node to continue from."""
    if target_node is not None and target_node not in PIPELINE_NODES:
        raise ValueError(f"unknown target node: {target_node}")
    decision_value = ApprovalDecision(decision)

    async with use_session(session) as db:
        run = await get_run(db, run_id)
        state = await state_for(db, run, "awaiting_approval")
        version = await ensure_version(db, run, state, campaign_version_id)
        await ApprovalRepository(db).create(
            run_id=run.id,
            campaign_version_id=version.id,
            decision=decision_value,
            comment=comment,
            target_node=target_node,
        )
        if decision_value is ApprovalDecision.APPROVE:
            await RunRepository(db).update_status(run, RunStatus.COMPLETED, current_node=DONE)
            return DONE
        continuation = target_node or await next_after_last_agent(db, run.id)
        await RunRepository(db).update_status(run, RunStatus.RUNNING, current_node=continuation)
        return continuation
