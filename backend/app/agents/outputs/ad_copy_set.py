"""Validated advertising copy produced by the Copywriter agent."""

from typing import Annotated

from pydantic import Field

from app.agents.outputs.base import OutputModel


class AdVariant(OutputModel):
    channel: Annotated[str, Field(min_length=2, max_length=100)]
    headline: Annotated[str, Field(min_length=3, max_length=200)]
    description: Annotated[str, Field(min_length=10, max_length=1000)]
    cta: Annotated[str, Field(min_length=2, max_length=100)]


class AdCopySet(OutputModel):
    variants: Annotated[list[AdVariant], Field(min_length=1, max_length=50)]
