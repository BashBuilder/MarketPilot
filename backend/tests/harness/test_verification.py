"""Tests for schema and semantic output verification."""

from app.agents.outputs.ad_copy_set import AdCopySet, AdVariant
from app.harness.verification import (
    MAX_HEADLINE_LENGTH,
    MIN_HEADLINE_LENGTH,
    CopySemanticValidator,
    SchemaValidator,
)

VALID_COPY = {
    "variants": [
        {
            "channel": "instagram",
            "headline": "Morning hair, handled",
            "description": "A lightweight serum that keeps frizz away all day.",
            "cta": "Shop the serum",
        }
    ]
}


def test_schema_validator_accepts_a_valid_model() -> None:
    assert SchemaValidator(AdCopySet).validate(AdCopySet.model_validate(VALID_COPY)) == []


def test_schema_validator_accepts_a_valid_raw_payload() -> None:
    assert SchemaValidator(AdCopySet).validate(VALID_COPY) == []


def test_schema_validator_reports_invalid_payloads() -> None:
    issues = SchemaValidator(AdCopySet).validate({"variants": []})

    assert len(issues) == 1
    assert issues[0].code == "schema"
    assert issues[0].path == "variants"
    assert issues[0].message


def test_copy_semantic_validator_accepts_valid_copy() -> None:
    assert CopySemanticValidator().validate(AdCopySet.model_validate(VALID_COPY)) == []


def test_copy_semantic_validator_rejects_an_empty_variant_list() -> None:
    copy = AdCopySet.model_construct(variants=[])

    issues = CopySemanticValidator().validate(copy)

    assert [issue.code for issue in issues] == ["copy.empty"]
    assert "no variants" in issues[0].message


def test_copy_semantic_validator_rejects_long_and_short_headlines() -> None:
    long_copy = AdCopySet.model_validate(
        {
            "variants": [
                {
                    **VALID_COPY["variants"][0],
                    "headline": "x" * (MAX_HEADLINE_LENGTH + 1),
                }
            ]
        }
    )
    short_variant = AdVariant.model_construct(
        channel="instagram",
        headline="abc",
        description="A valid description.",
        cta="Go",
    )
    short_copy = AdCopySet.model_construct(variants=[short_variant])

    long_issues = CopySemanticValidator().validate(long_copy)
    short_issues = CopySemanticValidator().validate(short_copy)

    assert [issue.code for issue in long_issues] == ["copy.headline"]
    assert f"maximum {MAX_HEADLINE_LENGTH}" in long_issues[0].message
    assert [issue.code for issue in short_issues] == ["copy.headline"]
    assert f"minimum {MIN_HEADLINE_LENGTH}" in short_issues[0].message


def test_copy_semantic_validator_reports_every_empty_field() -> None:
    variant = AdVariant.model_construct(channel="", headline="", description="", cta="")
    copy = AdCopySet.model_construct(variants=[variant])

    issues = CopySemanticValidator().validate(copy)

    assert [issue.code for issue in issues] == [
        "copy.headline",
        "copy.description",
        "copy.cta",
        "copy.channel",
    ]
