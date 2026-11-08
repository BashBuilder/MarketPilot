"""Schema verification plus the verified agent-step retry loop."""

from collections.abc import Awaitable, Callable, Mapping, Sequence

from pydantic import BaseModel, ValidationError

from app.core.config import Settings, get_settings
from app.core.errors import RetryExhausted
from app.harness.asset_validation import AssetSemanticValidator
from app.harness.copy_validation import (
    MAX_HEADLINE_LENGTH,
    MIN_HEADLINE_LENGTH,
    CopySemanticValidator,
)
from app.harness.issues import ValidationIssue, Validator

Prompt = Sequence[Mapping[str, str]]
type AgentStep[T] = Callable[[Prompt], Awaitable[T]]
EventCallback = Callable[[str, Mapping[str, object]], Awaitable[None]]

__all__ = [
    "AgentStep",
    "AssetSemanticValidator",
    "CopySemanticValidator",
    "EventCallback",
    "MAX_HEADLINE_LENGTH",
    "MIN_HEADLINE_LENGTH",
    "Prompt",
    "SchemaValidator",
    "ValidationIssue",
    "Validator",
    "run_with_verification",
]


class SchemaValidator[ModelT: BaseModel]:
    """Re-run Pydantic's schema validation at the verification boundary."""

    def __init__(self, model: type[ModelT]) -> None:
        self._model = model

    def validate(self, output: object, /) -> list[ValidationIssue]:
        try:
            self._model.model_validate(output)
        except ValidationError as error:
            return [
                ValidationIssue(
                    code="schema",
                    message=item["msg"],
                    path=".".join(str(part) for part in item["loc"]) or None,
                )
                for item in error.errors()
            ]
        return []


def _issue_text(issue: ValidationIssue) -> str:
    if issue.path:
        return f"{issue.path}: {issue.message}"
    return issue.message


def _feedback_text(issues: Sequence[ValidationIssue]) -> str:
    details = "\n".join(f"- {_issue_text(issue)}" for issue in issues)
    return (
        "Your previous output failed verification. Fix these issues and "
        f"return the complete corrected output:\n{details}"
    )


async def run_with_verification[T](
    step: AgentStep[T],
    *,
    prompt: Prompt,
    agent: str,
    validators: Sequence[Validator[T]],
    on_event: EventCallback,
    settings: Settings | None = None,
    max_attempts: int | None = None,
) -> T:
    """Run an agent step until its output passes every validator.

    Failed validation appends the issue text to the next prompt. Events are
    delivered to ``on_event``; no SSE wiring happens here.
    """
    resolved_attempts = (
        max_attempts
        if max_attempts is not None
        else (settings or get_settings()).retry_max_attempts
    )
    if resolved_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    base_messages = list(prompt)
    last_feedback = ""
    for attempt in range(1, resolved_attempts + 1):
        messages: list[Mapping[str, str]] = list(base_messages)
        if last_feedback:
            messages.append({"role": "user", "content": last_feedback})

        output = await step(messages)
        issues = [issue for validator in validators for issue in validator.validate(output)]
        if not issues:
            return output

        reason = "; ".join(_issue_text(issue) for issue in issues)
        last_feedback = _feedback_text(issues)
        await on_event("validation_failed", {"agent": agent, "reason": reason})
        if attempt < resolved_attempts:
            await on_event(
                "retrying",
                {
                    "agent": agent,
                    "attempt": attempt + 1,
                    "max_attempts": resolved_attempts,
                },
            )

    raise RetryExhausted(agent, resolved_attempts, last_feedback)
