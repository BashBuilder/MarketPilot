"""Event bus implementations: Redis Streams in production, memory in tests."""

import json
import uuid
from collections.abc import Mapping
from typing import Any, Protocol

from redis.asyncio import Redis

from app.events.envelope import BusEvent, envelope, is_terminal, sequence, stream_key


class EventBus(Protocol):
    """Append and replay per-run events; ids are opaque and increasing."""

    async def publish(
        self,
        run_id: uuid.UUID | str,
        event_type: str,
        agent: str,
        data: Mapping[str, Any],
    ) -> str:
        """Append one event and return its stream id."""
        ...

    async def read(self, run_id: uuid.UUID | str, after_id: str | None) -> list[BusEvent]:
        """Return events strictly after ``after_id`` in stream order."""
        ...

    async def close(self) -> None:
        """Release any underlying connection."""
        ...


class RedisEventBus:
    """One Redis Stream per run: ``run:{run_id}:events``."""

    def __init__(
        self,
        client: Redis,
        *,
        maxlen: int = 2000,
        ttl_seconds: int = 86400,
    ) -> None:
        self._client = client
        self._maxlen = maxlen
        self._ttl_seconds = ttl_seconds

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        maxlen: int = 2000,
        ttl_seconds: int = 86400,
    ) -> "RedisEventBus":
        client = Redis.from_url(url, decode_responses=True)
        return cls(client, maxlen=maxlen, ttl_seconds=ttl_seconds)

    async def publish(
        self,
        run_id: uuid.UUID | str,
        event_type: str,
        agent: str,
        data: Mapping[str, Any],
    ) -> str:
        key = stream_key(run_id)
        body = json.dumps(envelope(run_id, agent, data), default=str)
        event_id = await self._client.xadd(
            key,
            {"event": event_type, "data": body},
            maxlen=self._maxlen,
            approximate=True,
        )
        event: BusEvent = {
            "id": str(event_id),
            "event": event_type,
            "data": json.loads(body),
        }
        if is_terminal(event):
            await self._client.expire(key, self._ttl_seconds)
        return str(event_id)

    async def read(self, run_id: uuid.UUID | str, after_id: str | None) -> list[BusEvent]:
        minimum = f"({after_id}" if after_id else "-"
        entries = await self._client.xrange(stream_key(run_id), min=minimum, max="+") or []
        return [_decode(event_id, fields or {}) for event_id, fields in entries]

    async def close(self) -> None:
        await self._client.aclose()


class InMemoryEventBus:
    """Deterministic bus for tests and offline runs."""

    def __init__(self) -> None:
        self._streams: dict[str, list[BusEvent]] = {}
        self._next: dict[str, int] = {}

    async def publish(
        self,
        run_id: uuid.UUID | str,
        event_type: str,
        agent: str,
        data: Mapping[str, Any],
    ) -> str:
        key = stream_key(run_id)
        number = self._next.get(key, 0) + 1
        self._next[key] = number
        event_id = f"{number}-0"
        self._streams.setdefault(key, []).append(
            {
                "id": event_id,
                "event": event_type,
                "data": envelope(run_id, agent, data),
            }
        )
        return event_id

    async def read(self, run_id: uuid.UUID | str, after_id: str | None) -> list[BusEvent]:
        events = self._streams.get(stream_key(run_id), [])
        if after_id is None:
            return list(events)
        cursor = sequence(after_id)
        return [event for event in events if sequence(event["id"]) > cursor]

    async def close(self) -> None:
        self._streams.clear()


def _decode(event_id: object, fields: Mapping[bytes | str, bytes | str]) -> BusEvent:
    raw = fields.get("data", "{}")
    return {
        "id": str(event_id),
        "event": str(fields.get("event", "")),
        "data": json.loads(str(raw)),
    }
