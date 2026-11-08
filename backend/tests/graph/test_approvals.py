"""Approve and revise decisions through the human-gate API."""

import uuid
from pathlib import Path

import pytest

from app.core.errors import RevisionCommentRequired, RunNotAwaitingApproval
from app.database.models import ApprovalDecision, RunStatus
from app.database.repositories import ApprovalRepository, RunRepository, VersionRepository
from app.graph.approvals import approve_run, revise_run
from app.graph.workflow import run_workflow
from app.llm.fake import FakeLLMClient
from tests.graph.workflow_fixtures import generated_asset, settings
from tests.graph.workflow_outputs import brief, compliance, copy, direction, research, score
from tests.graph.workflow_test_helpers import start_run


def revised_copy():
    original = copy()
    return original.model_copy(
        update={
            "variants": [
                original.variants[0].model_copy(update={"headline": "Evening hair, handled"})
            ]
        }
    )


async def gated_run(db_session, tmp_path: Path):
    run = await start_run(db_session)
    asset = await generated_asset(tmp_path)
    await run_workflow(
        run.id,
        llm=FakeLLMClient(
            [brief(), research(), copy(), direction(), compliance(asset.path), score()]
        ),
        settings=settings(tmp_path),
        session=db_session,
    )
    return run


async def test_approve_records_a_row_and_completes(db_session, tmp_path: Path):
    run = await gated_run(db_session, tmp_path)

    result = await approve_run(
        run.id,
        "Looks good",
        settings=settings(tmp_path),
        session=db_session,
    )

    assert result == {"status": "completed", "version": 1}
    approvals = await ApprovalRepository(db_session).list_for_run(run.id)
    assert len(approvals) == 1
    assert approvals[0].decision == ApprovalDecision.APPROVE
    assert approvals[0].comment == "Looks good"
    stored = await RunRepository(db_session).get(run.id)
    assert stored is not None and stored.status == RunStatus.COMPLETED


async def test_revise_creates_the_next_version_and_feeds_the_target(db_session, tmp_path: Path):
    run = await gated_run(db_session, tmp_path)
    asset = await generated_asset(tmp_path)
    llm = FakeLLMClient([revised_copy(), direction(), compliance(asset.path), score()])

    result = await revise_run(
        run.id,
        "Tighten the headline",
        target_node="copywriter",
        llm=llm,
        settings=settings(tmp_path),
        session=db_session,
    )

    versions = await VersionRepository(db_session).list_for_campaign(run.campaign_id)
    assert result["version"] == 2
    assert [version.version for version in versions] == [1, 2]
    assert versions[1].parent_version_id == versions[0].id
    assert versions[1].package["copy"]["variants"][0]["headline"] == "Evening hair, handled"

    context = llm.calls[0][-1]["content"]
    assert "Tighten the headline" in context
    assert copy().variants[0].headline in context

    approvals = await ApprovalRepository(db_session).list_for_run(run.id)
    assert approvals[-1].decision == ApprovalDecision.REVISE
    assert approvals[-1].target_node == "copywriter"
    original = await RunRepository(db_session).get(run.id)
    continuation = await RunRepository(db_session).get(uuid.UUID(result["run_id"]))
    assert original is not None and original.status == RunStatus.COMPLETED
    assert continuation is not None and continuation.status == RunStatus.AWAITING_APPROVAL


@pytest.mark.parametrize("comment", ["   ", None])
async def test_revise_without_a_comment_is_rejected(db_session, comment):
    run = await start_run(db_session)

    with pytest.raises(RevisionCommentRequired):
        await revise_run(run.id, comment, session=db_session)


async def test_approving_a_run_that_is_not_waiting_is_rejected(db_session):
    run = await start_run(db_session)

    with pytest.raises(RunNotAwaitingApproval):
        await approve_run(run.id, session=db_session)
