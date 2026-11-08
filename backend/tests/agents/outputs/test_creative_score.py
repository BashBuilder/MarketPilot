import pytest
from pydantic import ValidationError

from app.agents.outputs.creative_score import CreativeScore

DIMENSION = {"score": 7, "justification": "Clear and on brief"}

VALID = {
    "brief_alignment": {"score": 8, "justification": "Matches the stated goal"},
    "audience_fit": {"score": 7, "justification": "Speaks to the target group"},
    "copy_quality": {"score": 9, "justification": "Concise and specific"},
    "visual_quality": {"score": 8, "justification": "Polished, editorial framing"},
    "compliance_risk": {"score": 7, "justification": "Minor claim needs proof"},
    "total": 78.0,
}


def test_valid_creative_score() -> None:
    score = CreativeScore.model_validate(VALID)

    assert score.total == 78.0
    assert score.compliance_risk.score == 7


def test_mismatched_total_is_rejected() -> None:
    with pytest.raises(ValidationError, match="total must equal"):
        CreativeScore.model_validate({**VALID, "total": 80.0})


def test_dimension_above_ten_is_rejected() -> None:
    invalid = {**VALID, "copy_quality": {**DIMENSION, "score": 11}}

    with pytest.raises(ValidationError):
        CreativeScore.model_validate(invalid)
