"""Tests for the shared agent scaffold."""

import json
from collections.abc import Mapping

import pytest

from app.agents.base import BaseAgent
from app.agents.outputs import CampaignBrief
from app.core.config import Settings
from app.core.errors import RetryExhausted
from app.harness.issues import ValidationIssue
from app.llm.fake import FakeLLMClient
from tests.harness.context_fixtures import make_state


def settings(*, attempts: int = 2) -> Settings:
    return Settings(
        deepseek_api_key="test-key",
        database_url="postgresql+asyncpg://user:pass@localhost:5432/marketpilot",
        redis_url="redis://localhost:6379/0",
        retry_max_attempts=attempts,
        _env_file=None,
    )


def brief(*, goal: str = "Launch a hydrating shampoo for adults with dry hair.") -> CampaignBrief:
    return CampaignBrief(
        product="HydraSilk Shampoo",
        goal=goal,
        audience="Adults aged 25 to 40 who style their hair daily.",
        tone="Warm and confident",
        channels=["Instagram", "Email"],
        constraints=["No medical claims"],
    )


class GoalMentionsHair:
    """Semantic validator used to exercise retries."""

    def validate(self, output: CampaignBrief, /) -> list[ValidationIssue]:
        if "hair" not in output.goal.lower():
            return [ValidationIssue("goal", "goal must mention hair")]
        return []


def event_collector() -> tuple[list[tuple[str, Mapping[str, object]]], object]:
    events: list[tuple[str, Mapping[str, object]]] = []

    async def emit(name: str, data: Mapping[str, object]) -> None:
        events.append((name, data))

    return events, emit


def fenced_context(content: str) -> dict[str, object]:
    start = content.index("<untrusted")
    body_start = content.index("\n", start) + 1
    body_end = content.rindex("\n</untrusted>")
    return json.loads(content[body_start:body_end])


async def test_only_mapped_context_reaches_the_prompt() -> None:
    state = make_state()
    expected = brief()
    llm = FakeLLMClient([expected])
    agent = BaseAgent(name="brief", output_model=CampaignBrief, settings=settings())
    events, emit = event_collector()

    result = await agent.run(state, llm, emit)

    assert result is expected
    system, user = llm.calls[0]
    assert system["role"] == "system"
    assert system["content"].startswith("You are the Brief agent")
    assert 'source="workflow_state:brief"' in user["content"]
    context = fenced_context(user["content"])
    assert set(context) == {"idea", "brief", "revision_feedback"}
    assert context["idea"] == state.idea
    assert context["revision_feedback"] is None
    assert events == []


async def test_agent_does_not_mutate_state() -> None:
    state = make_state()
    snapshot = state.model_dump(mode="json")
    agent = BaseAgent(name="brief", output_model=CampaignBrief, settings=settings())
    _, emit = event_collector()

    await agent.run(state, FakeLLMClient([brief()]), emit)

    assert state.model_dump(mode="json") == snapshot


async def test_invalid_output_retries_with_validator_feedback() -> None:
    invalid = brief(goal="Sell more shampoo")
    valid = brief()
    llm = FakeLLMClient([invalid, valid])
    agent = BaseAgent(
        name="brief",
        output_model=CampaignBrief,
        validators=[GoalMentionsHair()],
        settings=settings(attempts=2),
    )
    events, emit = event_collector()

    result = await agent.run(make_state(), llm, emit)

    assert result is valid
    assert [name for name, _ in events] == ["validation_failed", "retrying"]
    feedback = llm.calls[1][-1]
    assert feedback["role"] == "user"
    assert "goal must mention hair" in feedback["content"]


async def test_exhausted_retries_raise_retry_exhausted() -> None:
    invalid = brief(goal="Sell more shampoo")
    llm = FakeLLMClient([invalid, invalid])
    agent = BaseAgent(
        name="brief",
        output_model=CampaignBrief,
        validators=[GoalMentionsHair()],
        settings=settings(attempts=2),
    )
    _, emit = event_collector()

    with pytest.raises(RetryExhausted) as excinfo:
        await agent.run(make_state(), llm, emit)

    assert excinfo.value.attempts == 2
    assert "goal must mention hair" in excinfo.value.last_error
    assert len(llm.calls) == 2
