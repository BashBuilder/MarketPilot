"""Persistence operations for append-only workflow checkpoints."""

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import WorkflowCheckpoint


class CheckpointRepository:
    """Insert-only access to workflow checkpoints."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        run_id: uuid.UUID,
        step: int,
        node: str,
        state: dict[str, Any],
    ) -> WorkflowCheckpoint:
        checkpoint = WorkflowCheckpoint(run_id=run_id, step=step, node=node, state=state)
        self._session.add(checkpoint)
        await self._session.flush()
        return checkpoint

    async def create_next(
        self,
        *,
        run_id: uuid.UUID,
        node: str,
        state: dict[str, Any],
    ) -> WorkflowCheckpoint:
        return await self.create(
            run_id=run_id,
            step=await self.next_step(run_id),
            node=node,
            state=state,
        )

    async def next_step(self, run_id: uuid.UUID) -> int:
        statement = select(func.coalesce(func.max(WorkflowCheckpoint.step), 0)).where(
            WorkflowCheckpoint.run_id == run_id
        )
        latest = await self._session.scalar(statement)
        return int(latest or 0) + 1

    async def latest_for_run(self, run_id: uuid.UUID) -> WorkflowCheckpoint | None:
        statement = (
            select(WorkflowCheckpoint)
            .where(WorkflowCheckpoint.run_id == run_id)
            .order_by(WorkflowCheckpoint.step.desc(), WorkflowCheckpoint.created_at.desc())
            .limit(1)
        )
        return await self._session.scalar(statement)

    async def latest_excluding(
        self,
        run_id: uuid.UUID,
        node: str,
    ) -> WorkflowCheckpoint | None:
        statement = (
            select(WorkflowCheckpoint)
            .where(
                WorkflowCheckpoint.run_id == run_id,
                WorkflowCheckpoint.node != node,
            )
            .order_by(WorkflowCheckpoint.step.desc(), WorkflowCheckpoint.created_at.desc())
            .limit(1)
        )
        return await self._session.scalar(statement)
