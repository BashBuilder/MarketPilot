"""Token estimation and deterministic context trimming."""

import json
from collections.abc import Callable, Mapping
from typing import Any, Final

from app.core.errors import GuardrailViolation

type TokenEstimator = Callable[[str], int]

DEFAULT_CHARS_PER_TOKEN: Final = 4

# Raw research detail is the oldest, least critical context: drop from the end
# of each list first, then drop the whole section if the budget is still tight.
RESEARCH_LISTS: Final[tuple[str, ...]] = (
    "sources",
    "messaging_angles",
    "pain_points",
    "segments",
)

# Only these string fields are truncated; ids, urls, numbers and structural
# fields keep their type. The brief and compliance report are never listed.
TEXT_FIELDS: Final[Mapping[str, frozenset[str]]] = {
    "direction": frozenset(
        ("style_guide", "composition", "image_prompts", "video_prompts", "negative_prompts")
    ),
    "copy": frozenset(("description",)),
    "assets": frozenset(("prompt",)),
    "score": frozenset(("justification",)),
}
FREE_TEXT_FIELDS: Final[tuple[str, ...]] = ("errors", "revision_feedback")
DROPPABLE_FIELDS: Final = ("direction", "assets", "copy", "score", "errors", "revision_feedback")


def estimate_tokens(text: str) -> int:
    """Approximate tokens from characters; callers can inject a real tokenizer."""
    return (len(text) + DEFAULT_CHARS_PER_TOKEN - 1) // DEFAULT_CHARS_PER_TOKEN


def context_tokens(value: object, estimator: TokenEstimator = estimate_tokens) -> int:
    """Estimate the tokens in a JSON-serialisable context value."""
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return estimator(encoded)


def trim_context(
    context: dict[str, Any],
    agent_name: str,
    budget: int,
    estimator: TokenEstimator,
) -> dict[str, Any]:
    """Trim a selected context in place until it fits ``budget`` tokens."""
    if context_tokens(context, estimator) <= budget:
        return context

    _trim_research(context, budget, estimator)
    if context_tokens(context, estimator) <= budget:
        return context
    context.pop("research", None)

    for limit in (800, 400, 200, 100, 50, 20):
        _truncate_text(context, limit)
        if context_tokens(context, estimator) <= budget:
            return context

    for field in DROPPABLE_FIELDS:
        context.pop(field, None)
        if context_tokens(context, estimator) <= budget:
            return context

    raise GuardrailViolation(
        f"{agent_name} context needs {context_tokens(context, estimator)} tokens but "
        f"the budget is {budget}; protected fields cannot be trimmed further"
    )


def _trim_research(context: dict[str, Any], budget: int, estimator: TokenEstimator) -> None:
    research = context.get("research")
    if not isinstance(research, dict):
        return
    for key in RESEARCH_LISTS:
        values = research.get(key)
        if not isinstance(values, list):
            continue
        while len(values) > 1 and context_tokens(context, estimator) > budget:
            values.pop()


def _truncate_text(context: dict[str, Any], limit: int) -> None:
    for field, keys in TEXT_FIELDS.items():
        if field in context:
            context[field] = _truncate_keys(context[field], keys, limit)
    for field in FREE_TEXT_FIELDS:
        if field in context:
            context[field] = _truncate_strings(context[field], limit)


def _truncate_keys(value: Any, keys: frozenset[str], limit: int) -> Any:
    if isinstance(value, dict):
        return {
            key: _truncate_strings(item, limit)
            if key in keys
            else _truncate_keys(item, keys, limit)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_truncate_keys(item, keys, limit) for item in value]
    return value


def _truncate_strings(value: Any, limit: int) -> Any:
    if isinstance(value, str):
        return value[:limit]
    if isinstance(value, list):
        return [_truncate_strings(item, limit) for item in value]
    if isinstance(value, dict):
        return {key: _truncate_strings(item, limit) for key, item in value.items()}
    return value
