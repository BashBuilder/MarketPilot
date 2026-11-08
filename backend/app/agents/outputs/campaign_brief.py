"""Validated campaign brief produced by the Brief agent."""

from typing import Annotated

from pydantic import Field

from app.agents.outputs.base import OutputModel

Channel = Annotated[str, Field(min_length=1, max_length=100)]
Constraint = Annotated[str, Field(min_length=1, max_length=200)]


class CampaignBrief(OutputModel):
    product: Annotated[str, Field(min_length=2, max_length=200)]
    goal: Annotated[str, Field(min_length=5, max_length=500)]
    audience: Annotated[str, Field(min_length=3, max_length=500)]
    tone: Annotated[str, Field(min_length=2, max_length=100)]
    channels: Annotated[list[Channel], Field(min_length=1, max_length=10)]
    constraints: Annotated[list[Constraint], Field(min_length=1, max_length=20)]
