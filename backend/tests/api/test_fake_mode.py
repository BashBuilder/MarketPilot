"""Full fake-mode pipeline through httpx with the real asyncio launcher."""

from app.evaluation.datasets import GOLDEN_IDEAS
from tests.api.sse import parse_sse

EXPECTED = [
    "agent_started",
    "agent_handoff",
    "agent_started",
    "agent_handoff",
    "agent_started",
    "agent_handoff",
    "agent_started",
    "agent_handoff",
    "agent_started",
    "agent_handoff",
    "agent_started",
    "agent_handoff",
    "agent_started",
    "agent_handoff",
    "awaiting_approval",
]


async def test_fake_mode_run_streams_the_pipeline_in_order(fake_client) -> None:
    created = await fake_client.post(
        "/api/v1/campaigns",
        json={"idea": GOLDEN_IDEAS[0].idea},
    )

    assert created.status_code == 201
    run_id = created.json()["run_id"]
    response = await fake_client.get(f"/api/v1/runs/{run_id}/stream")

    assert response.status_code == 200
    events = parse_sse(response.text)
    names = [event["event"] for event in events]

    assert [name for name in names if name != "tool_called"] == EXPECTED
    assert "tool_called" in names
    assert events[-1]["event"] == "awaiting_approval"
    assert events[-1]["data"]["version"] == 1
    assert events[-1]["data"]["run_id"] == run_id

    resumed = await fake_client.get(
        f"/api/v1/runs/{run_id}/stream",
        headers={"Last-Event-ID": events[2]["id"]},
    )
    replayed = parse_sse(resumed.text)

    assert [event["id"] for event in replayed] == [event["id"] for event in events[3:]]
    assert len({event["id"] for event in replayed}) == len(replayed)
