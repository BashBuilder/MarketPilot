"""Persistence operations for human approval decisions."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Approval, ApprovalDecision


class ApprovalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        run_id: uuid.UUID,
        campaign_version_id: uuid.UUID,
        decision: ApprovalDecision,
        comment: str | None = None,
        target_node: str | None = None,
    ) -> Approval:
        approval = Approval(
            run_id=run_id,
            campaign_version_id=campaign_version_id,
            decision=decision,
            comment=comment,
            target_node=target_node,
        )
        self._session.add(approval)
        await self._session.flush()
        return approval

    async def list_for_run(self, run_id: uuid.UUID) -> list[Approval]:
        statement = (
            select(Approval).where(Approval.run_id == run_id).order_by(Approval.created_at.asc())
        )
        result = await self._session.scalars(statement)
        return list(result)

    async def approved_for_version(
        self,
        campaign_version_id: uuid.UUID,
    ) -> Approval | None:
        statement = (
            select(Approval)
            .where(
                Approval.campaign_version_id == campaign_version_id,
                Approval.decision == ApprovalDecision.APPROVE,
            )
            .limit(1)
        )
        return await self._session.scalar(statement)
