"""Repository behavior against a migrated PostgreSQL database."""

from app.database.models import ApprovalDecision, CampaignStatus, RunStatus
from app.database.repositories import (
    ApprovalRepository,
    CampaignRepository,
    RunRepository,
    VersionRepository,
)


async def test_campaign_create_get_list_and_status(db_session):
    repository = CampaignRepository(db_session)

    campaign = await repository.create("A hair-care campaign")

    assert campaign.status == CampaignStatus.DRAFT
    assert await repository.get(campaign.id) is campaign
    assert [item.id for item in await repository.list()] == [campaign.id]

    await repository.update_status(campaign, CampaignStatus.RUNNING)
    await db_session.commit()

    stored = await repository.get(campaign.id)

    assert stored is not None
    assert stored.status == CampaignStatus.RUNNING


async def test_run_status_updates(db_session):
    campaign = await CampaignRepository(db_session).create("Campaign")
    repository = RunRepository(db_session)
    run = await repository.create(campaign.id, RunStatus.RUNNING)

    await repository.update_status(
        run,
        RunStatus.COMPLETED,
        current_node="reviewer",
    )
    await db_session.commit()

    stored = await repository.get(run.id)

    assert stored is not None
    assert stored.status == RunStatus.COMPLETED
    assert stored.current_node == "reviewer"


async def test_versions_are_numbered_linked_and_ordered(db_session):
    campaign = await CampaignRepository(db_session).create("Campaign")
    repository = VersionRepository(db_session)

    first = await repository.create(campaign.id, {"brief": {"product": "Shampoo"}})
    second = await repository.create(
        campaign.id,
        {"brief": {"product": "Shampoo v2"}},
        parent_version_id=first.id,
        score=82.0,
    )
    await db_session.commit()

    assert (first.version, second.version) == (1, 2)
    assert second.parent_version_id == first.id

    listed = await repository.list_for_campaign(campaign.id)
    latest = await repository.latest(campaign.id)
    by_number = await repository.get(campaign.id, 2)

    assert [version.version for version in listed] == [1, 2]
    assert latest is not None and latest.id == second.id
    assert by_number is not None and by_number.id == second.id


async def test_approval_records_decision_and_comment(db_session):
    campaign = await CampaignRepository(db_session).create("Campaign")
    run = await RunRepository(db_session).create(campaign.id)
    version = await VersionRepository(db_session).create(campaign.id, {})
    repository = ApprovalRepository(db_session)

    approval = await repository.create(
        run_id=run.id,
        campaign_version_id=version.id,
        decision=ApprovalDecision.REVISE,
        comment="Tighten the headline",
        target_node="copywriter",
    )
    await db_session.commit()

    listed = await repository.list_for_run(run.id)

    assert [item.id for item in listed] == [approval.id]
    assert listed[0].decision == ApprovalDecision.REVISE
    assert listed[0].comment == "Tighten the headline"
