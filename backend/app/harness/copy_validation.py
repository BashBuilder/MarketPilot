"""Semantic checks for advertising copy."""

from app.agents.outputs.ad_copy_set import AdCopySet
from app.harness.issues import ValidationIssue

MIN_HEADLINE_LENGTH = 5
MAX_HEADLINE_LENGTH = 90


class CopySemanticValidator:
    """Checks that ad copy is usable, beyond what the schema guarantees."""

    def validate(self, output: AdCopySet, /) -> list[ValidationIssue]:
        if not output.variants:
            return [ValidationIssue("copy.empty", "copy contains no variants")]

        issues: list[ValidationIssue] = []
        for index, variant in enumerate(output.variants, start=1):
            label = f"variant {index} ({variant.channel or 'unknown channel'})"
            headline_length = len(variant.headline.strip())
            if headline_length == 0:
                issues.append(ValidationIssue("copy.headline", f"{label}: headline is empty"))
            elif headline_length < MIN_HEADLINE_LENGTH:
                issues.append(
                    ValidationIssue(
                        "copy.headline",
                        f"{label}: headline is {headline_length} characters "
                        f"(minimum {MIN_HEADLINE_LENGTH})",
                    )
                )
            elif headline_length > MAX_HEADLINE_LENGTH:
                issues.append(
                    ValidationIssue(
                        "copy.headline",
                        f"{label}: headline is {headline_length} characters "
                        f"(maximum {MAX_HEADLINE_LENGTH})",
                    )
                )
            if not variant.description.strip():
                issues.append(ValidationIssue("copy.description", f"{label}: description is empty"))
            if not variant.cta.strip():
                issues.append(ValidationIssue("copy.cta", f"{label}: call to action is empty"))
            if not variant.channel.strip():
                issues.append(ValidationIssue("copy.channel", f"{label}: channel is empty"))
        return issues
