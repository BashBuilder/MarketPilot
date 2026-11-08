"""Creative Director agent: safe, production-ready creative direction."""

from app.agents.base import BaseAgent
from app.agents.blocklist import BLOCKED_NAMES
from app.agents.outputs import CreativeDirection
from app.core.config import Settings, get_settings
from app.harness.issues import ValidationIssue


class CreativeDirectionValidator:
    """Check prompt usability, length and blocked names."""

    def __init__(self, max_prompt_length: int) -> None:
        if max_prompt_length < 1:
            raise ValueError("max_prompt_length must be at least 1")
        self._max_prompt_length = max_prompt_length

    def validate(self, output: CreativeDirection, /) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if not output.image_prompts:
            issues.append(
                ValidationIssue("direction.image_prompts", "at least one image prompt is required")
            )
        for index, prompt in enumerate(output.image_prompts, start=1):
            length = len(prompt.strip())
            if length == 0:
                issues.append(
                    ValidationIssue("direction.image_prompts", f"image prompt {index} is empty")
                )
            elif length > self._max_prompt_length:
                issues.append(
                    ValidationIssue(
                        "direction.image_prompts",
                        f"image prompt {index} is {length} characters "
                        f"(maximum {self._max_prompt_length})",
                    )
                )

        if not output.negative_prompts:
            issues.append(
                ValidationIssue(
                    "direction.negative_prompts",
                    "at least one negative prompt is required",
                )
            )

        text = " ".join(
            (
                *output.image_prompts,
                *output.video_prompts,
                output.style_guide,
                output.composition,
                *output.negative_prompts,
            )
        ).casefold()
        for name in BLOCKED_NAMES:
            if name.casefold() in text:
                issues.append(
                    ValidationIssue("direction.blocklist", f"blocked name or brand: {name}")
                )
        return issues


class CreativeDirectorAgent(BaseAgent[CreativeDirection]):
    """Produce direction without any tool access."""

    def __init__(self, settings: Settings | None = None) -> None:
        resolved = settings or get_settings()
        super().__init__(
            name="creative_director",
            output_model=CreativeDirection,
            prompt_name="creative_director",
            validators=[CreativeDirectionValidator(resolved.max_image_prompt_length)],
            settings=resolved,
        )
