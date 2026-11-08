"""LangGraph wiring for the seven-agent pipeline with routing loops."""

from collections.abc import Awaitable, Callable, Hashable, Mapping

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.brief import BriefAgent
from app.agents.compliance import ComplianceAgent
from app.agents.copywriter import CopywriterAgent
from app.agents.creative_director import CreativeDirectorAgent
from app.agents.designer import DesignerAgent
from app.agents.research import ResearchAgent
from app.agents.reviewer import ReviewerAgent
from app.core.config import Settings, get_settings
from app.database.repositories import RunRepository, VersionRepository
from app.graph.node_runtime import Agent, NodeRuntime, event_data
from app.graph.nodes import Node, make_node
from app.graph.routing import (
    HUMAN_GATE,
    LINEAR_NODES,
    escalation_target,
    route_compliance,
    route_reviewer,
    target_from_state,
)
from app.graph.runner import continue_run, run_pipeline, run_workflow
from app.graph.state import WorkflowState
from app.harness.checkpoints import request_approval

__all__ = ["build_agents", "build_workflow", "continue_run", "run_pipeline", "run_workflow"]

APPROVAL_NODE = "request_approval"
COMPLIANCE_ROUTER = "route_compliance"
REVIEWER_ROUTER = "route_reviewer"

Graph = CompiledStateGraph[WorkflowState, None, WorkflowState, WorkflowState]
Router = Callable[[WorkflowState, NodeRuntime], Awaitable[WorkflowState]]
Path = Callable[[WorkflowState], str]
_TARGETS: dict[Hashable, str] = {
    **{node: node for node in LINEAR_NODES},
    HUMAN_GATE: APPROVAL_NODE,
}


def build_agents(settings: Settings | None = None) -> dict[str, Agent]:
    """Construct the default agent set for one workflow graph."""
    resolved = settings or get_settings()
    return {
        "brief": BriefAgent(settings=resolved),
        "research": ResearchAgent(settings=resolved),
        "copywriter": CopywriterAgent(settings=resolved),
        "creative_director": CreativeDirectorAgent(settings=resolved),
        "designer": DesignerAgent(settings=resolved),
        "compliance": ComplianceAgent(settings=resolved),
        "reviewer": ReviewerAgent(settings=resolved),
    }


def build_workflow(
    runtime: NodeRuntime,
    agents: Mapping[str, Agent] | None = None,
) -> Graph:
    """Compile the pipeline with compliance and score loops."""
    resolved = dict(agents) if agents is not None else build_agents()
    graph = StateGraph(WorkflowState)
    for name in LINEAR_NODES:
        graph.add_node(name, make_node(resolved[name], runtime))
    graph.add_node(COMPLIANCE_ROUTER, _router_node(route_compliance, runtime))
    graph.add_node(REVIEWER_ROUTER, _router_node(route_reviewer, runtime))
    graph.add_node(APPROVAL_NODE, _approval_node(runtime))

    graph.add_conditional_edges(START, _entry_target, _TARGETS)
    for index, name in enumerate(LINEAR_NODES):
        if name == "compliance":
            graph.add_edge(name, COMPLIANCE_ROUTER)
        elif name == "reviewer":
            graph.add_edge(name, REVIEWER_ROUTER)
        else:
            following = LINEAR_NODES[index + 1]
            graph.add_conditional_edges(
                name,
                _linear_route(following),
                {following: following, HUMAN_GATE: APPROVAL_NODE},
            )
    graph.add_conditional_edges(COMPLIANCE_ROUTER, target_from_state, _TARGETS)
    graph.add_conditional_edges(REVIEWER_ROUTER, target_from_state, _TARGETS)
    graph.add_edge(APPROVAL_NODE, END)
    return graph.compile()


def _entry_target(state: WorkflowState) -> str:
    if state.target_node in LINEAR_NODES:
        return str(state.target_node)
    return HUMAN_GATE if state.target_node == HUMAN_GATE else LINEAR_NODES[0]


def _linear_route(following: str) -> Path:
    def choose(state: WorkflowState) -> str:
        return escalation_target(state, following)

    return choose


def _router_node(router: Router, runtime: NodeRuntime) -> Node:
    async def node(state: WorkflowState) -> WorkflowState:
        return await router(state, runtime)

    return node


def _approval_node(runtime: NodeRuntime) -> Node:
    async def request_human(state: WorkflowState) -> WorkflowState:
        await request_approval(runtime.run_id, session=runtime.session)
        run = await RunRepository(runtime.session).get(runtime.run_id)
        version = None
        if run is not None:
            version = await VersionRepository(runtime.session).latest(run.campaign_id)
        await runtime.emit(
            "awaiting_approval",
            event_data(
                runtime,
                "human",
                {"version": version.version if version is not None else 1},
            ),
        )
        return state.model_copy(update={"status": "awaiting_approval"})

    return request_human
