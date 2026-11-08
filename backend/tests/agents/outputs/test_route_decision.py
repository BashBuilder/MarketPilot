import pytest
from pydantic import ValidationError

from app.agents.outputs.route_decision import RouteDecision

VALID = {
    "next_node": "copywriter",
    "reason": "Compliance failed, so rewrite the claims first",
    "escalate": False,
}


def test_valid_route_decision() -> None:
    decision = RouteDecision.model_validate(VALID)

    assert decision.next_node == "copywriter"
    assert decision.escalate is False


def test_unknown_node_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RouteDecision.model_validate({**VALID, "next_node": "marketing"})
