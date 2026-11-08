"""Automatic compliance/score loops and escalation against PostgreSQL."""

from pathlib import Path

from app.agents.base import BaseAgent
from app.agents.outputs import CampaignBrief
from app.agents.supervisor import AUTO_LOOP_COUNTER
from app.graph.state import WorkflowState
from app.graph.workflow import build_agents, run_workflow
from app.harness.checkpoints import load_latest_checkpoint
from app.harness.issues import ValidationIssue
from app.llm.fake import FakeLLMClient
from tests.graph.workflow_fixtures import generated_asset, settings
from tests.graph.workflow_outputs import brief, compliance, copy, direction, research, score
from tests.graph.workflow_test_helpers import collector, start_run, started_agents


class AlwaysInvalid:
    def validate(self, output: CampaignBrief, /) -> list[ValidationIssue]:
        return [ValidationIssue("goal", "forced retry exhaustion")]


async def test_failed_copy_loops_to_copywriter_once_then_passes(db_session, tmp_path: Path) -> None:
    run = await start_run(db_session)
    asset = await generated_asset(tmp_path)
    responses = [
        brief(),
        research(),
        copy(),
        direction(),
        compliance(asset.path, copy_passed=False),
        copy(),
        direction(),
        compliance(asset.path),
        score(),
    ]
    events, emit = collector()

    result = await run_workflow(
        run.id,
        llm=FakeLLMClient(responses),
        settings=settings(tmp_path),
        emit=emit,
        session=db_session,
    )

    assert result.status == "awaiting_approval"
    agents = started_agents(events)
    assert agents.count("copywriter") == 2
    assert agents.count("creative_director") == 2
    assert agents[-1] == "reviewer"
    latest = await load_latest_checkpoint(run.id, session=db_session)
    assert latest is not None
    assert latest.retry_counters[AUTO_LOOP_COUNTER] == 1


async def test_low_score_loops_to_the_weakest_node_and_counter_reloads(
    db_session, tmp_path: Path
) -> None:
    run = await start_run(db_session)
    asset = await generated_asset(tmp_path)
    responses = [
        brief(),
        research(),
        copy(),
        direction(),
        compliance(asset.path),
        score(copy_quality=2),
        copy(),
        direction(),
        compliance(asset.path),
        score(),
    ]
    events, emit = collector()

    result = await run_workflow(
        run.id,
        llm=FakeLLMClient(responses),
        settings=settings(tmp_path),
        emit=emit,
        session=db_session,
    )

    assert result.status == "awaiting_approval"
    assert started_agents(events).count("copywriter") == 2
    latest = await load_latest_checkpoint(run.id, session=db_session)
    assert latest is not None
    assert latest.retry_counters[AUTO_LOOP_COUNTER] == 1


async def test_third_low_score_goes_to_the_human_gate(db_session, tmp_path: Path) -> None:
    run = await start_run(db_session)
    asset = await generated_asset(tmp_path)
    loop = [copy(), direction(), compliance(asset.path), score(copy_quality=2)]
    responses = [brief(), research(), *loop, *loop, *loop]
    events, emit = collector()

    result = await run_workflow(
        run.id,
        llm=FakeLLMClient(responses),
        settings=settings(tmp_path),
        emit=emit,
        session=db_session,
    )

    assert result.status == "awaiting_approval"
    agents = started_agents(events)
    assert agents.count("copywriter") == 3
    assert agents.count("reviewer") == 3
    latest = await load_latest_checkpoint(run.id, session=db_session)
    assert latest is not None
    assert latest.retry_counters[AUTO_LOOP_COUNTER] == 2


async def test_retry_exhausted_escalates_straight_to_the_gate(db_session, tmp_path: Path) -> None:
    run = await start_run(db_session)
    resolved = settings(tmp_path, retry_attempts=2)
    agents = build_agents(resolved)
    agents["brief"] = BaseAgent(
        name="brief",
        output_model=CampaignBrief,
        validators=[AlwaysInvalid()],
        settings=resolved,
    )
    events, emit = collector()

    result = await run_workflow(
        run.id,
        llm=FakeLLMClient([brief(), brief()]),
        agents=agents,
        settings=resolved,
        emit=emit,
        session=db_session,
    )

    assert isinstance(result, WorkflowState)
    assert result.status == "awaiting_approval"
    assert started_agents(events) == ["brief"]
    assert "error" in [name for name, _ in events]
    latest = await load_latest_checkpoint(run.id, session=db_session)
    assert latest is not None and "brief:" in latest.errors[0]
