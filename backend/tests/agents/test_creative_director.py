"""Tests for the Creative Director agent and its safety checks."""

from collections.abc import Mapping

import pytest

from app.agents.creative_director import CreativeDirectionValidator, CreativeDirectorAgent
from app.agents.outputs import CreativeDirection
from app.agents.prompts.loader import load_prompt
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


def direction(
    *,
    image_prompt: str = "Editorial still life of a shampoo bottle on a stone plinth",
    negative_prompts: tuple[str, ...] = ("harsh shadows",),
) -> CreativeDirection:
    return CreativeDirection(
        image_prompts=[image_prompt],
        video_prompts=["Slow orbit around the bottle in soft daylight"],
        style_guide="Warm neutral palette with soft editorial lighting.",
        composition="Centered subject with generous negative space.",
        negative_prompts=list(negative_prompts),
    )


async def emit(name: str, data: Mapping[str, object]) -> None:
    return None


async def test_valid_direction_passes() -> None:
    expected = direction()
    llm = FakeLLMClient([expected])

    result = await CreativeDirectorAgent(settings=settings()).run(make_state(), llm, emit)

    assert result is expected


async def test_blocklisted_brand_triggers_a_retry() -> None:
    invalid = direction(image_prompt="A Nike billboard on a city street at dusk")
    valid = direction()
    llm = FakeLLMClient([invalid, valid])
    events: list[str] = []

    async def collect(name: str, data: Mapping[str, object]) -> None:
        events.append(name)

    result = await CreativeDirectorAgent(settings=settings()).run(make_state(), llm, collect)

    assert result is valid
    assert events == ["validation_failed", "retrying"]
    feedback = llm.calls[1][-1]["content"]
    assert "blocked name or brand: Nike" in feedback


def test_creative_director_has_no_tools() -> None:
    registry = ToolRegistry()

    assert registry.allowed_tools("creative_director") == frozenset()
    for tool in ("search_tools", "policy_lookup", "generate_image"):
        with pytest.raises(GuardrailViolation, match="not allowed"):
            registry.get_tool("creative_director", tool)


@pytest.mark.parametrize(
    ("update", "message"),
    [
        ({"image_prompts": [""]}, "image prompt 1 is empty"),
        ({"image_prompts": ["x" * 30]}, "maximum 20"),
        ({"negative_prompts": []}, "at least one negative prompt is required"),
    ],
)
def test_direction_validator_rejects_unusable_prompts(
    update: dict[str, list[str]],
    message: str,
) -> None:
    output = direction().model_copy(update=update)

    issues = CreativeDirectionValidator(20).validate(output)

    assert any(message in issue.message for issue in issues)


def test_creative_director_prompt_is_versioned() -> None:
    prompt = load_prompt("creative_director")

    assert prompt.version == "1"
    assert "real people" in prompt.text
