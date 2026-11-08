"""Context-held emitter the tool middleware publishes through."""

from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar

ToolEventEmitter = Callable[[str, str, int, str], Awaitable[None]]

_emitter: ContextVar[ToolEventEmitter | None] = ContextVar("marketpilot_tool_emitter", default=None)


@contextmanager
def tool_event_emitter(emitter: ToolEventEmitter) -> Iterator[None]:
    """Install ``emitter`` for every tool call made in this context."""
    token = _emitter.set(emitter)
    try:
        yield
    finally:
        _emitter.reset(token)


async def emit_tool_call(*, agent: str, tool: str, duration_ms: int, status: str) -> None:
    """Publish one tool event when a context emitter is installed."""
    emitter = _emitter.get()
    if emitter is None:
        return
    await emitter(agent, tool, duration_ms, status)
