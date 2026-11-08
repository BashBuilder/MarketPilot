"""Version history, full package and diff endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.api.schemas import CampaignPackage, DiffResponse, VersionSummary
from app.core.errors import CampaignNotFound, VersionNotFound
from app.database.repositories import CampaignRepository, VersionRepository
from app.graph.diff import load_diff

router = APIRouter(tags=["versions"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/campaigns/{campaign_id}/versions", response_model=list[VersionSummary])
async def list_versions(
    campaign_id: uuid.UUID,
    session: SessionDep,
) -> list[VersionSummary]:
    """Return version summaries oldest first."""
    await _require_campaign(session, campaign_id)
    versions = await VersionRepository(session).list_for_campaign(campaign_id)
    return [
        VersionSummary(
            version=version.version,
            parent_version_id=version.parent_version_id,
            score=version.score,
            created_at=version.created_at,
        )
        for version in versions
    ]


@router.get(
    "/campaigns/{campaign_id}/versions/{version}",
    response_model=CampaignPackage,
    response_model_exclude_none=True,
)
async def get_version(
    campaign_id: uuid.UUID,
    version: int,
    session: SessionDep,
) -> CampaignPackage:
    """Return the immutable package for one version."""
    await _require_campaign(session, campaign_id)
    stored = await VersionRepository(session).get(campaign_id, version)
    if stored is None:
        raise VersionNotFound(str(campaign_id), version)
    return CampaignPackage.model_validate(stored.package)


@router.get(
    "/campaigns/{campaign_id}/versions/{from_version}/diff/{to_version}",
    response_model=DiffResponse,
)
async def diff_versions(
    campaign_id: uuid.UUID,
    from_version: int,
    to_version: int,
    session: SessionDep,
) -> DiffResponse:
    """Return dotted-path changes between two versions."""
    await _require_campaign(session, campaign_id)
    payload = await load_diff(session, campaign_id, from_version, to_version)
    return DiffResponse.model_validate(payload)


async def _require_campaign(session: AsyncSession, campaign_id: uuid.UUID) -> None:
    if await CampaignRepository(session).get(campaign_id) is None:
        raise CampaignNotFound(campaign_id)
