"""The bus is wired into the node wrapper, tools and verification loop."""

import uuid
from collections import deque
from pathlib import Path

from app.agents.outputs import AdCopySet, AdVariant
from app.events.bus import InMemoryEventBus
from app.events.emitter import bus_emitter
from app.graph.workflow import run_workflow
from app.harness.copy_validation import CopySemanticValidator
from app.harness.verification import Prompt, run_with_verification
from app.llm.fake import FakeLLMClient
from tests.graph.workflow_fixtures import generated_asset, settings
from tests.graph.workflow_outputs import brief, compliance, copy, direction, research, score
from tests.graph.workflow_test_helpers import start_run

EXPECTED = [
    "agent_started",
    "agent_handoff",
    "agent_started",
    "agent_handoff",
    "agent_started",
    "agent_handoff",
    "agent_started",
    "agent_handoff",
    "agent_started",
    "agent_handoff",
    "agent_started",
    "agent_handoff",
    "agent_started",
    "agent_handoff",
    "awaiting_approval",
]


async def test_full_run_events_arrive_in_pipeline_order(db_session, tmp_path: Path) -> None:
    bus = InMemoryEventBus()
    run = await start_run(db_session)
    asset = await generated_asset(tmp_path)
    responses = [brief(), research(), copy(), direction(), compliance(asset.path), score()]

    await run_workflow(
        run.id,
        llm=FakeLLMClient(responses),
        settings=settings(tmp_path),
        emit=bus_emitter(bus, run.id),
        session=db_session,
    )

    events = await bus.read(run.id, None)
    names = [event["event"] for event in events]
    without_tools = [name for name in names if name != "tool_called"]
    agents = [event["data"]["agent"] for event in events if event["event"] == "agent_started"]
    tool_event = next(event for event in events if event["event"] == "tool_called")

    assert without_tools == EXPECTED
    assert agents == [
        "brief",
        "research",
        "copywriter",
        "creative_director",
        "designer",
        "compliance",
        "reviewer",
    ]
    assert events[-1]["data"]["agent"] == "human"
    assert events[-1]["data"]["version"] == 1
    assert tool_event["data"]["agent"] == "research"
    assert tool_event["data"]["status"] == "success"
    assert tool_event["data"]["duration_ms"] >= 0
    assert tool_event["data"]["run_id"] == str(run.id)


def valid_copy() -> AdCopySet:
    variant = AdVariant(
        channel="instagram",
        headline="Morning hair, handled",
        description="A lightweight serum for all-day smoothness.",
        cta="Shop the serum",
    )
    return AdCopySet(variants=[variant])


def invalid_copy() -> AdCopySet:
    variant = AdVariant.model_construct(
        channel="instagram",
        headline="abc",
        description="A lightweight serum for all-day smoothness.",
        cta="Shop the serum",
    )
    return AdCopySet.model_construct(variants=[variant])


async def test_forced_validation_failure_publishes_failure_then_retry() -> None:
    bus = InMemoryEventBus()
    run_id = uuid.uuid4()
    remaining = deque([invalid_copy(), valid_copy()])

    async def step(messages: Prompt) -> AdCopySet:
        return remaining.popleft()

    await run_with_verification(
        step,
        prompt=[{"role": "system", "content": "Write copy."}],
        agent="copywriter",
        validators=[CopySemanticValidator()],
        on_event=bus_emitter(bus, run_id),
        max_attempts=3,
    )

    events = await bus.read(run_id, None)

    assert [event["event"] for event in events] == ["validation_failed", "retrying"]
    assert events[0]["data"]["agent"] == "copywriter"
    assert "headline" in events[0]["data"]["reason"]
    assert events[1]["data"]["attempt"] == 2
    assert events[1]["data"]["max_attempts"] == 3
    assert events[0]["data"]["run_id"] == str(run_id)
