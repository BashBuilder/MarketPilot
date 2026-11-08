import pytest
from pydantic import ValidationError

from app.agents.outputs.audience_research import AudienceResearch

VALID = {
    "segments": [
        {
            "name": "Busy professionals",
            "description": "Adults aged 25 to 40 with limited morning time",
        }
    ],
    "pain_points": ["Frizz returns by midday"],
    "messaging_angles": ["Low-effort confidence"],
    "sources": [
        {
            "title": "Hair care market report",
            "url": "https://example.com/report",
        }
    ],
}


def test_valid_audience_research() -> None:
    research = AudienceResearch.model_validate(VALID)

    assert research.segments[0].name == "Busy professionals"
    assert str(research.sources[0].url) == "https://example.com/report"


def test_empty_segments_are_rejected() -> None:
    with pytest.raises(ValidationError):
        AudienceResearch.model_validate({**VALID, "segments": []})
