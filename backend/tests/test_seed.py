"""Seed data is stable across repeated runs."""

from sqlalchemy import func, select

from app.database.models import Campaign, PolicyDocument
from app.database.seed import DEMO_CAMPAIGN_ID, POLICY_DOCUMENTS, seed


async def test_seed_is_idempotent(db_session):
    await seed(db_session)
    await seed(db_session)

    campaign = await db_session.get(Campaign, DEMO_CAMPAIGN_ID)
    campaign_count = await db_session.scalar(select(func.count()).select_from(Campaign))
    document_count = await db_session.scalar(select(func.count()).select_from(PolicyDocument))

    assert campaign is not None
    assert campaign.idea.startswith("Create an advertising campaign")
    assert campaign_count == 1
    assert document_count == len(POLICY_DOCUMENTS) == 3
