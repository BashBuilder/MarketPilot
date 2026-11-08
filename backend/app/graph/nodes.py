"""Node factory: run one agent, persist its handoff, and emit its events."""

from collections.abc import Awaitable
from typing import Protocol

from app.core.errors import RetryExhausted
from app.database.repositories import AgentOutputRepository
from app.graph.node_runtime import Agent, NodeRuntime, event_data
from app.graph.state import WorkflowState
from app.harness.checkpoints import save_checkpoint

STATE_FIELDS: dict[str, str] = {
    "brief": "brief",
    "research": "research",
    "copywriter": "copy",
    "creative_director": "direction",
    "designer": "assets",
    "compliance": "compliance",
    "reviewer": "score",
}

HANDOFF_TARGETS: dict[str, str] = {
    "brief": "research",
    "research": "copywriter",
    "copywriter": "creative_director",
    "creative_director": "designer",
    "designer": "compliance",
    "compliance": "reviewer",
    "reviewer": "human",
}


class Node(Protocol):
    """Async graph node: state in, updated state out."""

    def __call__(self, state: WorkflowState) -> Awaitable[WorkflowState]:
        """Run the node."""
        ...


def make_node(agent: Agent, runtime: NodeRuntime) -> Node:
    """Return a graph node that turns one agent run into a durable handoff."""

    async def node(state: WorkflowState) -> WorkflowState:
        await runtime.emit("agent_started", event_data(runtime, agent.name))
        try:
            # The agent builds its mapped context and runs the verified harness loop.
            output = await agent.run(
                state, runtime.llm, runtime.emit, runtime.tools_for(agent.name)
            )
        except RetryExhausted as error:
            return await _escalate(state, agent.name, error, runtime)

        validated = type(output).model_validate(output)
        updated = _merge(state, agent.name, validated)
        await AgentOutputRepository(runtime.session).create(
            run_id=runtime.run_id,
            agent=agent.name,
            output=validated.model_dump(mode="json"),
        )
        await save_checkpoint(runtime.run_id, agent.name, updated, session=runtime.session)
        await runtime.emit(
            "agent_handoff",
            event_data(
                runtime,
                agent.name,
                {"from": agent.name, "to": HANDOFF_TARGETS[agent.name]},
            ),
        )
        return updated

    return node


def _merge(state: WorkflowState, agent: str, output: object) -> WorkflowState:
    field = STATE_FIELDS[agent]
    return state.model_copy(update={field: output, "status": "running"})


async def _escalate(
    state: WorkflowState,
    agent: str,
    error: RetryExhausted,
    runtime: NodeRuntime,
) -> WorkflowState:
    updated = state.model_copy(
        update={
            "status": "escalated",
            "errors": [*state.errors, f"{agent}: {error.message}"],
        }
    )
    await save_checkpoint(runtime.run_id, agent, updated, session=runtime.session)
    await runtime.emit(
        "error",
        event_data(
            runtime,
            agent,
            {"message": str(error), "recoverable": False, "attempts": error.attempts},
        ),
    )
    return updated
