"""Tests for the Reviewer agent and its rubric validators."""

from collections.abc import Mapping

import pytest

from app.agents.outputs import CreativeScore, ScoreDimension
from app.agents.prompts.loader import load_prompt
from app.agents.reviewer import ReviewerAgent
from app.agents.scoring import weighted_total
from app.core.config import Settings
from app.core.errors import GuardrailViolation
from app.harness.registry import ToolRegistry
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


def dimension(value: float, justification: str = "Clear and on brief") -> ScoreDimension:
    return ScoreDimension(score=value, justification=justification)


def score(*, total: float | None = None) -> CreativeScore:
    dimensions = {
        "brief_alignment": dimension(8),
        "audience_fit": dimension(7),
        "copy_quality": dimension(9),
        "visual_quality": dimension(8),
        "compliance_risk": dimension(7),
    }
    resolved = weighted_total(dimensions.values()) if total is None else total
    return CreativeScore(**dimensions, total=resolved)


async def emit(name: str, data: Mapping[str, object]) -> None:
    return None


async def test_total_mismatch_triggers_a_retry() -> None:
    invalid = CreativeScore.model_construct(
        brief_alignment=dimension(8),
        audience_fit=dimension(7),
        copy_quality=dimension(9),
        visual_quality=dimension(8),
        compliance_risk=dimension(7),
        total=99.0,
    )
    valid = score()
    llm = FakeLLMClient([invalid, valid])
    events: list[str] = []

    async def collect(name: str, data: Mapping[str, object]) -> None:
        events.append(name)

    result = await ReviewerAgent(settings=settings()).run(make_state(), llm, collect)

    assert result == valid
    assert events == ["validation_failed", "retrying"]
    assert "total must equal" in llm.calls[1][-1]["content"]


async def test_empty_justification_triggers_a_retry() -> None:
    invalid = score()
    blank = ScoreDimension.model_construct(score=8, justification=" ")
    invalid = invalid.model_copy(update={"brief_alignment": blank})
    valid = score()
    llm = FakeLLMClient([invalid, valid])
    events: list[str] = []

    async def collect(name: str, data: Mapping[str, object]) -> None:
        events.append(name)

    result = await ReviewerAgent(settings=settings()).run(make_state(), llm, collect)

    assert result == valid
    assert events == ["validation_failed", "retrying"]
    assert "brief_alignment needs a justification" in llm.calls[1][-1]["content"]


def test_reviewer_is_denied_export_package() -> None:
    registry = ToolRegistry()

    assert "policy_lookup" in registry.allowed_tools("reviewer")
    for tool in ("export_package", "generate_image", "search_tools"):
        with pytest.raises(GuardrailViolation, match="not allowed"):
            registry.get_tool("reviewer", tool)


def test_reviewer_output_has_no_approval_field() -> None:
    assert "approval" not in CreativeScore.model_fields
    assert "approved" not in CreativeScore.model_fields
    assert "decision" not in CreativeScore.model_fields


def test_reviewer_prompt_is_versioned_and_forbids_approval() -> None:
    prompt = load_prompt("reviewer")

    assert prompt.version == "1"
    assert "Never approve" in prompt.text
