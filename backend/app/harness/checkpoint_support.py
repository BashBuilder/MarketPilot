"""Shared session and state helpers for checkpoint and gate primitives."""

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ValidationFailure
from app.database.models import Campaign, WorkflowRun
from app.database.repositories import CheckpointRepository, RunRepository
from app.database.session import session_scope
from app.graph.state import WorkflowState, WorkflowStatus


@asynccontextmanager
async def use_session(session: AsyncSession | None) -> AsyncIterator[AsyncSession]:
    """Yield the caller's session, or open and commit a scoped one."""
    if session is not None:
        yield session
        return
    async with session_scope() as scoped:
        yield scoped


async def get_run(session: AsyncSession, run_id: uuid.UUID | str) -> WorkflowRun:
    run = await RunRepository(session).get(as_uuid(run_id))
    if run is None:
        raise LookupError(f"run {run_id} not found")
    return run


async def state_for(
    session: AsyncSession,
    run: WorkflowRun,
    status: WorkflowStatus,
) -> WorkflowState:
    """Load the latest state, falling back to a fresh state for the campaign."""
    checkpoint = await CheckpointRepository(session).latest_for_run(run.id)
    if checkpoint is not None:
        state = parse_state(checkpoint.state)
    else:
        campaign = await session.get(Campaign, run.campaign_id)
        if campaign is None:
            raise LookupError(f"campaign {run.campaign_id} not found")
        state = WorkflowState(idea=campaign.idea)
    state.status = status
    return state


def as_uuid(run_id: uuid.UUID | str) -> uuid.UUID:
    return run_id if isinstance(run_id, uuid.UUID) else uuid.UUID(run_id)


def parse_state(raw: Any) -> WorkflowState:
    try:
        if isinstance(raw, str | bytes | bytearray):
            return WorkflowState.model_validate_json(raw)
        return WorkflowState.model_validate(raw)
    except ValidationError as error:
        raise ValidationFailure("checkpoint", str(error)) from error
