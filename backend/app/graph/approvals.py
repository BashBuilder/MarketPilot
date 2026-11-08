"""Human approval and revision operations for a gated run."""

import uuid
from collections.abc import Mapping
from typing import Literal, TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.supervisor import route_revision
from app.core.config import Settings
from app.core.errors import RevisionCommentRequired, RunNotAwaitingApproval
from app.database.models import ApprovalDecision, RunStatus
from app.database.repositories import ApprovalRepository, CampaignRepository, RunRepository
from app.graph.execution import current_state
from app.graph.node_runtime import Agent
from app.graph.runner import continue_run
from app.graph.versioning import ensure_version, state_from_package
from app.harness.checkpoint_support import get_run, use_session
from app.harness.checkpoints import DONE, save_checkpoint
from app.harness.pipeline import PIPELINE_NODES
from app.harness.verification import EventCallback
from app.llm.base import LLMClient

SUPERVISOR_NODE = "supervisor"


class ApproveResult(TypedDict):
    status: Literal["completed"]
    version: int


class ReviseResult(TypedDict):
    run_id: str
    version: int


async def approve_run(
    run_id: uuid.UUID | str,
    comment: str | None = None,
    *,
    llm: LLMClient | None = None,
    agents: Mapping[str, Agent] | None = None,
    emit: EventCallback | None = None,
    session: AsyncSession | None = None,
    settings: Settings | None = None,
) -> ApproveResult:
    """Record an approval for a gated run and complete it."""
    async with use_session(session) as db:
        run = await get_run(db, run_id)
        _require_awaiting(run.id, run.status)
        state = await current_state(db, run)
        version = await ensure_version(db, run, state, None)
        await ApprovalRepository(db).create(
            run_id=run.id,
            campaign_version_id=version.id,
            decision=ApprovalDecision.APPROVE,
            comment=comment,
        )
        completed = await continue_run(
            run.id,
            ApprovalDecision.APPROVE,
            comment=comment,
            record_decision=False,
            llm=llm,
            agents=agents,
            emit=emit,
            session=db,
            settings=settings,
        )
        if completed.status != "completed":
            raise RuntimeError(f"run {run.id} did not complete after approval")
        return {"status": "completed", "version": version.version}


async def revise_run(
    run_id: uuid.UUID | str,
    comment: str | None,
    target_node: str | None = None,
    *,
    llm: LLMClient | None = None,
    agents: Mapping[str, Agent] | None = None,
    emit: EventCallback | None = None,
    session: AsyncSession | None = None,
    settings: Settings | None = None,
) -> ReviseResult:
    """Record a revision and continue it in a new run from the previous package."""
    feedback = comment.strip() if comment is not None else ""
    if not feedback:
        raise RevisionCommentRequired()

    async with use_session(session) as db:
        run = await get_run(db, run_id)
        _require_awaiting(run.id, run.status)
        state = await current_state(db, run)
        version = await ensure_version(db, run, state, None)
        target = target_node or route_revision(state).next_node
        if target not in PIPELINE_NODES:
            raise ValueError("a revision needs a target node or a scored package")

        campaign = await CampaignRepository(db).get(run.campaign_id)
        if campaign is None:
            raise LookupError(f"campaign {run.campaign_id} not found")

        await ApprovalRepository(db).create(
            run_id=run.id,
            campaign_version_id=version.id,
            decision=ApprovalDecision.REVISE,
            comment=feedback,
            target_node=target,
        )
        continuation = await RunRepository(db).create(run.campaign_id, RunStatus.RUNNING)
        revised_state = state_from_package(
            campaign.idea,
            version.package,
            target_node=target,
            revision_feedback=feedback,
        )
        await save_checkpoint(
            continuation.id,
            SUPERVISOR_NODE,
            revised_state,
            session=db,
        )
        await RunRepository(db).update_status(run, RunStatus.COMPLETED, current_node=DONE)

        completed = await continue_run(
            continuation.id,
            ApprovalDecision.REVISE,
            comment=feedback,
            target_node=target,
            record_decision=False,
            llm=llm,
            agents=agents,
            emit=emit,
            session=db,
            settings=settings,
        )
        latest = await ensure_version(db, continuation, completed, None)
        return {"run_id": str(continuation.id), "version": latest.version}


def _require_awaiting(run_id: uuid.UUID, status: RunStatus) -> None:
    if status is not RunStatus.AWAITING_APPROVAL:
        raise RunNotAwaitingApproval(str(run_id), status.value)
