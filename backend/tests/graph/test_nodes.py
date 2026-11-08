"""Graph node factory: merge, persist, checkpoint and event ordering."""

from collections.abc import Mapping

from app.agents.base import BaseAgent
from app.agents.outputs import CampaignBrief
from app.core.config import Settings
from app.database.repositories import AgentOutputRepository, CheckpointRepository
from app.graph.node_runtime import NodeRuntime
from app.graph.nodes import make_node
from app.graph.state import WorkflowState
from app.harness.issues import ValidationIssue
from app.llm.fake import FakeLLMClient
from tests.harness.checkpoint_fixtures import make_run


def settings(*, attempts: int = 2) -> Settings:
    return Settings(
        deepseek_api_key="test-key",
        database_url="postgresql+asyncpg://user:pass@localhost:5432/marketpilot",
        redis_url="redis://localhost:6379/0",
        retry_max_attempts=attempts,
        _env_file=None,
    )


def brief() -> CampaignBrief:
    return CampaignBrief(
        product="HydraSilk Shampoo",
        goal="Launch a hydrating shampoo for adults with dry hair.",
        audience="Adults aged 25 to 40 who style their hair daily.",
        tone="Warm and confident",
        channels=["Instagram", "Email"],
        constraints=["No medical claims"],
    )


class AlwaysInvalid:
    def validate(self, output: CampaignBrief, /) -> list[ValidationIssue]:
        return [ValidationIssue("goal", "goal must be rejected for this test")]


def event_collector() -> tuple[list[tuple[str, Mapping[str, object]]], object]:
    events: list[tuple[str, Mapping[str, object]]] = []

    async def emit(name: str, data: Mapping[str, object]) -> None:
        events.append((name, data))

    return events, emit


def runtime(run_id, session, llm, emit) -> NodeRuntime:  # type: ignore[no-untyped-def]
    return NodeRuntime(
        run_id=run_id,
        session=session,
        llm=llm,
        emit=emit,
        tools_for=lambda _: None,
    )


async def test_node_merges_output_persists_row_and_checkpoint(db_session) -> None:
    run = await make_run(db_session)
    output = brief()
    events, emit = event_collector()
    node = make_node(
        BaseAgent(name="brief", output_model=CampaignBrief, settings=settings()),
        runtime(run.id, db_session, FakeLLMClient([output]), emit),
    )

    updated = await node(WorkflowState(idea="Hair-care campaign"))

    assert updated.brief == output
    assert updated.status == "running"
    rows = await AgentOutputRepository(db_session).list_for_run(run.id)
    assert [(row.agent, row.output) for row in rows] == [("brief", output.model_dump(mode="json"))]
    checkpoint = await CheckpointRepository(db_session).latest_for_run(run.id)
    assert checkpoint is not None
    assert checkpoint.node == "brief"
    assert checkpoint.state["brief"] == output.model_dump(mode="json")
    assert [name for name, _ in events] == ["agent_started", "agent_handoff"]
    assert events[1][1]["to"] == "research"


async def test_exhausted_retries_escalate_and_emit_error(db_session) -> None:
    run = await make_run(db_session)
    events, emit = event_collector()
    agent = BaseAgent(
        name="brief",
        output_model=CampaignBrief,
        validators=[AlwaysInvalid()],
        settings=settings(attempts=2),
    )
    node = make_node(agent, runtime(run.id, db_session, FakeLLMClient([brief(), brief()]), emit))

    result = await node(WorkflowState(idea="Hair-care campaign"))

    assert result.status == "escalated"
    assert [name for name, _ in events][-1] == "error"
    assert "agent_handoff" not in [name for name, _ in events]
    assert await AgentOutputRepository(db_session).list_for_run(run.id) == []
    checkpoint = await CheckpointRepository(db_session).latest_for_run(run.id)
    assert checkpoint is not None
    assert checkpoint.node == "brief"
    assert checkpoint.state["status"] == "escalated"
    assert "brief:" in checkpoint.state["errors"][0]
