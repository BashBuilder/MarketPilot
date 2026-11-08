"""Approve and revise endpoints: success, 404, 409 and 422."""

import uuid

from app.api import runs as runs_module
from app.database.models import CampaignStatus, RunStatus
from app.database.repositories import CampaignRepository, RunRepository
from tests.api.helpers import Harness


async def make_run(db_session, status: RunStatus = RunStatus.PENDING):
    campaign = await CampaignRepository(db_session).create("Hair care", CampaignStatus.RUNNING)
    run = await RunRepository(db_session).create(campaign.id, status)
    await db_session.commit()
    return run


async def test_approve_completes_and_returns_the_version(
    client, harness: Harness, db_session, monkeypatch
) -> None:
    run = await make_run(db_session, RunStatus.AWAITING_APPROVAL)

    async def fake_approve(run_id, comment, **kwargs):
        return {"status": "completed", "version": 1}

    monkeypatch.setattr(runs_module, "approve_run", fake_approve)

    response = await client.post(f"/api/v1/runs/{run.id}/approve", json={"comment": "Looks good"})

    assert response.status_code == 200
    assert response.json() == {"status": "completed", "version": 1}


async def test_revise_starts_the_continuation_run(
    client, harness: Harness, db_session, monkeypatch
) -> None:
    run = await make_run(db_session, RunStatus.AWAITING_APPROVAL)
    continuation = uuid.uuid4()

    async def fake_revise(run_id, comment, target_node=None, **kwargs):
        return {"run_id": str(continuation), "version": 2}

    monkeypatch.setattr(runs_module, "revise_run", fake_revise)

    response = await client.post(
        f"/api/v1/runs/{run.id}/revise",
        json={"comment": "Tighten the headline", "target_node": "copywriter"},
    )

    assert response.status_code == 200
    assert response.json() == {"run_id": str(continuation), "version": 2}
    assert harness.launcher.started == [str(continuation)]


async def test_unknown_run_is_404_for_both_actions(client) -> None:
    run_id = uuid.uuid4()

    approve = await client.post(f"/api/v1/runs/{run_id}/approve", json={})
    revise = await client.post(f"/api/v1/runs/{run_id}/revise", json={"comment": "Rework"})

    assert approve.status_code == 404
    assert approve.json()["error"]["code"] == "run_not_found"
    assert revise.status_code == 404
    assert revise.json()["error"]["code"] == "run_not_found"


async def test_a_run_that_is_not_awaiting_approval_is_409(client, db_session) -> None:
    run = await make_run(db_session)

    approve = await client.post(f"/api/v1/runs/{run.id}/approve", json={})
    revise = await client.post(f"/api/v1/runs/{run.id}/revise", json={"comment": "Rework"})

    assert approve.status_code == 409
    assert approve.json()["error"]["code"] == "run_not_awaiting_approval"
    assert revise.status_code == 409
    assert revise.json()["error"]["code"] == "run_not_awaiting_approval"


async def test_revise_requires_a_non_empty_comment(client, db_session) -> None:
    run = await make_run(db_session, RunStatus.AWAITING_APPROVAL)

    response = await client.post(f"/api/v1/runs/{run.id}/revise", json={"comment": "   "})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "revision_comment_required"


async def test_revise_rejects_an_unknown_target_node(client, db_session) -> None:
    run = await make_run(db_session, RunStatus.AWAITING_APPROVAL)

    response = await client.post(
        f"/api/v1/runs/{run.id}/revise",
        json={"comment": "Rework", "target_node": "nobody"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_failed"


async def test_overlong_approval_comment_is_422(client, harness: Harness, db_session) -> None:
    run = await make_run(db_session, RunStatus.AWAITING_APPROVAL)

    response = await client.post(
        f"/api/v1/runs/{run.id}/approve",
        json={"comment": "x" * (harness.settings.max_comment_length + 1)},
    )

    assert response.status_code == 422
    assert response.json()["error"]["details"]["field"] == "comment"
