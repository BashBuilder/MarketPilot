"""Deterministic routing decision produced by the Supervisor."""

from typing import Annotated, Literal

from pydantic import Field

from app.agents.outputs.base import OutputModel

PipelineNode = Literal[
    "brief",
    "research",
    "copywriter",
    "creative_director",
    "designer",
    "compliance",
    "reviewer",
    "supervisor",
    "human",
]


class RouteDecision(OutputModel):
    next_node: PipelineNode
    reason: Annotated[str, Field(min_length=5, max_length=500)]
    escalate: bool
