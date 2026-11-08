"""Background launcher contract and asyncio-task implementation."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.database.session import session_scope
from app.events.bus import EventBus
from app.events.emitter import bus_emitter
from app.graph.runner import run_workflow

logger = logging.getLogger(__name__)


class RunLauncher(Protocol):
    """Start a run in the background without blocking the request."""

    async def start(self, run_id: str) -> None:
        """Schedule the run identified by ``run_id``."""
        ...

    async def shutdown(self) -> None:
        """Cancel in-flight tasks and release resources."""
        ...


class RecordingLauncher:
    """Test launcher that only records started ids; never executes."""

    def __init__(self) -> None:
        self.started: list[str] = []

    async def start(self, run_id: str) -> None:
        self.started.append(run_id)

    async def shutdown(self) -> None:
        return None


class WorkflowRunLauncher:
    """Own one asyncio task per run and turn crashes into fatal error events."""

    def __init__(
        self,
        settings: Settings,
        bus: EventBus,
        *,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._settings = settings
        self._bus = bus
        self._session_factory = session_factory
        self._tasks: set[asyncio.Task[None]] = set()
        self._closed = False

    async def start(self, run_id: str) -> None:
        if self._closed:
            raise RuntimeError("launcher is shutting down")
        task = asyncio.create_task(self._run(run_id), name=f"workflow-run-{run_id}")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _run(self, run_id: str) -> None:
        try:
            async with self._session() as session:
                await run_workflow(
                    run_id,
                    emit=bus_emitter(self._bus, run_id),
                    session=session,
                    settings=self._settings,
                )
        except asyncio.CancelledError:
            raise
        except Exception as error:
            logger.exception("workflow run %s crashed", run_id)
            try:
                await self._bus.publish(
                    run_id,
                    "error",
                    "supervisor",
                    {"message": str(error), "recoverable": False},
                )
            except Exception:
                logger.exception("failed to publish fatal error for run %s", run_id)

    @asynccontextmanager
    async def _session(self) -> AsyncIterator[AsyncSession]:
        if self._session_factory is None:
            async with session_scope() as session:
                yield session
            return
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def shutdown(self) -> None:
        self._closed = True
        tasks = list(self._tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
