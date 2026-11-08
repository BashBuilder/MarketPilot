"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_error_handlers
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.events.bus import EventBus, RedisEventBus
from app.runs.launcher import RunLauncher, WorkflowRunLauncher


def create_app(
    settings: Settings | None = None,
    launcher: RunLauncher | None = None,
    bus: EventBus | None = None,
) -> FastAPI:
    """Build the application with an injectable launcher and event bus."""
    resolved = settings or get_settings()
    resolved_bus = bus or RedisEventBus.from_url(
        resolved.redis_url,
        maxlen=resolved.event_stream_maxlen,
        ttl_seconds=resolved.event_stream_ttl_seconds,
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        yield
        await cast(RunLauncher, application.state.launcher).shutdown()
        await cast(EventBus, application.state.event_bus).close()

    application = FastAPI(title="MarketPilot API", lifespan=lifespan)
    application.state.event_bus = resolved_bus
    application.state.launcher = launcher or WorkflowRunLauncher(resolved, resolved_bus)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.frontend_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Last-Event-ID"],
    )

    @application.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Liveness probe at the root path."""
        return {"status": "ok"}

    application.include_router(api_router)
    register_error_handlers(application)
    return application


app = create_app()
