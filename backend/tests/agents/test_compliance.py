"""Tests for the Compliance agent and its deterministic overrides."""

import uuid
from collections.abc import Mapping

import pytest

from app.agents.compliance import ComplianceAgent
from app.agents.outputs import AdCopySet, AdVariant, ComplianceItem, ComplianceReport
from app.core.config import Settings
from app.core.errors import GuardrailViolation
from app.evaluation.datasets import BAD_CLAIMS
from app.harness.registry import ToolRegistry
from app.llm.fake import FakeLLMClient
from app.tools.policy_tools import PolicyLookupArgs, PolicyMatch
from tests.harness.context_fixtures import make_state

COPY_LABEL = "copy:Instagram"
ASSET_LABEL = "asset:assets/hero.png"


def settings(*, attempts: int = 2) -> Settings:
    return Settings(
        deepseek_api_key="test-key",
        database_url="postgresql+asyncpg://user:pass@localhost:5432/marketpilot",
        redis_url="redis://localhost:6379/0",
        retry_max_attempts=attempts,
        _env_file=None,
    )


def report(*, copy_passed: bool = True, include_asset: bool = True) -> ComplianceReport:
    items = [
        ComplianceItem(
            check=f"{COPY_LABEL} - no unsupported claims",
            passed=copy_passed,
            reason="Checked against the retrieved claims policy.",
        )
    ]
    if include_asset:
        items.append(
            ComplianceItem(
                check=f"{ASSET_LABEL} - no brand imagery",
                passed=True,
                reason="No brand or likeness is described.",
            )
        )
    return ComplianceReport(items=items)


async def policy_runner(tool: str, args: object, *, step: str = "") -> list[PolicyMatch]:
    assert tool == "policy_lookup"
    assert isinstance(args, PolicyLookupArgs)
    return [
        PolicyMatch(
            id=uuid.uuid4(),
            title="Health and beauty claims",
            source="internal://policies/health-beauty-claims",
            content="Do not promise medical outcomes for cosmetic products.",
            distance=0.0,
        )
    ]


async def emit(name: str, data: Mapping[str, object]) -> None:
    return None


def state_with_bad_claim():  # type: ignore[no-untyped-def]
    state = make_state()
    state.copy = AdCopySet(
        variants=[
            AdVariant(
                channel="Instagram",
                headline="Guaranteed hair regrowth",
                description=BAD_CLAIMS[0].text,
                cta="Buy now",
            )
        ]
    )
    return state


async def test_seeded_bad_claim_fails_even_when_the_llm_passes() -> None:
    llm = FakeLLMClient([report(copy_passed=True)])

    result = await ComplianceAgent(settings=settings()).run(
        state_with_bad_claim(), llm, emit, policy_runner
    )

    failed = next(item for item in result.items if item.check.startswith(COPY_LABEL))
    assert failed.passed is False
    assert "guaranteed or instant results" in failed.reason


async def test_clean_variant_passes() -> None:
    result = await ComplianceAgent(settings=settings()).run(
        make_state(), FakeLLMClient([report()]), emit, policy_runner
    )

    assert all(item.passed for item in result.items)


async def test_missing_item_triggers_a_retry_with_the_subject() -> None:
    llm = FakeLLMClient([report(include_asset=False), report()])
    events: list[str] = []

    async def collect(name: str, data: Mapping[str, object]) -> None:
        events.append(name)

    result = await ComplianceAgent(settings=settings()).run(
        make_state(), llm, collect, policy_runner
    )

    assert all(item.passed for item in result.items)
    assert events == ["validation_failed", "retrying"]
    assert f"missing compliance item for {ASSET_LABEL}" in llm.calls[1][-1]["content"]


def test_compliance_cannot_call_image_or_search_tools() -> None:
    registry = ToolRegistry()

    assert registry.allowed_tools("compliance") == frozenset({"policy_lookup", "read_state"})
    for tool in ("generate_image", "edit_image", "search_tools"):
        with pytest.raises(GuardrailViolation, match="not allowed"):
            registry.get_tool("compliance", tool)
