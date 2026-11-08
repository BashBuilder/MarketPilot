"""Validated audience research produced by the Research agent."""

from typing import Annotated

from pydantic import Field, HttpUrl

from app.agents.outputs.base import OutputModel

Insight = Annotated[str, Field(min_length=3, max_length=300)]


class AudienceSegment(OutputModel):
    name: Annotated[str, Field(min_length=2, max_length=100)]
    description: Annotated[str, Field(min_length=5, max_length=500)]


class ResearchSource(OutputModel):
    title: Annotated[str, Field(min_length=2, max_length=200)]
    url: HttpUrl


class AudienceResearch(OutputModel):
    segments: Annotated[list[AudienceSegment], Field(min_length=1, max_length=10)]
    pain_points: Annotated[list[Insight], Field(min_length=1, max_length=20)]
    messaging_angles: Annotated[list[Insight], Field(min_length=1, max_length=20)]
    sources: Annotated[list[ResearchSource], Field(min_length=1, max_length=20)]
