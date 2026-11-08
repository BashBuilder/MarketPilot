"""Event bus storage, replay and terminal-event rules."""

import uuid
from typing import cast

from redis.asyncio import Redis

from app.events.bus import InMemoryEventBus, RedisEventBus
from app.events.envelope import is_terminal, stream_key


async def test_in_memory_bus_replays_everything_after_the_cursor() -> None:
    bus = InMemoryEventBus()
    run_id = uuid.uuid4()

    first = await bus.publish(run_id, "agent_started", "brief", {})
    second = await bus.publish(
        run_id, "agent_handoff", "brief", {"from": "brief", "to": "research"}
    )

    everything = await bus.read(run_id, None)
    after_first = await bus.read(run_id, first)

    assert [event["id"] for event in everything] == [first, second]
    assert [event["id"] for event in after_first] == [second]
    assert everything[1]["data"]["from"] == "brief"
    assert everything[0]["data"]["run_id"] == str(run_id)
    assert "timestamp" in everything[0]["data"]


def test_terminal_rules() -> None:
    def event(name: str, **data: object):
        return {"id": "1-0", "event": name, "data": dict(data)}

    assert is_terminal(event("awaiting_approval", version=1))
    assert is_terminal(event("completed", version=1, score=80))
    assert is_terminal(event("error", message="boom", recoverable=False))
    assert not is_terminal(event("error", message="slow", recoverable=True))
    assert not is_terminal(event("agent_started"))


class FakeRedis:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.expired: list[int] = []

    async def xadd(self, key, fields, *, maxlen, approximate):
        self.calls.append((key, fields, maxlen, approximate))
        return "12-0"

    async def xrange(self, key, *, min, max):
        self.calls.append((key, min, max))
        return [("12-0", {"event": "agent_started", "data": '{"run_id": "x"}'})]

    async def expire(self, key, ttl):
        self.expired.append(ttl)

    async def aclose(self):
        return None


async def test_redis_bus_uses_one_stream_per_run_and_expires_on_terminal() -> None:
    fake = FakeRedis()
    bus = RedisEventBus(cast(Redis, fake), maxlen=50, ttl_seconds=120)
    run_id = uuid.uuid4()

    event_id = await bus.publish(run_id, "awaiting_approval", "human", {"version": 1})
    replayed = await bus.read(run_id, None)

    assert event_id == "12-0"
    assert fake.calls[0][0] == stream_key(run_id) == f"run:{run_id}:events"
    assert fake.calls[0][2] == 50
    assert fake.expired == [120]
    assert replayed[0]["event"] == "agent_started"
