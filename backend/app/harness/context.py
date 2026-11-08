"""Per-agent context selection with a token budget."""

from collections.abc import Mapping
from typing import Any, Final

from app.graph.state import WorkflowState
from app.harness.context_trim import TokenEstimator, estimate_tokens, trim_context

ALL_FIELDS: Final[tuple[str, ...]] = (
    "idea",
    "brief",
    "research",
    "copy",
    "direction",
    "assets",
    "compliance",
    "score",
    "target_node",
    "revision_feedback",
    "versions",
    "status",
    "retry_counters",
    "errors",
)

AGENT_CONTEXT_FIELDS: Final[Mapping[str, tuple[str, ...]]] = {
    "brief": ("idea",),
    "research": ("idea", "brief"),
    "copywriter": ("idea", "brief", "research", "compliance"),
    "creative_director": ("idea", "brief", "research", "copy"),
    "designer": ("idea", "brief", "direction", "compliance"),
    "compliance": ("idea", "brief", "copy", "direction", "assets", "compliance"),
    "reviewer": ALL_FIELDS,
    "supervisor": ALL_FIELDS,
}


def build_agent_context(
    state: WorkflowState,
    agent_name: str,
    budget: int,
    *,
    estimator: TokenEstimator = estimate_tokens,
) -> dict[str, Any]:
    """Return only the state fields ``agent_name`` needs, within ``budget`` tokens."""
    if budget < 0:
        raise ValueError("budget must be non-negative")
    fields = AGENT_CONTEXT_FIELDS.get(agent_name)
    if fields is None:
        raise ValueError(f"unknown agent: {agent_name}")

    dumped = state.model_dump(mode="json")
    context = {field: dumped[field] for field in fields}
    return trim_context(context, agent_name, budget, estimator)
