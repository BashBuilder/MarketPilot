"""Server-Sent Events endpoint with replay and heartbeats."""

import asyncio
import json
import time
import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings, get_event_bus, get_session
from app.core.config import Settings
from app.core.errors import RunNotFound
from app.database.repositories import RunRepository
from app.events.bus import EventBus
from app.events.envelope import BusEvent, is_terminal

router = APIRouter(tags=["stream"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
BusDep = Annotated[EventBus, Depends(get_event_bus)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@router.get("/runs/{run_id}/stream")
async def stream_run(
    run_id: uuid.UUID,
    request: Request,
    session: SessionDep,
    bus: BusDep,
    settings: SettingsDep,
) -> StreamingResponse:
    """Replay missed events, then follow new ones until a terminal event."""
    if await RunRepository(session).get(run_id) is None:
        raise RunNotFound(run_id)
    last_id = request.headers.get("Last-Event-ID")
    return StreamingResponse(
        _events(request, bus, run_id, last_id, settings),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


async def _events(
    request: Request,
    bus: EventBus,
    run_id: uuid.UUID,
    last_id: str | None,
    settings: Settings,
) -> AsyncIterator[str]:
    cursor = last_id
    heartbeat_at = time.monotonic()
    while True:
        events = await bus.read(run_id, cursor)
        for event in events:
            cursor = event["id"]
            heartbeat_at = time.monotonic()
            yield format_sse(event)
            if is_terminal(event):
                return
        if time.monotonic() - heartbeat_at >= settings.sse_heartbeat_seconds:
            heartbeat_at = time.monotonic()
            yield ": heartbeat\n\n"
        if not events:
            if await request.is_disconnected():
                return
            await asyncio.sleep(settings.sse_poll_seconds)


def format_sse(event: BusEvent) -> str:
    """Render one stored event as an SSE frame."""
    data = json.dumps(event["data"], separators=(",", ":"), default=str)
    return f"id: {event['id']}\nevent: {event['event']}\ndata: {data}\n\n"
