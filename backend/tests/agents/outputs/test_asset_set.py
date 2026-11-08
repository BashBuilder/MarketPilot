import pytest
from pydantic import ValidationError

from app.agents.outputs.asset_set import AssetSet

VALID = {
    "assets": [
        {
            "uri": "assets/campaigns/serum-hero.png",
            "checksum": "a" * 64,
            "model": "fake-sdxl",
            "seed": 9223372036854775807,
            "prompt": "Soft daylight portrait of a woman with glossy hair",
        }
    ]
}


def test_valid_asset_set() -> None:
    assets = AssetSet.model_validate(VALID)

    assert assets.assets[0].seed == 9223372036854775807
    assert len(assets.assets[0].checksum) == 64


def test_invalid_checksum_is_rejected() -> None:
    invalid = {
        **VALID,
        "assets": [{**VALID["assets"][0], "checksum": "not-a-checksum"}],
    }

    with pytest.raises(ValidationError):
        AssetSet.model_validate(invalid)
