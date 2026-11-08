import pytest
from pydantic import ValidationError

from app.agents.outputs.creative_direction import CreativeDirection

VALID = {
    "image_prompts": ["Soft daylight portrait of a woman with glossy hair"],
    "video_prompts": ["Slow pan across a bathroom shelf at sunrise"],
    "style_guide": "Warm neutral palette with a single teal accent",
    "composition": "Centered subject with generous negative space",
    "negative_prompts": ["harsh shadows", "cluttered background"],
}


def test_valid_creative_direction() -> None:
    direction = CreativeDirection.model_validate(VALID)

    assert direction.image_prompts[0].startswith("Soft daylight")
    assert direction.negative_prompts == ["harsh shadows", "cluttered background"]


def test_empty_image_prompts_are_rejected() -> None:
    with pytest.raises(ValidationError):
        CreativeDirection.model_validate({**VALID, "image_prompts": []})
