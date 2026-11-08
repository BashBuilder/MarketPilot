"""Deterministic in-memory LLM client for tests."""

import json
from collections import deque
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.errors import ValidationFailure
from app.llm.base import LLMError, OutputT, TokenUsage

QueuedResponse = str | BaseModel | Mapping[str, Any]


class FakeLLMClient:
    """Replays queued responses in order and records the messages it receives."""

    def __init__(
        self,
        responses: Sequence[QueuedResponse] | None = None,
        *,
        usage: TokenUsage | None = None,
    ) -> None:
        self._responses: deque[QueuedResponse] = deque(responses or ())
        self._usage = usage or TokenUsage()
        self.calls: list[list[Mapping[str, str]]] = []

    @property
    def remaining(self) -> int:
        """Number of responses still queued."""
        return len(self._responses)

    async def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        output_model: type[OutputT] | None = None,
    ) -> tuple[OutputT | str, TokenUsage]:
        self.calls.append(list(messages))
        if not self._responses:
            raise LLMError("FakeLLMClient has no queued responses")
        response = self._responses.popleft()
        if output_model is None:
            return self._as_text(response), self._usage
        return self._as_model(response, output_model), self._usage

    @staticmethod
    def _as_text(response: QueuedResponse) -> str:
        if isinstance(response, str):
            return response
        if isinstance(response, BaseModel):
            return response.model_dump_json()
        return json.dumps(dict(response))

    @staticmethod
    def _as_model(response: QueuedResponse, output_model: type[OutputT]) -> OutputT:
        if isinstance(response, output_model):
            return response
        if isinstance(response, BaseModel):
            raise LLMError(f"queued {type(response).__name__}, expected {output_model.__name__}")
        try:
            if isinstance(response, str):
                return output_model.model_validate_json(response)
            return output_model.model_validate(response)
        except ValidationError as error:
            raise ValidationFailure(output_model.__name__, str(error)) from error
