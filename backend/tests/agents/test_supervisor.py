"""Tests for the deterministic Supervisor routing rules."""

from app.agents.outputs import ComplianceReport
from app.agents.supervisor import AUTO_LOOP_COUNTER, route
from tests.agents.supervisor_fixtures import failure, score, settings
from tests.harness.context_fixtures import make_state


def test_retry_exhaustion_escalates_to_the_human() -> None:
    state = make_state()
    state.errors = ["retry_exhausted: copywriter exhausted 3 attempts"]

    decision = route(state, settings=settings())

    assert decision.next_node == "human"
    assert decision.escalate is True


def test_failed_copy_item_routes_to_the_copywriter() -> None:
    state = make_state()
    state.compliance = ComplianceReport(items=[failure("copy:Instagram - no claims")])

    decision = route(state, settings=settings())

    assert decision.next_node == "copywriter"
    assert decision.escalate is False


def test_failed_asset_item_routes_to_the_designer() -> None:
    state = make_state()
    state.compliance = ComplianceReport(items=[failure("asset:assets/hero.png - no brands")])

    assert route(state, settings=settings()).next_node == "designer"


def test_retry_exhaustion_beats_compliance_and_score_rules() -> None:
    state = make_state()
    state.errors = ["retry_exhausted: reviewer"]
    state.compliance = ComplianceReport(items=[failure("copy:Instagram - no claims")])
    state.score = score(copy_quality=1)

    decision = route(state, settings=settings())

    assert decision.next_node == "human"
    assert decision.escalate is True


def test_low_score_routes_to_the_weakest_node_and_counts_the_loop() -> None:
    state = make_state()
    state.score = score(copy_quality=2)

    decision = route(state, settings=settings())

    assert decision.next_node == "copywriter"
    assert state.retry_counters[AUTO_LOOP_COUNTER] == 1


def test_third_low_score_goes_to_the_human_instead_of_looping() -> None:
    state = make_state()
    state.score = score(copy_quality=2)
    config = settings(max_loops=2)

    assert route(state, settings=config).next_node == "copywriter"
    assert route(state, settings=config).next_node == "copywriter"
    assert route(state, settings=config).next_node == "human"
    assert state.retry_counters[AUTO_LOOP_COUNTER] == 2


def test_score_at_the_threshold_goes_to_the_human_without_looping() -> None:
    state = make_state()
    state.score = score(
        brief_alignment=7,
        audience_fit=7,
        copy_quality=7,
        visual_quality=7,
        compliance_risk=7,
    )

    decision = route(state, settings=settings(threshold=70))

    assert decision.next_node == "human"
    assert AUTO_LOOP_COUNTER not in state.retry_counters


def test_healthy_package_goes_to_the_human_gate() -> None:
    state = make_state()
    state.score = score()

    decision = route(state, settings=settings())

    assert decision.next_node == "human"
    assert decision.escalate is False
