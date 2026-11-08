import pytest
from pydantic import ValidationError

from app.agents.outputs.ad_copy_set import AdCopySet

VALID = {
    "variants": [
        {
            "channel": "instagram",
            "headline": "Morning hair, handled",
            "description": "A lightweight serum that keeps frizz away all day.",
            "cta": "Shop the serum",
        }
    ]
}


def test_valid_ad_copy_set() -> None:
    copy = AdCopySet.model_validate(VALID)

    assert copy.variants[0].channel == "instagram"
    assert copy.variants[0].cta == "Shop the serum"


def test_empty_variants_are_rejected() -> None:
    with pytest.raises(ValidationError):
        AdCopySet.model_validate({**VALID, "variants": []})
