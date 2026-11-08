"""Golden campaign ideas used by the offline evaluation suite."""

from typing import NamedTuple


class GoldenIdea(NamedTuple):
    """One stable evaluation input."""

    id: str
    idea: str


class BadClaim(NamedTuple):
    """One copy line that deterministic rules must reject."""

    id: str
    text: str


GOLDEN_IDEAS: tuple[GoldenIdea, ...] = (
    GoldenIdea(
        id="hair-care-25-40",
        idea=(
            "Create an advertising campaign for a fictional hair-care product "
            "targeting adults aged 25 to 40"
        ),
    ),
)

BAD_CLAIMS: tuple[BadClaim, ...] = (
    BadClaim(id="regrowth-guarantee", text="guaranteed hair regrowth in 7 days"),
    BadClaim(id="miracle-cure", text="a 100% miracle cure for dry hair after one wash"),
)
