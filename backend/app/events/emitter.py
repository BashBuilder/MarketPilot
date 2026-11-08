"""Adapt an EventBus into the harness ``EventCallback`` contract."""

import uuid
from collections.abc import Mapping

from app.events.bus import EventBus
from app.harness.verification import EventCallback

_RESERVED = frozenset({"run_id", "timestamp", "agent"})


def bus_emitter(bus: EventBus, run_id: uuid.UUID | str) -> EventCallback:
    """Bind a run to a bus and return the callback agents and nodes call."""

    async def emit(event_type: str, data: Mapping[str, object]) -> None:
        agent = str(data.get("agent", ""))
        extra = {key: value for key, value in data.items() if key not in _RESERVED}
        await bus.publish(run_id, event_type, agent, extra)

    return emit
