"""Persistence operations for tool-call audit records."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ToolCall


class ToolCallRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        run_id: uuid.UUID,
        agent: str,
        tool: str,
        args_hash: str,
        duration_ms: int,
        status: str,
        cost: float = 0.0,
        error: str | None = None,
    ) -> ToolCall:
        record = ToolCall(
            run_id=run_id,
            agent=agent,
            tool=tool,
            args_hash=args_hash,
            duration_ms=duration_ms,
            status=status,
            cost=cost,
            error=error,
        )
        self._session.add(record)
        await self._session.flush()
        return record
