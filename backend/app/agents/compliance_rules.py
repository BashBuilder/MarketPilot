"""Deterministic, editable compliance rules for copy and asset prompts."""

import re
from dataclasses import dataclass, field

from app.agents.blocklist import BLOCKED_NAMES


@dataclass(frozen=True, slots=True)
class RuleHit:
    """One rule matched by a piece of text."""

    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ComplianceRule:
    """A rule with optional regex patterns and literal names."""

    code: str
    message: str
    patterns: tuple[re.Pattern[str], ...] = field(default_factory=tuple)
    names: tuple[str, ...] = field(default_factory=tuple)

    def matches(self, text: str) -> bool:
        if any(pattern.search(text) for pattern in self.patterns):
            return True
        folded = text.casefold()
        return any(name.casefold() in folded for name in self.names)


RULES: tuple[ComplianceRule, ...] = (
    ComplianceRule(
        code="guaranteed_results",
        message="guaranteed or instant results are not allowed",
        patterns=(
            re.compile(r"\bguarantee(?:d|s)?\b", re.IGNORECASE),
            re.compile(r"\binstant(?:ly)?\b", re.IGNORECASE),
            re.compile(r"\bimmediate(?:ly)? results?\b", re.IGNORECASE),
        ),
    ),
    ComplianceRule(
        code="before_and_after",
        message="before-and-after promises are not allowed",
        patterns=(
            re.compile(r"\bbefore\s*(?:and|&)\s*after\b", re.IGNORECASE),
            re.compile(r"\bbefore/after\b", re.IGNORECASE),
        ),
    ),
    ComplianceRule(
        code="miracle_cure",
        message="miracle or cure wording is not allowed",
        patterns=(
            re.compile(r"\bmirac(?:le|les|ulous)\b", re.IGNORECASE),
            re.compile(r"\bcures?\b", re.IGNORECASE),
            re.compile(r"\bheals?\b", re.IGNORECASE),
        ),
    ),
    ComplianceRule(
        code="absolute_claim",
        message="absolute 100% claims are not allowed",
        patterns=(re.compile(r"\b100\s*%", re.IGNORECASE),),
    ),
    ComplianceRule(
        code="targets_minors",
        message="targeting minors is not allowed",
        patterns=(
            re.compile(r"\bminors?\b", re.IGNORECASE),
            re.compile(r"\bchildren\b", re.IGNORECASE),
            re.compile(r"\bteens?\b", re.IGNORECASE),
            re.compile(r"\bunder\s*(?:13|16|18)\b", re.IGNORECASE),
        ),
    ),
    ComplianceRule(
        code="named_person_or_brand",
        message="named real people or brands are not allowed",
        names=BLOCKED_NAMES,
    ),
)


def check_text(text: str) -> list[RuleHit]:
    """Return every rule hit in ``text``; an empty list means clean."""
    if not text.strip():
        return []
    return [RuleHit(rule.code, rule.message) for rule in RULES if rule.matches(text)]
