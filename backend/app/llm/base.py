"""Shared LLM client contract and token accounting."""

from collections.abc import Mapping, Sequence
from typing import Protocol, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.core.errors import MarketPilotError


class LLMError(MarketPilotError):
    """Raised when an LLM provider call fails or returns unusable output."""

    code = "llm_error"
    status_code = 502


class TokenUsage(BaseModel):
    """Token counts reported by an LLM provider."""

    model_config = ConfigDict(frozen=True)

    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


OutputT = TypeVar("OutputT", bound=BaseModel)


class LLMClient(Protocol):
    """Provider-neutral interface for one structured LLM completion."""

    async def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        output_model: type[OutputT] | None = None,
    ) -> tuple[OutputT | str, TokenUsage]:
        """Return validated output (or text) and the token usage for the call."""
        ...
