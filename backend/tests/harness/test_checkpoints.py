"""Checkpoint persistence: append-only rows with re-validated state."""

import pytest
from sqlalchemy import func, select

from app.core.errors import ValidationFailure
from app.database.models import WorkflowCheckpoint
from app.harness.checkpoints import (
    DONE,
    load_latest_checkpoint,
    request_approval,
    resume_point,
    save_checkpoint,
)
from tests.harness.checkpoint_fixtures import make_run, make_state


async def test_save_then_load_returns_an_equal_state(db_session):
    run = await make_run(db_session)
    state = make_state("First checkpoint")

    saved = await save_checkpoint(run.id, "brief", state, session=db_session)
    loaded = await load_latest_checkpoint(run.id, session=db_session)

    assert saved.step == 1
    assert saved.node == "brief"
    assert loaded == state


async def test_latest_of_several_checkpoints_is_returned(db_session):
    run = await make_run(db_session)
    first = make_state("First checkpoint")
    second = make_state("Second checkpoint")

    await save_checkpoint(run.id, "brief", first, session=db_session)
    await save_checkpoint(run.id, "research", second, session=db_session)

    loaded = await load_latest_checkpoint(run.id, session=db_session)

    assert loaded == second


async def test_each_save_appends_a_new_row(db_session):
    run = await make_run(db_session)
    state = make_state("Append-only checkpoint")

    await save_checkpoint(run.id, "brief", state, session=db_session)
    await save_checkpoint(run.id, "brief", state, session=db_session)

    loaded = await load_latest_checkpoint(run.id, session=db_session)
    count = await db_session.scalar(select(func.count()).select_from(WorkflowCheckpoint))

    assert loaded == state
    assert count == 2


async def test_corrupt_state_raises_validation_failure(db_session):
    run = await make_run(db_session)
    db_session.add(WorkflowCheckpoint(run_id=run.id, step=1, node="brief", state={"idea": ""}))
    await db_session.flush()

    with pytest.raises(ValidationFailure):
        await load_latest_checkpoint(run.id, session=db_session)


async def test_malformed_json_text_raises_validation_failure(db_session):
    run = await make_run(db_session)
    db_session.add(WorkflowCheckpoint(run_id=run.id, step=1, node="brief", state="{not-json"))
    await db_session.flush()

    with pytest.raises(ValidationFailure):
        await load_latest_checkpoint(run.id, session=db_session)


async def test_missing_checkpoint_returns_none(db_session):
    run = await make_run(db_session)

    assert await load_latest_checkpoint(run.id, session=db_session) is None


async def test_crash_after_third_node_resumes_at_fourth(db_session):
    run = await make_run(db_session)
    for node in ("brief", "research", "copywriter"):
        await save_checkpoint(run.id, node, make_state(node), session=db_session)

    assert await resume_point(run.id, session=db_session) == "creative_director"


async def test_resume_point_without_checkpoints_starts_at_brief(db_session):
    run = await make_run(db_session)

    assert await resume_point(run.id, session=db_session) == "brief"


async def test_resume_point_after_the_human_gate_is_done(db_session):
    run = await make_run(db_session)
    await save_checkpoint(run.id, "reviewer", make_state("Reviewed"), session=db_session)
    await request_approval(run.id, session=db_session)

    assert await resume_point(run.id, session=db_session) == DONE
