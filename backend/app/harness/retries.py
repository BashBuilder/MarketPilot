"""Async retries with bounded exponential backoff and jitter."""

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.core.config import get_settings
from app.core.errors import RetryExhausted, ToolError

T = TypeVar("T")
Sleep = Callable[[float], Awaitable[None]]

DEFAULT_BASE_DELAY_SECONDS = 0.5
DEFAULT_MAX_DELAY_SECONDS = 8.0
DEFAULT_JITTER_RATIO = 0.25


async def _default_sleep(delay: float) -> None:
    await asyncio.sleep(delay)


class RetryPolicy:
    """Retry retryable tool failures, then fall back or escalate.

    Only ``ToolError`` instances with ``retryable=True`` are retried. Every
    other exception, including non-retryable ``ToolError`` values, propagates
    immediately so callers can handle it without extra delay.
    """

    def __init__(
        self,
        *,
        max_attempts: int | None = None,
        base_delay: float = DEFAULT_BASE_DELAY_SECONDS,
        max_delay: float = DEFAULT_MAX_DELAY_SECONDS,
        jitter_ratio: float = DEFAULT_JITTER_RATIO,
        sleep: Sleep = _default_sleep,
        rng: random.Random | None = None,
    ) -> None:
        resolved_attempts = (
            get_settings().retry_max_attempts if max_attempts is None else max_attempts
        )
        if resolved_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if base_delay < 0:
            raise ValueError("base_delay must be non-negative")
        if max_delay < base_delay:
            raise ValueError("max_delay must be greater than or equal to base_delay")
        if not 0 <= jitter_ratio <= 1:
            raise ValueError("jitter_ratio must be between 0 and 1")

        self._max_attempts = resolved_attempts
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._jitter_ratio = jitter_ratio
        self._sleep = sleep
        self._rng = rng or random.Random()

    @property
    def max_attempts(self) -> int:
        """Total attempts allowed, including the first one."""
        return self._max_attempts

    def backoff_delay(self, attempt: int) -> float:
        """Delay after a failed attempt, capped at ``max_delay``."""
        if attempt < 1:
            raise ValueError("attempt must be at least 1")
        exponential = min(self._base_delay * float(2 ** (attempt - 1)), self._max_delay)
        jitter = exponential * self._jitter_ratio * float(self._rng.random())
        return float(min(exponential + jitter, self._max_delay))

    async def run(
        self,
        operation: Callable[[], Awaitable[T]],
        *,
        agent: str,
        fallback: Callable[[], Awaitable[T]] | None = None,
    ) -> T:
        """Run ``operation``, retrying retryable tool errors.

        ``fallback`` is invoked once after the final failed attempt. Without a
        fallback, exhausted retries raise ``RetryExhausted`` chained to the
        last tool error.
        """
        last_error: ToolError | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                return await operation()
            except ToolError as error:
                if not error.retryable:
                    raise
                last_error = error
                if attempt < self._max_attempts:
                    await self._sleep(self.backoff_delay(attempt))

        if fallback is not None:
            return await fallback()

        assert last_error is not None
        raise RetryExhausted(agent, self._max_attempts, str(last_error)) from last_error
