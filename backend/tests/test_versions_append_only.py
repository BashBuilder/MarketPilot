"""Prove PostgreSQL rejects mutations to committed campaign versions."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.database.repositories import CampaignRepository, VersionRepository


async def create_committed_version(db_session):
    campaign = await CampaignRepository(db_session).create("Campaign")
    version = await VersionRepository(db_session).create(
        campaign.id,
        {"brief": {"product": "Shampoo"}},
    )
    await db_session.commit()
    return version


async def test_version_update_is_rejected(db_session):
    version = await create_committed_version(db_session)
    version_id = version.id

    with pytest.raises(DBAPIError, match="append-only"):
        await db_session.execute(
            text("UPDATE campaign_versions SET score = 99 WHERE id = CAST(:id AS uuid)"),
            {"id": str(version_id)},
        )
        await db_session.commit()

    await db_session.rollback()

    stored = await VersionRepository(db_session).get_by_id(version_id)

    assert stored is not None
    assert stored.score is None


async def test_version_delete_is_rejected(db_session):
    version = await create_committed_version(db_session)
    version_id = version.id

    with pytest.raises(DBAPIError, match="append-only"):
        await db_session.execute(
            text("DELETE FROM campaign_versions WHERE id = CAST(:id AS uuid)"),
            {"id": str(version_id)},
        )
        await db_session.commit()

    await db_session.rollback()

    stored = await VersionRepository(db_session).get_by_id(version_id)

    assert stored is not None
