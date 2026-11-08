"""Tests for the async retry policy."""

import pytest

from app.core.errors import RetryExhausted, ToolError
from app.harness.retries import RetryPolicy


def make_policy(*, max_attempts: int = 3) -> tuple[RetryPolicy, list[float]]:
    sleeps: list[float] = []

    async def sleep(delay: float) -> None:
        sleeps.append(delay)

    return (
        RetryPolicy(max_attempts=max_attempts, base_delay=0.1, sleep=sleep),
        sleeps,
    )


async def test_retryable_error_then_success_returns_the_result() -> None:
    policy, sleeps = make_policy()
    attempts = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ToolError("image", "timed out", retryable=True)
        return "generated"

    result = await policy.run(operation, agent="designer")

    assert result == "generated"
    assert attempts == 2
    assert len(sleeps) == 1


async def test_non_retryable_error_is_not_retried() -> None:
    policy, sleeps = make_policy()
    attempts = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        raise ToolError("image", "invalid prompt", retryable=False)

    with pytest.raises(ToolError, match="invalid prompt"):
        await policy.run(operation, agent="designer")

    assert attempts == 1
    assert sleeps == []


async def test_exhausted_retries_raise_retry_exhausted() -> None:
    policy, sleeps = make_policy(max_attempts=3)
    attempts = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        raise ToolError("image", "provider down", retryable=True)

    with pytest.raises(RetryExhausted) as excinfo:
        await policy.run(operation, agent="designer")

    assert attempts == 3
    assert len(sleeps) == 2
    assert excinfo.value.attempts == 3
    assert excinfo.value.last_error == "image: provider down"
    assert isinstance(excinfo.value.__cause__, ToolError)


async def test_fallback_is_used_after_the_last_failed_attempt() -> None:
    policy, _ = make_policy(max_attempts=2)
    attempts = 0
    fallback_calls = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        raise ToolError("image", "provider down", retryable=True)

    async def fallback() -> str:
        nonlocal fallback_calls
        fallback_calls += 1
        return "placeholder"

    result = await policy.run(operation, agent="designer", fallback=fallback)

    assert result == "placeholder"
    assert attempts == 2
    assert fallback_calls == 1


async def test_unexpected_errors_propagate_without_retry() -> None:
    policy, sleeps = make_policy()
    attempts = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await policy.run(operation, agent="designer")

    assert attempts == 1
    assert sleeps == []


def test_backoff_is_exponential_and_capped() -> None:
    policy = RetryPolicy(
        max_attempts=5,
        base_delay=1.0,
        max_delay=3.0,
        jitter_ratio=0.0,
    )

    assert policy.backoff_delay(1) == 1.0
    assert policy.backoff_delay(2) == 2.0
    assert policy.backoff_delay(3) == 3.0
    assert policy.backoff_delay(4) == 3.0


def test_invalid_max_attempts_is_rejected() -> None:
    with pytest.raises(ValueError, match="max_attempts"):
        RetryPolicy(max_attempts=0)
