"""Contract tests: every endpoint response and SSE event matches section 2."""

import uuid
from typing import Any

from app.database.models import CampaignStatus, RunStatus
from app.database.repositories import CampaignRepository, RunRepository
from app.evaluation.datasets import GOLDEN_IDEAS
from tests.api.sse import parse_sse
from tests.contract_endpoints import (
    assert_create,
    assert_error,
    assert_summary,
    assert_version_summary,
)
from tests.contract_events import assert_event
from tests.contract_shapes import assert_approve, assert_diff, assert_package, assert_revise


async def gated_run(client) -> tuple[str, str]:
    created = await client.post("/api/v1/campaigns", json={"idea": GOLDEN_IDEAS[0].idea})
    assert created.status_code == 201
    body = created.json()
    assert_create(body)
    stream = await client.get(f"/api/v1/runs/{body['run_id']}/stream")
    assert stream.status_code == 200
    assert parse_sse(stream.text)[-1]["event"] == "awaiting_approval"
    return body["campaign_id"], body["run_id"]


async def test_health_campaign_list_detail_and_error_shapes(fake_client) -> None:
    assert (await fake_client.get("/health")).json() == {"status": "ok"}
    assert (await fake_client.get("/api/v1/health")).json() == {"status": "ok"}

    created = await fake_client.post("/api/v1/campaigns", json={"idea": GOLDEN_IDEAS[0].idea})
    assert created.status_code == 201
    assert_create(created.json())

    listed = (await fake_client.get("/api/v1/campaigns")).json()
    assert isinstance(listed, list)
    for summary in listed:
        assert_summary(summary)

    detail = await fake_client.get(f"/api/v1/campaigns/{created.json()['campaign_id']}")
    assert detail.status_code == 200
    assert_summary(detail.json())

    missing = await fake_client.get(f"/api/v1/campaigns/{uuid.uuid4()}")
    assert missing.status_code == 404
    assert_error(missing.json())

    invalid = await fake_client.post("/api/v1/campaigns", json={"idea": " "})
    assert invalid.status_code == 422
    assert_error(invalid.json())


async def test_version_package_diff_and_decision_shapes(fake_client) -> None:
    campaign_id, run_id = await gated_run(fake_client)

    versions = (await fake_client.get(f"/api/v1/campaigns/{campaign_id}/versions")).json()
    assert isinstance(versions, list) and versions
    for summary in versions:
        assert_version_summary(summary)

    package = (await fake_client.get(f"/api/v1/campaigns/{campaign_id}/versions/1")).json()
    assert_package(package)

    same = (await fake_client.get(f"/api/v1/campaigns/{campaign_id}/versions/1/diff/1")).json()
    assert_diff(same)
    assert same["changes"] == []

    revised = await fake_client.post(
        f"/api/v1/runs/{run_id}/revise",
        json={"comment": "Tighten the headline", "target_node": "copywriter"},
    )
    assert revised.status_code == 200
    assert_revise(revised.json())
    assert revised.json()["version"] == 2
    continuation = revised.json()["run_id"]

    approved = await fake_client.post(
        f"/api/v1/runs/{continuation}/approve", json={"comment": "Ship it"}
    )
    assert approved.status_code == 200
    assert_approve(approved.json())

    completed = await fake_client.get(f"/api/v1/runs/{continuation}/stream")
    frames = parse_sse(completed.text)
    assert frames and frames[-1]["event"] == "completed"
    for frame in frames:
        assert_event(frame)

    versions = (await fake_client.get(f"/api/v1/campaigns/{campaign_id}/versions")).json()
    assert [summary["version"] for summary in versions] == [1, 2]
    for summary in versions:
        assert_version_summary(summary)
    diff = (await fake_client.get(f"/api/v1/campaigns/{campaign_id}/versions/1/diff/2")).json()
    assert_diff(diff)
    assert_summary((await fake_client.get(f"/api/v1/campaigns/{campaign_id}")).json())


async def test_every_sse_event_matches_its_shape(fake_client, fake_harness, db_factory) -> None:
    first = await seed_run(db_factory)
    events: list[tuple[str, str, dict[str, Any]]] = [
        ("agent_started", "brief", {}),
        ("agent_handoff", "brief", {"from": "brief", "to": "research"}),
        (
            "tool_called",
            "research",
            {"tool": "search_tools", "duration_ms": 4, "status": "success"},
        ),
        ("validation_failed", "copywriter", {"reason": "headline too short"}),
        ("retrying", "copywriter", {"attempt": 2, "max_attempts": 3}),
        ("error", "supervisor", {"message": "temporary", "recoverable": True}),
        ("awaiting_approval", "human", {"version": 1}),
    ]
    for event_type, agent, data in events:
        await fake_harness.bus.publish(first, event_type, agent, data)

    frames = parse_sse((await fake_client.get(f"/api/v1/runs/{first}/stream")).text)
    assert [frame["event"] for frame in frames] == [event for event, _, _ in events]
    for frame in frames:
        assert_event(frame)

    second = await seed_run(db_factory)
    await fake_harness.bus.publish(second, "completed", "human", {"version": 1, "score": 80})
    completed = parse_sse((await fake_client.get(f"/api/v1/runs/{second}/stream")).text)
    assert completed[0]["event"] == "completed"
    assert_event(completed[0])


async def seed_run(factory) -> uuid.UUID:
    async with factory() as session:
        campaign = await CampaignRepository(session).create("Hair care", CampaignStatus.RUNNING)
        run = await RunRepository(session).create(campaign.id, RunStatus.RUNNING)
        await session.commit()
        return run.id
