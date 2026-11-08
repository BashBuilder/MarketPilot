"""Project campaigns and runs onto the shared summary shape."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import CampaignSummary
from app.database.models import Campaign, RunStatus
from app.database.repositories import RunRepository, VersionRepository

CLOSED_RUN_STATUSES = frozenset({RunStatus.COMPLETED, RunStatus.FAILED})


async def build_summary(session: AsyncSession, campaign: Campaign) -> CampaignSummary:
    """Return a summary with the latest version and the newest open run."""
    latest = await VersionRepository(session).latest(campaign.id)
    runs = await RunRepository(session).list_for_campaign(campaign.id)
    active = next((run for run in runs if run.status not in CLOSED_RUN_STATUSES), None)
    return CampaignSummary(
        id=campaign.id,
        idea=campaign.idea,
        status=campaign.status,
        latest_version=latest.version if latest is not None else None,
        latest_score=latest.score if latest is not None else None,
        active_run_id=active.id if active is not None else None,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )
