"""Deterministic scoring helpers shared by the Reviewer and Supervisor."""

from collections.abc import Iterable
from typing import Final

from app.agents.outputs import CreativeScore, PipelineNode, ScoreDimension
from app.harness.pipeline import PIPELINE_NODES

WEIGHT: Final = 0.2
TOTAL_SCALE: Final = 10.0

DIMENSION_NODES: Final[tuple[tuple[str, PipelineNode], ...]] = (
    ("brief_alignment", "brief"),
    ("audience_fit", "research"),
    ("copy_quality", "copywriter"),
    ("visual_quality", "creative_director"),
    ("compliance_risk", "copywriter"),
)

DIMENSION_FIELDS: Final[tuple[str, ...]] = tuple(field for field, _ in DIMENSION_NODES)


def weighted_total(dimensions: Iterable[ScoreDimension]) -> float:
    """Return the 0-100 rubric total for equally weighted dimensions."""
    return round(sum(dimension.score for dimension in dimensions) * WEIGHT * TOTAL_SCALE, 2)


def dimensions(score: CreativeScore) -> tuple[ScoreDimension, ...]:
    """Return the five scored dimensions in rubric order."""
    return tuple(getattr(score, field) for field in DIMENSION_FIELDS)


def weakest_node(score: CreativeScore) -> PipelineNode:
    """Return the node to rerun for the lowest-scoring dimension.

    Ties go to the node that appears earlier in the pipeline.
    """
    candidates = (
        (getattr(score, field).score, PIPELINE_NODES.index(node), node)
        for field, node in DIMENSION_NODES
    )
    _, _, node = min(candidates)
    return node
