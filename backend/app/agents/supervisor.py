"""Deterministic Supervisor routing; no LLM and no provider calls."""

from collections.abc import Sequence
from typing import Final

from app.agents.outputs import ComplianceItem, PipelineNode, RouteDecision
from app.agents.scoring import weakest_node
from app.core.config import Settings, get_settings
from app.graph.state import WorkflowState

AUTO_LOOP_COUNTER: Final = "auto_loop"
RETRY_EXHAUSTED_MARKERS: Final = ("retry_exhausted", "retryexhausted")


def route(state: WorkflowState, *, settings: Settings | None = None) -> RouteDecision:
    """Return the next automatic routing decision.

    The decision is deterministic and LLM-free. A low-score loop advances the
    shared auto-loop counter on ``state`` so the caller can checkpoint it.
    """
    if _retry_exhausted(state):
        return RouteDecision(
            next_node="human",
            reason="A retry was exhausted; escalate to the human approval gate.",
            escalate=True,
        )

    failed = _failed_compliance_items(state)
    if failed and _has_copy_failure(failed):
        return RouteDecision(
            next_node="copywriter",
            reason="Compliance failed for copy; rerun the copywriter before the gate.",
            escalate=False,
        )
    if failed:
        return RouteDecision(
            next_node="designer",
            reason="Compliance failed outside copy; rerun the designer before the gate.",
            escalate=False,
        )

    resolved = settings or get_settings()
    score = state.score
    if score is not None and score.total < resolved.score_threshold:
        loops = state.retry_counters.get(AUTO_LOOP_COUNTER, 0)
        if loops < resolved.max_auto_loops:
            state.retry_counters[AUTO_LOOP_COUNTER] = loops + 1
            node = weakest_node(score)
            return RouteDecision(
                next_node=node,
                reason=(
                    f"Score {score.total:.2f} is below {resolved.score_threshold}; "
                    f"rerun the weakest node {node} (auto loop {loops + 1} of "
                    f"{resolved.max_auto_loops})."
                ),
                escalate=False,
            )

    return RouteDecision(
        next_node="human",
        reason="No blocked checks or score loops remain; open the human approval gate.",
        escalate=False,
    )


def route_revision(
    state: WorkflowState,
    target_node: PipelineNode | None = None,
) -> RouteDecision:
    """Route a human revise decision to its target or the weakest node."""
    if target_node is not None:
        return RouteDecision(
            next_node=target_node,
            reason=f"The human asked to revise {target_node}.",
            escalate=False,
        )

    if state.score is not None:
        node = weakest_node(state.score)
        return RouteDecision(
            next_node=node,
            reason=(
                f"The human asked for a revision without a target; rerun the weakest node {node}."
            ),
            escalate=False,
        )

    return RouteDecision(
        next_node="human",
        reason="A revision was requested but no score exists to pick a weakest node.",
        escalate=False,
    )


def _retry_exhausted(state: WorkflowState) -> bool:
    return any(
        marker in error.casefold() for error in state.errors for marker in RETRY_EXHAUSTED_MARKERS
    )


def _failed_compliance_items(state: WorkflowState) -> list[ComplianceItem]:
    if state.compliance is None:
        return []
    return [item for item in state.compliance.items if not item.passed]


def _has_copy_failure(items: Sequence[ComplianceItem]) -> bool:
    return any(item.check.casefold().startswith("copy") for item in items)
