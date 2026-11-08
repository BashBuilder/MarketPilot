import pytest
from pydantic import ValidationError

from app.agents.outputs.compliance_report import ComplianceReport

VALID = {
    "items": [
        {
            "check": "Substantiate performance claims",
            "passed": False,
            "reason": "The headline claims all-day hold without evidence",
        },
        {
            "check": "No medical claims",
            "passed": True,
            "reason": "Copy avoids treatment and cure language",
        },
    ]
}


def test_valid_compliance_report() -> None:
    report = ComplianceReport.model_validate(VALID)

    assert report.items[0].passed is False
    assert report.items[1].passed is True


def test_empty_items_are_rejected() -> None:
    with pytest.raises(ValidationError):
        ComplianceReport.model_validate({**VALID, "items": []})
