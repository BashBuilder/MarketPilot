"""Validated generated-asset metadata produced by the Designer agent."""

from typing import Annotated

from pydantic import Field

from app.agents.outputs.base import OutputModel

Checksum = Annotated[str, Field(pattern=r"^[0-9a-fA-F]{64}$")]


class GeneratedAsset(OutputModel):
    uri: Annotated[str, Field(min_length=1, max_length=2000)]
    checksum: Checksum
    model: Annotated[str, Field(min_length=1, max_length=100)]
    seed: Annotated[int, Field(ge=0)]
    prompt: Annotated[str, Field(min_length=1, max_length=1000)]


class AssetSet(OutputModel):
    assets: Annotated[list[GeneratedAsset], Field(min_length=1, max_length=20)]
