"""Tests for the offline evaluation datasets."""

from app.evaluation.datasets import BAD_CLAIMS, GOLDEN_IDEAS


def test_hair_care_golden_idea_is_present() -> None:
    hair_care = next(item for item in GOLDEN_IDEAS if item.id == "hair-care-25-40")

    assert "fictional hair-care product" in hair_care.idea
    assert "aged 25 to 40" in hair_care.idea


def test_bad_claim_cases_are_present() -> None:
    assert [claim.id for claim in BAD_CLAIMS] == ["regrowth-guarantee", "miracle-cure"]
