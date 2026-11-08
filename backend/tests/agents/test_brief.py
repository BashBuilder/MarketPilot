"""Tests for the Brief agent."""

from collections.abc import Mapping

import pytest

from app.agents.brief import BriefAgent, BriefSemanticValidator
from app.agents.outputs import CampaignBrief
from app.core.config import Settings
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


def valid_brief() -> CampaignBrief:
    return CampaignBrief(
        product="HydraSilk Shampoo",
        goal="Launch a hydrating shampoo for adults with dry hair.",
        audience="Adults aged 25 to 40 who style their hair daily.",
        tone="Warm and confident",
        channels=["Instagram", "Email"],
        constraints=["Fictional product", "No medical claims"],
    )


async def emit(name: str, data: Mapping[str, object]) -> None:
    return None


async def test_valid_brief_passes_without_retries() -> None:
    expected = valid_brief()
    llm = FakeLLMClient([expected])
    agent = BriefAgent(settings=settings())

    result = await agent.run(make_state(), llm, emit)

    assert result is expected
    assert len(llm.calls) == 1


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("product", "product must not be empty"),
        ("goal", "goal must not be empty"),
        ("audience", "audience must not be empty"),
    ],
)
def test_validator_rejects_empty_required_fields(field: str, message: str) -> None:
    output = valid_brief().model_copy(update={field: "   "})

    issues = BriefSemanticValidator().validate(output)

    assert [issue.message for issue in issues] == [message]


def test_validator_requires_at_least_one_channel() -> None:
    output = valid_brief().model_copy(update={"channels": ["  "]})

    issues = BriefSemanticValidator().validate(output)

    assert [issue.message for issue in issues] == ["at least one channel is required"]


async def test_missing_audience_retries_with_the_issue_text() -> None:
    invalid = valid_brief().model_copy(update={"audience": ""})
    valid = valid_brief()
    llm = FakeLLMClient([invalid, valid])
    agent = BriefAgent(settings=settings(attempts=2))

    result = await agent.run(make_state(), llm, emit)

    assert result is valid
    assert len(llm.calls) == 2
    feedback = llm.calls[1][-1]
    assert feedback["role"] == "user"
    assert "audience must not be empty" in feedback["content"]
