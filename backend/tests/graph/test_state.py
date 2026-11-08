import pytest

from app.agents.outputs import CampaignBrief
from app.core.errors import ValidationFailure
from app.graph.state import WorkflowState, parse_agent_output

STATE = {
    "idea": "Create a hair-care campaign for adults aged 25 to 40",
    "brief": {
        "product": "Lumen Hair Serum",
        "goal": "Increase trial among busy professionals",
        "audience": "Adults aged 25 to 40",
        "tone": "Confident and calm",
        "channels": ["instagram"],
        "constraints": ["No medical claims"],
    },
    "research": {
        "segments": [
            {
                "name": "Professionals",
                "description": "Busy adults with limited time",
            }
        ],
        "pain_points": ["Frizz returns by midday"],
        "messaging_angles": ["Effortless confidence"],
        "sources": [{"title": "Market report", "url": "https://example.com/report"}],
    },
    "copy": {
        "variants": [
            {
                "channel": "instagram",
                "headline": "Morning hair, handled",
                "description": "A lightweight serum for all-day smoothness.",
                "cta": "Shop the serum",
            }
        ]
    },
    "direction": {
        "image_prompts": ["soft daylight portrait"],
        "video_prompts": ["slow shelf pan"],
        "style_guide": "Warm neutral palette",
        "composition": "Centered subject",
        "negative_prompts": ["harsh shadows"],
    },
    "assets": {
        "assets": [
            {
                "uri": "assets/hero.png",
                "checksum": "a" * 64,
                "model": "fake",
                "seed": 7,
                "prompt": "soft daylight portrait",
            }
        ]
    },
    "compliance": {
        "items": [
            {
                "check": "No medical claims",
                "passed": True,
                "reason": "Copy avoids cure language",
            }
        ]
    },
    "score": {
        "brief_alignment": {"score": 6, "justification": "Consistent with brief"},
        "audience_fit": {"score": 6, "justification": "Consistent with brief"},
        "copy_quality": {"score": 6, "justification": "Consistent with brief"},
        "visual_quality": {"score": 6, "justification": "Consistent with brief"},
        "compliance_risk": {"score": 6, "justification": "Consistent with brief"},
        "total": 60.0,
    },
    "target_node": "copywriter",
    "revision_feedback": "Tighten the call to action",
    "versions": [1],
    "status": "awaiting_approval",
    "retry_counters": {"copywriter": 1},
    "errors": ["compliance: claim needs evidence"],
}


def test_state_round_trips_through_json() -> None:
    state = WorkflowState.model_validate(STATE)

    restored = WorkflowState.model_validate_json(state.model_dump_json())

    assert restored == state
    assert restored.copy is not None
    assert restored.copy.variants[0].cta == "Shop the serum"


def test_invalid_agent_output_raises_validation_failure() -> None:
    invalid = {**STATE["brief"], "channels": []}

    with pytest.raises(ValidationFailure) as excinfo:
        parse_agent_output(CampaignBrief, invalid)

    assert excinfo.value.agent == "CampaignBrief"
    assert "validation" in str(excinfo.value)
