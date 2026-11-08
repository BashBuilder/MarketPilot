"""Small reusable helpers for workflow integration tests."""

from collections.abc import Mapping

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import RunStatus, WorkflowCheckpoint, WorkflowRun
from app.database.repositories import CampaignRepository, RunRepository
from app.harness.verification import EventCallback

Events = list[tuple[str, Mapping[str, object]]]


async def start_run(
    session: AsyncSession,
    idea: str = "Create a hair-care campaign for adults aged 25 to 40",
) -> WorkflowRun:
    campaign = await CampaignRepository(session).create(idea)
    return await RunRepository(session).create(campaign.id, RunStatus.RUNNING)


def collector() -> tuple[Events, EventCallback]:
    events: Events = []

    async def emit(name: str, data: Mapping[str, object]) -> None:
        events.append((name, data))

    return events, emit


def started_agents(events: Events) -> list[str]:
    return [str(data["agent"]) for name, data in events if name == "agent_started"]


async def checkpoint_nodes(session: AsyncSession, run_id: object) -> list[str]:
    rows = await session.scalars(
        select(WorkflowCheckpoint)
        .where(WorkflowCheckpoint.run_id == run_id)
        .order_by(WorkflowCheckpoint.step)
    )
    return [row.node for row in rows]
