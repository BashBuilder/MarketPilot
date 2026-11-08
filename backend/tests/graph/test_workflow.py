"""End-to-end linear graph run against PostgreSQL with offline fakes."""

from collections.abc import Mapping
from pathlib import Path

from sqlalchemy import select

from app.core.config import Settings
from app.database.models import RunStatus, WorkflowCheckpoint
from app.database.repositories import AgentOutputRepository, CampaignRepository, RunRepository
from app.graph.workflow import LINEAR_NODES, run_workflow
from app.harness.checkpoints import HUMAN_GATE
from app.llm.fake import FakeLLMClient
from tests.graph.workflow_fixtures import generated_asset, settings
from tests.graph.workflow_outputs import brief, compliance, copy, direction, research, score


async def test_linear_pipeline_persists_every_handoff(db_session, tmp_path: Path) -> None:
    idea = "Create a hair-care campaign for adults aged 25 to 40"
    campaign = await CampaignRepository(db_session).create(idea)
    run = await RunRepository(db_session).create(campaign.id, RunStatus.RUNNING)
    resolved: Settings = settings(tmp_path)
    generated = await generated_asset(tmp_path)
    responses = [
        brief(),
        research(),
        copy(),
        direction(),
        compliance(generated.path),
        score(),
    ]
    events: list[tuple[str, Mapping[str, object]]] = []

    async def emit(name: str, data: Mapping[str, object]) -> None:
        events.append((name, data))

    result = await run_workflow(
        run.id,
        llm=FakeLLMClient(responses),
        settings=resolved,
        emit=emit,
        session=db_session,
    )

    assert result.status == "awaiting_approval"
    assert result.brief == responses[0]
    assert result.research == responses[1]
    assert result.copy == responses[2]
    assert result.direction == responses[3]
    assert result.assets is not None and result.assets.assets[0].uri == generated.path
    assert result.compliance == responses[4]
    assert result.score == responses[5]

    rows = await AgentOutputRepository(db_session).list_for_run(run.id)
    assert {row.agent for row in rows} == set(LINEAR_NODES)
    checkpoints = list(
        await db_session.scalars(
            select(WorkflowCheckpoint)
            .where(WorkflowCheckpoint.run_id == run.id)
            .order_by(WorkflowCheckpoint.step)
        )
    )
    assert [checkpoint.node for checkpoint in checkpoints] == [*LINEAR_NODES, HUMAN_GATE]
    names = [name for name, _ in events]
    assert [name for name in names if name != "tool_called"] == [
        name for _ in LINEAR_NODES for name in ("agent_started", "agent_handoff")
    ] + ["awaiting_approval"]
    assert "tool_called" in names
    assert events[-1][0] == "awaiting_approval"
    assert events[-1][1]["agent"] == "human"
    handoffs = [data for name, data in events if name == "agent_handoff"]
    assert handoffs[-1]["to"] == HUMAN_GATE
    stored_run = await RunRepository(db_session).get(run.id)
    assert stored_run is not None and stored_run.status == RunStatus.AWAITING_APPROVAL
