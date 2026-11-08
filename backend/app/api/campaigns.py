"""Campaign creation, listing and detail endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_launcher, get_session
from app.api.schemas import (
    CampaignSummary,
    CreateCampaignRequest,
    CreateCampaignResponse,
)
from app.api.summaries import build_summary
from app.core.config import Settings
from app.core.errors import CampaignNotFound, InvalidRequest
from app.database.models import CampaignStatus, RunStatus
from app.database.repositories import CampaignRepository, RunRepository
from app.runs.launcher import RunLauncher

router = APIRouter(tags=["campaigns"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
LauncherDep = Annotated[RunLauncher, Depends(get_launcher)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]


@router.post(
    "/campaigns",
    response_model=CreateCampaignResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_campaign(
    payload: CreateCampaignRequest,
    session: SessionDep,
    launcher: LauncherDep,
    settings: SettingsDep,
) -> CreateCampaignResponse:
    """Create a campaign and its first run, then hand the run to the launcher."""
    idea = _valid_idea(payload.idea, settings.max_idea_length)
    campaign = await CampaignRepository(session).create(idea, CampaignStatus.RUNNING)
    run = await RunRepository(session).create(campaign.id, RunStatus.RUNNING)
    await session.commit()
    await launcher.start(str(run.id))
    return CreateCampaignResponse(campaign_id=campaign.id, run_id=run.id)


@router.get("/campaigns", response_model=list[CampaignSummary])
async def list_campaigns(session: SessionDep) -> list[CampaignSummary]:
    """Return campaigns newest first."""
    campaigns = await CampaignRepository(session).list()
    return [await build_summary(session, campaign) for campaign in campaigns]


@router.get("/campaigns/{campaign_id}", response_model=CampaignSummary)
async def get_campaign(campaign_id: uuid.UUID, session: SessionDep) -> CampaignSummary:
    """Return one campaign summary or a 404 envelope."""
    campaign = await CampaignRepository(session).get(campaign_id)
    if campaign is None:
        raise CampaignNotFound(campaign_id)
    return await build_summary(session, campaign)


def _valid_idea(idea: str, limit: int) -> str:
    cleaned = idea.strip()
    if not cleaned:
        raise InvalidRequest("idea must not be empty", field="idea")
    if len(cleaned) > limit:
        raise InvalidRequest(
            f"idea must be at most {limit} characters",
            field="idea",
        )
    return cleaned
