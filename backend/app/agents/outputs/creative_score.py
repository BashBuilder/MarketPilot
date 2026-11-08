"""Validated creative score produced by the Reviewer agent.

Each dimension is scored 0-10 and weighted equally at 20%. The rubric total
is ``sum(score * 0.2) * 10`` out of 100; ``compliance_risk`` is inverted so
10 means the lowest risk.
"""

from typing import Annotated, Self

from pydantic import Field, model_validator

from app.agents.outputs.base import OutputModel

JUSTIFICATION = r"^[^\r\n]+$"


class ScoreDimension(OutputModel):
    score: Annotated[float, Field(ge=0, le=10)]
    justification: Annotated[
        str,
        Field(min_length=5, max_length=200, pattern=JUSTIFICATION),
    ]


class CreativeScore(OutputModel):
    brief_alignment: ScoreDimension
    audience_fit: ScoreDimension
    copy_quality: ScoreDimension
    visual_quality: ScoreDimension
    compliance_risk: ScoreDimension
    total: Annotated[float, Field(ge=0, le=100)]

    @model_validator(mode="after")
    def total_matches_weighted_dimensions(self) -> Self:
        dimensions = (
            self.brief_alignment,
            self.audience_fit,
            self.copy_quality,
            self.visual_quality,
            self.compliance_risk,
        )
        expected = round(sum(item.score for item in dimensions) * 0.2 * 10, 2)
        if abs(self.total - expected) > 0.01:
            raise ValueError(f"total must equal {expected} for the weighted dimensions")
        return self
