"""Shared base for validated, immutable agent outputs."""

from pydantic import BaseModel, ConfigDict


class OutputModel(BaseModel):
    """Strict base model: frozen, no unknown fields, trimmed strings."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )
