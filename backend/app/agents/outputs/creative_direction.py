"""Validated creative direction produced by the Creative Director agent."""

from typing import Annotated

from pydantic import Field

from app.agents.outputs.base import OutputModel

Prompt = Annotated[str, Field(min_length=5, max_length=1000)]


class CreativeDirection(OutputModel):
    image_prompts: Annotated[list[Prompt], Field(min_length=1, max_length=20)]
    video_prompts: Annotated[list[Prompt], Field(min_length=1, max_length=20)]
    style_guide: Annotated[str, Field(min_length=10, max_length=2000)]
    composition: Annotated[str, Field(min_length=10, max_length=2000)]
    negative_prompts: Annotated[list[Prompt], Field(min_length=1, max_length=20)]
