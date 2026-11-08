"""Tests for the verified agent-step retry loop."""

from collections import deque
from collections.abc import Awaitable, Callable, Mapping, Sequence

import pytest

from app.agents.outputs.ad_copy_set import AdCopySet, AdVariant
from app.core.config import Settings
from app.core.errors import RetryExhausted
from app.harness.copy_validation import CopySemanticValidator
from app.harness.verification import Prompt, run_with_verification

Step = Callable[[Prompt], Awaitable[AdCopySet]]

PROMPT: Prompt = [
    {"role": "system", "content": "Write advertising copy."},
    {"role": "user", "content": "Hair care serum for adults aged 25 to 40."},
]


def settings(*, attempts: int = 2) -> Settings:
    return Settings(
        deepseek_api_key="test-key",
        database_url="postgresql+asyncpg://user:pass@localhost:5432/marketpilot",
        redis_url="redis://localhost:6379/0",
        retry_max_attempts=attempts,
        _env_file=None,
    )


def valid_copy() -> AdCopySet:
    return AdCopySet.model_validate(
        {
            "variants": [
                {
                    "channel": "instagram",
                    "headline": "Morning hair, handled",
                    "description": "A lightweight serum that keeps frizz away all day.",
                    "cta": "Shop the serum",
                }
            ]
        }
    )


def invalid_copy() -> AdCopySet:
    variant = AdVariant.model_construct(
        channel="instagram",
        headline="abc",
        description="A lightweight serum that keeps frizz away all day.",
        cta="Shop the serum",
    )
    return AdCopySet.model_construct(variants=[variant])


def make_step(outputs: Sequence[AdCopySet], calls: list[list[dict[str, str]]]) -> Step:
    remaining = deque(outputs)

    async def step(messages: Prompt) -> AdCopySet:
        calls.append([dict(message) for message in messages])
        return remaining.popleft()

    return step


async def test_first_attempt_invalid_then_valid_returns_the_second_output() -> None:
    calls: list[list[dict[str, str]]] = []
    events: list[tuple[str, dict[str, object]]] = []
    valid = valid_copy()

    async def on_event(name: str, data: Mapping[str, object]) -> None:
        events.append((name, dict(data)))

    result = await run_with_verification(
        make_step([invalid_copy(), valid], calls),
        prompt=PROMPT,
        agent="copywriter",
        validators=[CopySemanticValidator()],
        on_event=on_event,
        settings=settings(attempts=3),
    )

    assert result is valid
    assert len(calls) == 2
    assert [name for name, _ in events] == ["validation_failed", "retrying"]
    assert events[1][1]["attempt"] == 2
    assert events[1][1]["max_attempts"] == 3


async def test_validator_feedback_reaches_the_second_prompt() -> None:
    calls: list[list[dict[str, str]]] = []

    async def on_event(name: str, data: Mapping[str, object]) -> None:
        return None

    await run_with_verification(
        make_step([invalid_copy(), valid_copy()], calls),
        prompt=PROMPT,
        agent="copywriter",
        validators=[CopySemanticValidator()],
        on_event=on_event,
        settings=settings(attempts=2),
    )

    assert calls[0] == [dict(message) for message in PROMPT]
    assert calls[1][: len(PROMPT)] == [dict(message) for message in PROMPT]
    feedback = calls[1][-1]
    assert feedback["role"] == "user"
    assert "headline is 3 characters (minimum 5)" in feedback["content"]


async def test_exhausted_attempts_raise_retry_exhausted_and_emit_events() -> None:
    calls: list[list[dict[str, str]]] = []
    events: list[tuple[str, dict[str, object]]] = []

    async def on_event(name: str, data: Mapping[str, object]) -> None:
        events.append((name, dict(data)))

    with pytest.raises(RetryExhausted) as excinfo:
        await run_with_verification(
            make_step([invalid_copy(), invalid_copy()], calls),
            prompt=PROMPT,
            agent="copywriter",
            validators=[CopySemanticValidator()],
            on_event=on_event,
            settings=settings(attempts=2),
        )

    assert len(calls) == 2
    assert excinfo.value.attempts == 2
    assert "headline is 3 characters (minimum 5)" in excinfo.value.last_error
    assert [name for name, _ in events] == [
        "validation_failed",
        "retrying",
        "validation_failed",
    ]
    assert events[1][1]["attempt"] == 2
    assert events[1][1]["max_attempts"] == 2
