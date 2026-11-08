"""Human-gate version snapshots are append-only and correctly linked."""

import json

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.database.models import RunStatus
from app.database.repositories import RunRepository, VersionRepository
from app.graph.versioning import package_from_state
from app.harness.checkpoints import request_approval, save_checkpoint
from tests.harness.checkpoint_fixtures import make_run
from tests.harness.context_fixtures import make_state as full_state


async def gated_version(session, run, state):
    await save_checkpoint(run.id, "reviewer", state, session=session)
    await request_approval(run.id, session=session)
    return await VersionRepository(session).latest(run.campaign_id)


def serialized(package: dict[str, object]) -> str:
    return json.dumps(package, sort_keys=True)


async def test_first_gate_creates_version_one_without_a_parent(db_session):
    run = await make_run(db_session)
    state = full_state()

    version = await gated_version(db_session, run, state)
    versions = await VersionRepository(db_session).list_for_campaign(run.campaign_id)

    assert version is not None
    assert [item.version for item in versions] == [1]
    assert version.parent_version_id is None
    assert serialized(version.package) == serialized(package_from_state(state))


async def test_second_package_creates_version_two_linked_to_one(db_session):
    run = await make_run(db_session)
    first_state = full_state()
    first = await gated_version(db_session, run, first_state)

    assert first_state.copy is not None
    revised_copy = first_state.copy.model_copy(
        update={
            "variants": [
                first_state.copy.variants[0].model_copy(
                    update={"headline": "Evening hair, handled"}
                )
            ]
        }
    )
    second_state = first_state.model_copy(update={"copy": revised_copy})
    second_run = await RunRepository(db_session).create(run.campaign_id, RunStatus.RUNNING)
    second = await gated_version(db_session, second_run, second_state)

    assert first is not None and second is not None
    assert (first.version, second.version) == (1, 2)
    assert second.parent_version_id == first.id


async def test_version_one_is_unchanged_after_version_two_is_created(db_session):
    run = await make_run(db_session)
    state = full_state()
    first = await gated_version(db_session, run, state)
    assert first is not None
    before = serialized(first.package)

    second_run = await RunRepository(db_session).create(run.campaign_id, RunStatus.RUNNING)
    await gated_version(db_session, second_run, state)

    await db_session.refresh(first)
    assert serialized(first.package) == before


async def test_repeated_gate_call_does_not_duplicate_the_version(db_session):
    run = await make_run(db_session)
    await gated_version(db_session, run, full_state())

    await request_approval(run.id, session=db_session)

    versions = await VersionRepository(db_session).list_for_campaign(run.campaign_id)
    assert [item.version for item in versions] == [1]


async def test_updating_a_version_is_rejected_by_the_database(db_session):
    run = await make_run(db_session)
    version = await gated_version(db_session, run, full_state())
    assert version is not None
    version_id = version.id
    await db_session.commit()

    with pytest.raises(DBAPIError, match="append-only"):
        await db_session.execute(
            text("UPDATE campaign_versions SET package = '{}' WHERE id = CAST(:id AS uuid)"),
            {"id": str(version_id)},
        )
        await db_session.commit()

    await db_session.rollback()
    stored = await VersionRepository(db_session).get_by_id(version_id)
    assert stored is not None
    assert serialized(stored.package) == serialized(package_from_state(full_state()))
