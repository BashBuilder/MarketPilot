"""Supervisor-driven routing for compliance, review and loop checkpoints."""

from app.agents.supervisor import route
from app.graph.node_runtime import NodeRuntime
from app.graph.state import WorkflowState
from app.harness.checkpoints import save_checkpoint

LINEAR_NODES: tuple[str, ...] = (
    "brief",
    "research",
    "copywriter",
    "creative_director",
    "designer",
    "compliance",
    "reviewer",
)
HUMAN_GATE = "human"
SUPERVISOR_NODE = "supervisor"


async def route_compliance(state: WorkflowState, runtime: NodeRuntime) -> WorkflowState:
    """Loop failed compliance back to copy/design, otherwise continue to review."""
    decision = route(state, settings=runtime.settings)
    if _escalated(state, decision.escalate):
        return _target(state, HUMAN_GATE)
    if decision.next_node in {"copywriter", "designer"}:
        return await _persist_loop(state, runtime, decision.next_node)
    return _target(state, HUMAN_GATE if _failed_compliance(state) else "reviewer")


async def route_reviewer(state: WorkflowState, runtime: NodeRuntime) -> WorkflowState:
    """Loop a low score to its weakest node, otherwise open the human gate."""
    decision = route(state, settings=runtime.settings)
    if _escalated(state, decision.escalate):
        return _target(state, HUMAN_GATE)
    if decision.next_node in LINEAR_NODES:
        return await _persist_loop(state, runtime, decision.next_node)
    return _target(state, HUMAN_GATE)


def target_from_state(state: WorkflowState) -> str:
    """Return the concrete graph target recorded by a routing node."""
    if state.target_node == HUMAN_GATE or state.target_node is None:
        return HUMAN_GATE
    if state.target_node in LINEAR_NODES:
        return state.target_node
    return HUMAN_GATE


def escalation_target(state: WorkflowState, following: str) -> str:
    """Short-circuit escalated runs to the human gate from any node."""
    return HUMAN_GATE if state.status == "escalated" else following


def _escalated(state: WorkflowState, decision_escalates: bool) -> bool:
    return state.status == "escalated" or decision_escalates


def _failed_compliance(state: WorkflowState) -> bool:
    return state.compliance is not None and any(not item.passed for item in state.compliance.items)


def _target(state: WorkflowState, target: str) -> WorkflowState:
    return state.model_copy(update={"target_node": target})


async def _persist_loop(
    state: WorkflowState,
    runtime: NodeRuntime,
    target: str,
) -> WorkflowState:
    """Checkpoint the supervisor's increment before the loop target reruns."""
    updated = state.model_copy(
        update={
            "target_node": target,
            "retry_counters": dict(state.retry_counters),
            # The score is stale until the Reviewer reruns after this loop.
            "score": None,
        }
    )
    await save_checkpoint(runtime.run_id, SUPERVISOR_NODE, updated, session=runtime.session)
    return updated
