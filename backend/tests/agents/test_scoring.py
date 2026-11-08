"""Tests for the deterministic scoring rubric helpers."""

import pytest

from app.agents.outputs import CreativeScore, PipelineNode, ScoreDimension
from app.agents.scoring import dimensions, weakest_node, weighted_total


def dimension(value: float) -> ScoreDimension:
    return ScoreDimension(score=value, justification="Clear and on brief")


def score(
    *,
    brief_alignment: float = 8,
    audience_fit: float = 8,
    copy_quality: float = 8,
    visual_quality: float = 8,
    compliance_risk: float = 8,
) -> CreativeScore:
    scored = {
        "brief_alignment": dimension(brief_alignment),
        "audience_fit": dimension(audience_fit),
        "copy_quality": dimension(copy_quality),
        "visual_quality": dimension(visual_quality),
        "compliance_risk": dimension(compliance_risk),
    }
    return CreativeScore(**scored, total=weighted_total(scored.values()))


def test_weighted_total_weights_every_dimension_equally() -> None:
    scored = (dimension(8), dimension(7), dimension(9), dimension(8), dimension(7))

    assert weighted_total(scored) == 78.0


def test_dimensions_are_returned_in_rubric_order() -> None:
    assert [item.score for item in dimensions(score())] == [8, 8, 8, 8, 8]


@pytest.mark.parametrize(
    ("lowest", "expected"),
    [
        ("brief_alignment", "brief"),
        ("audience_fit", "research"),
        ("copy_quality", "copywriter"),
        ("visual_quality", "creative_director"),
        ("compliance_risk", "copywriter"),
    ],
)
def test_weakest_node_maps_each_dimension(lowest: str, expected: PipelineNode) -> None:
    result = score(**{lowest: 3})

    assert weakest_node(result) == expected


def test_tie_picks_the_earlier_pipeline_node() -> None:
    result = score(brief_alignment=5, audience_fit=5)

    assert weakest_node(result) == "brief"


def test_tie_between_copywriter_and_creative_director_picks_copywriter() -> None:
    result = score(visual_quality=2, compliance_risk=2)

    assert weakest_node(result) == "copywriter"
