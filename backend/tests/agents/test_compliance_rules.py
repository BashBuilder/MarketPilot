"""Tests for the deterministic compliance rules."""

import pytest

from app.agents.compliance_rules import check_text


@pytest.mark.parametrize(
    "text",
    [
        "guaranteed hair regrowth in 7 days",
        "instant results after one wash",
        "see the before and after",
        "a miracle cure for dry hair",
        "100% effective",
        "a shampoo for minors",
        "a Nike campaign",
    ],
)
def test_bad_claims_hit_at_least_one_rule(text: str) -> None:
    assert check_text(text)


def test_clean_copy_has_no_hits() -> None:
    assert check_text("A lightweight serum that keeps frizz away all day.") == []
