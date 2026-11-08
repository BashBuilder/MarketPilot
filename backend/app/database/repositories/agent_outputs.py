"""Persistence operations for append-only validated agent outputs."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AgentOutput


class AgentOutputRepository:
    """Insert-only access to one validated output per (run, agent)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        run_id: uuid.UUID,
        agent: str,
        output: dict[str, Any],
    ) -> AgentOutput:
        existing = await self.get(run_id, agent)
        if existing is not None:
            # A loop reruns the same node in one run; the schema allows one row.
            return existing
        row = AgentOutput(run_id=run_id, agent=agent, output=output)
        self._session.add(row)
        await self._session.flush()
        return row

    async def get(self, run_id: uuid.UUID, agent: str) -> AgentOutput | None:
        statement = select(AgentOutput).where(
            AgentOutput.run_id == run_id,
            AgentOutput.agent == agent,
        )
        return await self._session.scalar(statement)

    async def list_for_run(self, run_id: uuid.UUID) -> list[AgentOutput]:
        statement = (
            select(AgentOutput)
            .where(AgentOutput.run_id == run_id)
            .order_by(AgentOutput.created_at, AgentOutput.id)
        )
        result = await self._session.scalars(statement)
        return list(result)
