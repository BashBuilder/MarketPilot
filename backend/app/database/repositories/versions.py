"""Append-only persistence operations for campaign versions.

Repositories never update or delete versions; a revision creates a new row.
"""

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import CampaignVersion


class VersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def next_number(self, campaign_id: uuid.UUID) -> int:
        current = await self._session.scalar(
            select(func.max(CampaignVersion.version)).where(
                CampaignVersion.campaign_id == campaign_id
            )
        )
        return (current or 0) + 1

    async def create(
        self,
        campaign_id: uuid.UUID,
        package: dict[str, Any],
        *,
        parent_version_id: uuid.UUID | None = None,
        score: float | None = None,
    ) -> CampaignVersion:
        version = CampaignVersion(
            campaign_id=campaign_id,
            version=await self.next_number(campaign_id),
            parent_version_id=parent_version_id,
            package=package,
            score=score,
        )
        self._session.add(version)
        await self._session.flush()
        return version

    async def get(
        self,
        campaign_id: uuid.UUID,
        version: int,
    ) -> CampaignVersion | None:
        statement = select(CampaignVersion).where(
            CampaignVersion.campaign_id == campaign_id,
            CampaignVersion.version == version,
        )
        return await self._session.scalar(statement)

    async def get_by_id(self, version_id: uuid.UUID) -> CampaignVersion | None:
        return await self._session.get(CampaignVersion, version_id)

    async def list_for_campaign(
        self,
        campaign_id: uuid.UUID,
    ) -> list[CampaignVersion]:
        statement = (
            select(CampaignVersion)
            .where(CampaignVersion.campaign_id == campaign_id)
            .order_by(CampaignVersion.version.asc())
        )
        result = await self._session.scalars(statement)
        return list(result)

    async def latest(self, campaign_id: uuid.UUID) -> CampaignVersion | None:
        statement = (
            select(CampaignVersion)
            .where(CampaignVersion.campaign_id == campaign_id)
            .order_by(CampaignVersion.version.desc())
            .limit(1)
        )
        return await self._session.scalar(statement)
