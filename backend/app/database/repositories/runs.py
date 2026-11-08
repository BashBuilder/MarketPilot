"""Persistence operations for workflow runs."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import RunStatus, WorkflowRun


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        campaign_id: uuid.UUID,
        status: RunStatus = RunStatus.PENDING,
    ) -> WorkflowRun:
        run = WorkflowRun(campaign_id=campaign_id, status=status)
        self._session.add(run)
        await self._session.flush()
        return run

    async def get(self, run_id: uuid.UUID) -> WorkflowRun | None:
        return await self._session.get(WorkflowRun, run_id)

    async def list_for_campaign(self, campaign_id: uuid.UUID) -> list[WorkflowRun]:
        statement = (
            select(WorkflowRun)
            .where(WorkflowRun.campaign_id == campaign_id)
            .order_by(WorkflowRun.created_at.desc(), WorkflowRun.id.desc())
        )
        result = await self._session.scalars(statement)
        return list(result)

    async def update_status(
        self,
        run: WorkflowRun,
        status: RunStatus,
        *,
        current_node: str | None = None,
        error: str | None = None,
    ) -> WorkflowRun:
        run.status = status
        run.current_node = current_node
        run.error = error
        await self._session.flush()
        return run
