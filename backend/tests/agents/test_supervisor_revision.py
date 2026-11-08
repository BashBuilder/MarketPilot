"""Tests for human revise decisions routed by the Supervisor."""

from app.agents.supervisor import route_revision
from tests.agents.supervisor_fixtures import score
from tests.harness.context_fixtures import make_state


def test_revise_uses_the_given_target_node() -> None:
    decision = route_revision(make_state(), "designer")

    assert decision.next_node == "designer"


def test_revise_without_target_uses_the_weakest_node() -> None:
    state = make_state()
    state.score = score(audience_fit=2)

    assert route_revision(state).next_node == "research"


def test_revise_without_a_score_goes_to_the_human() -> None:
    state = make_state()
    state.score = None

    assert route_revision(state).next_node == "human"
