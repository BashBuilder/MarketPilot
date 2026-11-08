"""Shared event envelope, stream keys and terminal-event rules."""

import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, TypedDict

TERMINAL_EVENTS: frozenset[str] = frozenset({"awaiting_approval", "completed"})


class BusEvent(TypedDict):
    """One stored stream entry, already shaped for SSE."""

    id: str
    event: str
    data: dict[str, Any]


def stream_key(run_id: uuid.UUID | str) -> str:
    """Return the Redis stream key for one run."""
    return f"run:{run_id}:events"


def is_terminal(event: BusEvent) -> bool:
    """A stream ends after a gate, a completion or a fatal error."""
    if event["event"] in TERMINAL_EVENTS:
        return True
    return event["event"] == "error" and not bool(event["data"].get("recoverable"))


def envelope(run_id: uuid.UUID | str, agent: str, data: Mapping[str, Any]) -> dict[str, Any]:
    """Build the body every SSE data frame carries."""
    payload: dict[str, Any] = {
        "run_id": str(run_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "agent": agent,
    }
    payload.update({key: value for key, value in data.items() if key not in payload})
    return payload


def sequence(event_id: str) -> int:
    """Return the numeric part of a stream id for in-memory comparisons."""
    return int(event_id.split("-", 1)[0])
