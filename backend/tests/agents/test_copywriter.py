"""Tests for the Copywriter agent and revision mode."""

import json
from collections.abc import Mapping

import pytest

from app.agents.copywriter import CopywriterAgent
from app.agents.outputs import AdCopySet, AdVariant, ComplianceItem, ComplianceReport
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


def copy(
    *,
    instagram_headline: str = "Morning hair, handled",
    email_headline: str = "Your new wash-day ritual",
) -> AdCopySet:
    return AdCopySet(
        variants=[
            AdVariant(
                channel="Instagram",
                headline=instagram_headline,
                description="A lightweight serum that keeps frizz away all day.",
                cta="Shop the serum",
            ),
            AdVariant(
                channel="Email",
                headline=email_headline,
                description="Meet the serum that fits into your existing routine.",
                cta="See the ritual",
            ),
        ]
    )


async def emit(name: str, data: Mapping[str, object]) -> None:
    return None


def fenced_context(content: str) -> dict[str, object]:
    start = content.index("<untrusted")
    body_start = content.index("\n", start) + 1
    body_end = content.rindex("\n</untrusted>")
    return json.loads(content[body_start:body_end])


async def test_normal_run_returns_copy_without_revision_mode() -> None:
    state = make_state()
    state.copy = None
    expected = copy()
    llm = FakeLLMClient([expected])

    result = await CopywriterAgent(settings=settings()).run(state, llm, emit)

    assert result is expected
    context = fenced_context(llm.calls[0][1]["content"])
    assert "revision_mode" not in context


async def test_revision_run_changes_only_the_flagged_variant() -> None:
    previous = copy()
    state = make_state()
    state.copy = previous
    state.compliance = ComplianceReport(
        items=[
            ComplianceItem(
                check="No guaranteed results",
                passed=False,
                reason="Instagram copy promises a guaranteed result",
            ),
            ComplianceItem(
                check="No medical claims",
                passed=True,
                reason="Copy avoids cure language",
            ),
        ]
    )
    revised = AdCopySet(
        variants=[
            AdVariant(
                channel="Instagram",
                headline="Morning hair, softly handled",
                description="A lightweight serum that keeps frizz away all day.",
                cta="Shop the serum",
            ),
            previous.variants[1],
        ]
    )
    llm = FakeLLMClient([revised])

    result = await CopywriterAgent(settings=settings()).run(state, llm, emit)

    assert result is revised
    context = fenced_context(llm.calls[0][1]["content"])
    assert context["revision_mode"] is True
    assert context["flagged_channels"] == ["instagram"]
    assert context["compliance"] == {
        "items": [
            {
                "check": "No guaranteed results",
                "passed": False,
                "reason": "Instagram copy promises a guaranteed result",
            }
        ]
    }
    assert context["copy"]["variants"][1]["channel"] == "Email"


async def test_changing_an_unflagged_variant_triggers_a_retry() -> None:
    previous = copy()
    state = make_state()
    state.copy = previous
    state.compliance = ComplianceReport(
        items=[
            ComplianceItem(
                check="No guaranteed results",
                passed=False,
                reason="Instagram copy promises a guaranteed result",
            )
        ]
    )
    changed = AdCopySet(
        variants=[
            previous.variants[0],
            AdVariant(
                channel="Email",
                headline="A different email headline",
                description="Meet the serum that fits into your existing routine.",
                cta="See the ritual",
            ),
        ]
    )
    valid = AdCopySet(
        variants=[
            AdVariant(
                channel="Instagram",
                headline="Morning hair, softly handled",
                description="A lightweight serum that keeps frizz away all day.",
                cta="Shop the serum",
            ),
            previous.variants[1],
        ]
    )
    llm = FakeLLMClient([changed, valid])
    events: list[str] = []

    async def collect(name: str, data: Mapping[str, object]) -> None:
        events.append(name)

    result = await CopywriterAgent(settings=settings()).run(state, llm, collect)

    assert result is valid
    assert events == ["validation_failed", "retrying"]
    feedback = llm.calls[1][-1]["content"]
    assert "unflagged variant changed" in feedback
    assert "Email" in feedback


def test_copywriter_may_look_up_policy_but_not_generate_images() -> None:
    registry = ToolRegistry()

    assert "policy_lookup" in registry.allowed_tools("copywriter")
    for tool in ("generate_image", "edit_image", "generate_video"):
        with pytest.raises(GuardrailViolation, match="not allowed"):
            registry.get_tool("copywriter", tool)
