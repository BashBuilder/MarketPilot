"""Human-gate primitives: request approval and record decisions."""

import pytest

from app.database.models import ApprovalDecision, RunStatus
from app.database.repositories import (
    ApprovalRepository,
    RunRepository,
    VersionRepository,
)
from app.harness.checkpoints import (
    DONE,
    HUMAN_GATE,
    load_latest_checkpoint,
    request_approval,
    resume_point,
    save_checkpoint,
    submit_decision,
)
from tests.harness.checkpoint_fixtures import make_run, make_state


async def test_request_approval_sets_status_and_appends_gate_checkpoint(db_session):
    run = await make_run(db_session)
    await save_checkpoint(run.id, "reviewer", make_state("Reviewed"), session=db_session)

    checkpoint = await request_approval(run.id, session=db_session)

    stored = await RunRepository(db_session).get(run.id)
    assert stored is not None
    assert stored.status == RunStatus.AWAITING_APPROVAL
    assert stored.current_node == HUMAN_GATE
    assert checkpoint.node == HUMAN_GATE
    assert checkpoint.step == 2
    latest = await load_latest_checkpoint(run.id, session=db_session)
    assert latest is not None
    assert latest.status == "awaiting_approval"


async def test_request_approval_without_checkpoint_uses_campaign_idea(db_session):
    run = await make_run(db_session)

    await request_approval(run.id, session=db_session)

    state = await load_latest_checkpoint(run.id, session=db_session)
    assert state is not None
    assert state.idea == "Checkpoint campaign"


async def test_revise_routes_to_target_node_and_records_decision(db_session):
    run = await make_run(db_session)
    await save_checkpoint(run.id, "reviewer", make_state("Reviewed"), session=db_session)
    await request_approval(run.id, session=db_session)

    node = await submit_decision(
        run.id,
        "revise",
        comment="Tighten the headline",
        target_node="copywriter",
        session=db_session,
    )

    assert node == "copywriter"
    stored = await RunRepository(db_session).get(run.id)
    assert stored is not None
    assert stored.status == RunStatus.RUNNING
    assert stored.current_node == "copywriter"
    approvals = await ApprovalRepository(db_session).list_for_run(run.id)
    assert len(approvals) == 1
    assert approvals[0].decision == ApprovalDecision.REVISE
    assert approvals[0].comment == "Tighten the headline"
    assert approvals[0].target_node == "copywriter"
    versions = await VersionRepository(db_session).list_for_campaign(run.campaign_id)
    assert len(versions) == 1


async def test_approve_returns_done_marker(db_session):
    run = await make_run(db_session)
    await save_checkpoint(run.id, "reviewer", make_state("Reviewed"), session=db_session)
    await request_approval(run.id, session=db_session)

    result = await submit_decision(
        run.id,
        "approve",
        comment="Looks good",
        session=db_session,
    )

    assert result == DONE
    stored = await RunRepository(db_session).get(run.id)
    assert stored is not None
    assert stored.status == RunStatus.COMPLETED
    assert stored.current_node == DONE
    approvals = await ApprovalRepository(db_session).list_for_run(run.id)
    assert approvals[0].decision == ApprovalDecision.APPROVE


async def test_revise_without_target_continues_after_last_agent(db_session):
    run = await make_run(db_session)
    await save_checkpoint(run.id, "reviewer", make_state("Reviewed"), session=db_session)
    await request_approval(run.id, session=db_session)

    node = await submit_decision(run.id, "revise", comment="Rework", session=db_session)

    assert node == "supervisor"


async def test_resume_point_uses_the_revise_target_after_a_decision(db_session):
    run = await make_run(db_session)
    await save_checkpoint(run.id, "reviewer", make_state("Reviewed"), session=db_session)
    await request_approval(run.id, session=db_session)
    await submit_decision(
        run.id,
        "revise",
        comment="Tighten the headline",
        target_node="copywriter",
        session=db_session,
    )

    assert await resume_point(run.id, session=db_session) == "copywriter"


async def test_revise_rejects_unknown_target_node(db_session):
    run = await make_run(db_session)
    await request_approval(run.id, session=db_session)

    with pytest.raises(ValueError, match="unknown target node"):
        await submit_decision(
            run.id,
            "revise",
            comment="Rework",
            target_node="nobody",
            session=db_session,
        )
