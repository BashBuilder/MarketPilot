import pytest
from pydantic import ValidationError

from app.agents.outputs.campaign_brief import CampaignBrief

VALID = {
    "product": "Lumen Hair Serum",
    "goal": "Increase trial among adults aged 25 to 40",
    "audience": "Busy professionals who want low-effort hair care",
    "tone": "Confident and calm",
    "channels": ["instagram", "search"],
    "constraints": ["No medical claims"],
}


def test_valid_campaign_brief() -> None:
    brief = CampaignBrief.model_validate(VALID)

    assert brief.product == "Lumen Hair Serum"
    assert brief.channels == ["instagram", "search"]


def test_empty_channels_are_rejected() -> None:
    with pytest.raises(ValidationError):
        CampaignBrief.model_validate({**VALID, "channels": []})
