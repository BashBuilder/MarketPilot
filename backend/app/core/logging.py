"""JSON logging with run-scoped context."""

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from typing import Any

run_id: ContextVar[str | None] = ContextVar("run_id", default=None)
campaign_id: ContextVar[str | None] = ContextVar("campaign_id", default=None)
agent: ContextVar[str | None] = ContextVar("agent", default=None)
step: ContextVar[str | None] = ContextVar("step", default=None)

_CONTEXT_VARS: dict[str, ContextVar[str | None]] = {
    "run_id": run_id,
    "campaign_id": campaign_id,
    "agent": agent,
    "step": step,
}


class JsonFormatter(logging.Formatter):
    """Render each record as one JSON object, adding any bound context."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for name, variable in _CONTEXT_VARS.items():
            value = variable.get()
            if value is not None:
                payload[name] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


@contextmanager
def log_context(**values: str | None) -> Iterator[None]:
    """Bind run context for the duration of the block."""
    unknown = set(values) - set(_CONTEXT_VARS)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise KeyError(f"Unknown log context fields: {names}")

    tokens: list[tuple[ContextVar[str | None], Token[str | None]]] = []
    try:
        for name, value in values.items():
            variable = _CONTEXT_VARS[name]
            tokens.append((variable, variable.set(value)))
        yield
    finally:
        for variable, token in reversed(tokens):
            variable.reset(token)


_configured = False


def configure_logging(level: str = "INFO") -> None:
    """Attach the JSON handler to the root logger exactly once."""
    global _configured

    root = logging.getLogger()
    root.setLevel(level.upper())
    if _configured:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    _configured = True
