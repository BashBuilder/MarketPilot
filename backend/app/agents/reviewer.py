"""Reviewer agent: score the finished package on the five-dimension rubric."""

from app.agents.base import BaseAgent
from app.agents.outputs import CreativeScore, ScoreDimension
from app.agents.scoring import DIMENSION_FIELDS, weighted_total
from app.core.config import Settings
from app.harness.issues import ValidationIssue

TOTAL_TOLERANCE = 0.01


class DimensionsScoredValidator:
    """Every rubric dimension must be scored and carry a justification."""

    def validate(self, output: CreativeScore, /) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for name in DIMENSION_FIELDS:
            dimension = getattr(output, name, None)
            if not isinstance(dimension, ScoreDimension):
                issues.append(ValidationIssue("score.dimension", f"{name} was not scored"))
            elif not dimension.justification.strip():
                issues.append(
                    ValidationIssue("score.justification", f"{name} needs a justification")
                )
        return issues


class WeightedTotalValidator:
    """The reported total must equal the weighted dimension scores."""

    def validate(self, output: CreativeScore, /) -> list[ValidationIssue]:
        scored: list[ScoreDimension] = []
        for name in DIMENSION_FIELDS:
            dimension = getattr(output, name, None)
            if not isinstance(dimension, ScoreDimension):
                # DimensionsScoredValidator reports the missing dimension.
                return []
            scored.append(dimension)

        expected = weighted_total(scored)
        if abs(output.total - expected) > TOTAL_TOLERANCE:
            return [
                ValidationIssue(
                    "score.total",
                    f"total must equal {expected} for the weighted dimensions",
                )
            ]
        return []


class ReviewerAgent(BaseAgent[CreativeScore]):
    """Score and recommend revisions without approving or rewriting."""

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(
            name="reviewer",
            output_model=CreativeScore,
            prompt_name="reviewer",
            validators=[DimensionsScoredValidator(), WeightedTotalValidator()],
            settings=settings,
        )
