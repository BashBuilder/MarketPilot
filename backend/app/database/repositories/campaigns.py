"""Persistence operations for campaigns."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Campaign, CampaignStatus


class CampaignRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        idea: str,
        status: CampaignStatus = CampaignStatus.DRAFT,
    ) -> Campaign:
        campaign = Campaign(idea=idea, status=status)
        self._session.add(campaign)
        await self._session.flush()
        return campaign

    async def get(self, campaign_id: uuid.UUID) -> Campaign | None:
        return await self._session.get(Campaign, campaign_id)

    async def list(self, limit: int = 100) -> list[Campaign]:
        statement = (
            select(Campaign).order_by(Campaign.created_at.desc(), Campaign.id.desc()).limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)

    async def update_status(
        self,
        campaign: Campaign,
        status: CampaignStatus,
    ) -> Campaign:
        campaign.status = status
        await self._session.flush()
        return campaign
