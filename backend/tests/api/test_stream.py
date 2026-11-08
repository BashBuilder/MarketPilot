"""SSE replay, reconnect, terminal close and unknown-run behaviour."""

import uuid

from app.database.models import CampaignStatus, RunStatus
from app.database.repositories import CampaignRepository, RunRepository
from app.events.bus import InMemoryEventBus
from tests.api.sse import parse_sse


async def make_run(db_session):
    campaign = await CampaignRepository(db_session).create("Hair care", CampaignStatus.RUNNING)
    run = await RunRepository(db_session).create(campaign.id, RunStatus.RUNNING)
    await db_session.commit()
    return run


async def seed_events(bus: InMemoryEventBus, run_id: uuid.UUID) -> list[str]:
    ids: list[str] = []
    for event_type, agent, data in [
        ("agent_started", "brief", {}),
        ("agent_handoff", "brief", {"from": "brief", "to": "research"}),
        (
            "tool_called",
            "research",
            {"tool": "search_tools", "duration_ms": 3, "status": "success"},
        ),
        ("agent_started", "research", {}),
        ("awaiting_approval", "human", {"version": 1}),
    ]:
        ids.append(await bus.publish(run_id, event_type, agent, data))
    return ids


async def test_stream_replays_events_in_order_and_closes_at_the_gate(
    client, harness, db_session
) -> None:
    run = await make_run(db_session)
    ids = await seed_events(harness.bus, run.id)

    response = await client.get(f"/api/v1/runs/{run.id}/stream")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    raw = response.text
    assert ": heartbeat" not in raw
    events = parse_sse(raw)
    assert [event["id"] for event in events] == ids
    assert [event["event"] for event in events] == [
        "agent_started",
        "agent_handoff",
        "tool_called",
        "agent_started",
        "awaiting_approval",
    ]
    assert events[-1]["data"]["version"] == 1
    assert events[2]["data"]["tool"] == "search_tools"
    assert events[0]["data"]["run_id"] == str(run.id)


async def test_reconnect_with_last_event_id_skips_delivered_events(
    client, harness, db_session
) -> None:
    run = await make_run(db_session)
    ids = await seed_events(harness.bus, run.id)

    response = await client.get(
        f"/api/v1/runs/{run.id}/stream",
        headers={"Last-Event-ID": ids[2]},
    )

    events = parse_sse(response.text)
    assert [event["id"] for event in events] == ids[3:]
    assert len({event["id"] for event in events}) == len(events)


async def test_unknown_run_returns_404_before_streaming(client) -> None:
    run_id = uuid.uuid4()

    response = await client.get(f"/api/v1/runs/{run_id}/stream")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "run_not_found"
