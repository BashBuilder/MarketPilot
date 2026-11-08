"""Expected SSE event shapes from section 2 of the backend guide."""

from typing import Any

from tests.contract_shapes import assert_keys, assert_timestamp, assert_uuid

EVENT_TYPES = {
    "agent_started",
    "agent_handoff",
    "tool_called",
    "validation_failed",
    "retrying",
    "awaiting_approval",
    "completed",
    "error",
}
AGENTS = {
    "brief",
    "research",
    "copywriter",
    "creative_director",
    "designer",
    "compliance",
    "reviewer",
    "supervisor",
    "human",
}
TOOL_STATUSES = {"success", "error", "denied"}


def assert_event(frame: dict[str, Any]) -> None:
    assert_keys(frame, {"id", "event", "data"})
    assert isinstance(frame["id"], str) and frame["id"]
    assert frame["event"] in EVENT_TYPES
    data = frame["data"]
    assert isinstance(data, dict)
    assert {"run_id", "timestamp", "agent"} <= set(data)
    assert_uuid(data["run_id"])
    assert_timestamp(data["timestamp"])
    assert data["agent"] in AGENTS

    event = frame["event"]
    if event == "agent_handoff":
        _assert_handoff(data)
    elif event == "tool_called":
        assert isinstance(data["tool"], str) and data["tool"]
        assert isinstance(data["duration_ms"], int) and data["duration_ms"] >= 0
        assert data["status"] in TOOL_STATUSES
    elif event == "validation_failed":
        assert isinstance(data["reason"], str) and data["reason"]
    elif event == "retrying":
        assert isinstance(data["attempt"], int) and data["attempt"] >= 2
        assert isinstance(data["max_attempts"], int)
    elif event == "awaiting_approval":
        assert isinstance(data["version"], int)
    elif event == "completed":
        assert isinstance(data["version"], int)
        assert data["score"] is None or isinstance(data["score"], int | float)
    elif event == "error":
        assert isinstance(data["message"], str) and data["message"]
        assert isinstance(data["recoverable"], bool)


def _assert_handoff(data: dict[str, Any]) -> None:
    assert data["from"] in AGENTS
    assert data["to"] in AGENTS
