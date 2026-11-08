"""Tests for per-agent context selection and budget trimming."""

import json

import pytest

from app.harness.context import (
    AGENT_CONTEXT_FIELDS,
    build_agent_context,
    estimate_tokens,
)
from tests.harness.context_fixtures import make_state


def context_size(context: dict[str, object]) -> int:
    encoded = json.dumps(context, ensure_ascii=False, sort_keys=True, default=str)
    return estimate_tokens(encoded)


@pytest.mark.parametrize(("agent", "expected"), AGENT_CONTEXT_FIELDS.items())
def test_each_agent_receives_only_mapped_fields(
    agent: str,
    expected: tuple[str, ...],
) -> None:
    context = build_agent_context(make_state(), agent, 100_000)

    assert tuple(context) == expected
    assert set(context) == set(expected)


def test_long_fixture_stays_under_budget() -> None:
    context = build_agent_context(make_state(long=True), "reviewer", 400)

    assert context_size(context) <= 400


def test_brief_and_compliance_are_never_trimmed() -> None:
    state = make_state(long=True)
    context = build_agent_context(state, "reviewer", 400)
    dumped = state.model_dump(mode="json")

    assert context["brief"] == dumped["brief"]
    assert context["compliance"] == dumped["compliance"]
    assert context["idea"] == dumped["idea"]


def test_estimator_is_injectable() -> None:
    calls: list[str] = []

    def estimator(text: str) -> int:
        calls.append(text)
        return 0

    context = build_agent_context(make_state(), "brief", 10, estimator=estimator)

    assert "idea" in context
    assert calls


def test_unknown_agent_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown agent"):
        build_agent_context(make_state(), "nobody", 1000)


def test_default_estimator_approximates_characters() -> None:
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcde") == 2
