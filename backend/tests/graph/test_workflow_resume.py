"""Crash resume, approval continuation and gated-run idempotence."""

from collections.abc import Mapping
from pathlib import Path

from sqlalchemy import func, select

from app.database.models import RunStatus, WorkflowCheckpoint, WorkflowRun
from app.database.repositories import (
    AgentOutputRepository,
    ApprovalRepository,
    RunRepository,
)
from app.graph.state import WorkflowState
from app.graph.workflow import continue_run, run_workflow
from app.harness.checkpoints import save_checkpoint
from app.llm.fake import FakeLLMClient
from tests.graph.workflow_fixtures import generated_asset, settings
from tests.graph.workflow_outputs import brief, compliance, copy, direction, research, score
from tests.graph.workflow_test_helpers import collector, start_run, started_agents


async def gated_run(db_session, tmp_path: Path) -> WorkflowRun:
    run = await start_run(db_session)
    asset = await generated_asset(tmp_path)
    await run_workflow(
        run.id,
        llm=FakeLLMClient(
            [brief(), research(), copy(), direction(), compliance(asset.path), score()]
        ),
        settings=settings(tmp_path),
        session=db_session,
    )
    return run


async def test_crash_after_copywriter_resumes_at_creative_director(
    db_session, tmp_path: Path
) -> None:
    run = await start_run(db_session)
    state = WorkflowState(
        idea="Create a hair-care campaign for adults aged 25 to 40",
        brief=brief(),
        research=research(),
        copy=copy(),
        status="running",
    )
    for node in ("brief", "research", "copywriter"):
        await save_checkpoint(run.id, node, state, session=db_session)
    asset = await generated_asset(tmp_path)
    events, emit = collector()

    result = await run_workflow(
        run.id,
        llm=FakeLLMClient([direction(), compliance(asset.path), score()]),
        settings=settings(tmp_path),
        emit=emit,
        session=db_session,
    )

    assert result.status == "awaiting_approval"
    assert started_agents(events) == [
        "creative_director",
        "designer",
        "compliance",
        "reviewer",
    ]
    assert result.copy == copy()


async def test_awaiting_approval_run_does_not_rerun_any_node(db_session, tmp_path: Path) -> None:
    run = await gated_run(db_session, tmp_path)
    before = await db_session.scalar(
        select(func.count())
        .select_from(WorkflowCheckpoint)
        .where(WorkflowCheckpoint.run_id == run.id)
    )
    events: list[tuple[str, Mapping[str, object]]] = []

    async def emit(name: str, data: Mapping[str, object]) -> None:
        events.append((name, data))

    result = await run_workflow(
        run.id,
        llm=FakeLLMClient([]),
        settings=settings(tmp_path),
        emit=emit,
        session=db_session,
    )

    after = await db_session.scalar(
        select(func.count())
        .select_from(WorkflowCheckpoint)
        .where(WorkflowCheckpoint.run_id == run.id)
    )
    assert result.status == "awaiting_approval"
    assert events == []
    assert after == before


async def test_revise_from_target_reruns_only_that_node_forward(db_session, tmp_path: Path) -> None:
    run = await gated_run(db_session, tmp_path)
    asset = await generated_asset(tmp_path)
    events, emit = collector()

    result = await continue_run(
        run.id,
        "revise",
        comment="Rework the image",
        target_node="designer",
        llm=FakeLLMClient([compliance(asset.path), score()]),
        settings=settings(tmp_path),
        emit=emit,
        session=db_session,
    )

    assert result.status == "awaiting_approval"
    assert started_agents(events) == ["designer", "compliance", "reviewer"]
    assert result.brief == brief()
    decisions = await ApprovalRepository(db_session).list_for_run(run.id)
    assert decisions[-1].target_node == "designer"


async def test_approve_completes_and_emits_completed(db_session, tmp_path: Path) -> None:
    run = await gated_run(db_session, tmp_path)
    events, emit = collector()

    result = await continue_run(
        run.id,
        "approve",
        comment="Approved",
        emit=emit,
        session=db_session,
        settings=settings(tmp_path),
    )

    assert result.status == "completed"
    stored = await RunRepository(db_session).get(run.id)
    assert stored is not None and stored.status == RunStatus.COMPLETED
    assert [name for name, _ in events] == ["completed"]
    assert events[0][1]["version"] == 1
    rows = await AgentOutputRepository(db_session).list_for_run(run.id)
    assert len(rows) == 7

    again_events, again_emit = collector()
    again = await run_workflow(
        run.id,
        llm=FakeLLMClient([]),
        settings=settings(tmp_path),
        emit=again_emit,
        session=db_session,
    )
    assert again.status == "completed"
    assert again_events == []
