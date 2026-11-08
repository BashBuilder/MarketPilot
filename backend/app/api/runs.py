"""Human approval and revision endpoints for a gated run."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_event_bus, get_launcher, get_session
from app.api.schemas import ApproveRequest, ApproveResponse, ReviseRequest, ReviseResponse
from app.core.config import Settings
from app.core.errors import InvalidRequest, RevisionCommentRequired, RunNotFound
from app.database.repositories import RunRepository
from app.events.bus import EventBus
from app.events.emitter import bus_emitter
from app.graph.approvals import approve_run, revise_run
from app.runs.launcher import RunLauncher

router = APIRouter(tags=["runs"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
LauncherDep = Annotated[RunLauncher, Depends(get_launcher)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]
BusDep = Annotated[EventBus, Depends(get_event_bus)]


@router.post("/runs/{run_id}/approve", response_model=ApproveResponse)
async def approve(
    run_id: uuid.UUID,
    payload: ApproveRequest,
    session: SessionDep,
    settings: SettingsDep,
    bus: BusDep,
) -> ApproveResponse:
    """Approve the version under review and complete the run."""
    await _require_run(session, run_id)
    _check_length(payload.comment, settings.max_comment_length)
    result = await approve_run(
        run_id,
        payload.comment,
        emit=bus_emitter(bus, run_id),
        session=session,
        settings=settings,
    )
    return ApproveResponse(status=result["status"], version=result["version"])


@router.post("/runs/{run_id}/revise", response_model=ReviseResponse)
async def revise(
    run_id: uuid.UUID,
    payload: ReviseRequest,
    session: SessionDep,
    launcher: LauncherDep,
    settings: SettingsDep,
) -> ReviseResponse:
    """Record a revision and start the continuation run."""
    await _require_run(session, run_id)
    comment = payload.comment.strip()
    if not comment:
        raise RevisionCommentRequired()
    _check_length(comment, settings.max_comment_length)
    result = await revise_run(
        run_id,
        comment,
        payload.target_node,
        session=session,
        settings=settings,
    )
    await launcher.start(result["run_id"])
    return ReviseResponse(run_id=uuid.UUID(result["run_id"]), version=result["version"])


async def _require_run(session: AsyncSession, run_id: uuid.UUID) -> None:
    if await RunRepository(session).get(run_id) is None:
        raise RunNotFound(run_id)


def _check_length(comment: str | None, limit: int) -> None:
    if comment is not None and len(comment) > limit:
        raise InvalidRequest(
            f"comment must be at most {limit} characters",
            field="comment",
        )
