"""Deterministic pipeline LLM used when ``APP_MODE=fake``.

Outputs are built around the golden hair-care idea. The compliance report is
derived from the subjects the agent put in its context, so generated asset
paths are covered without touching the network.
"""

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from app.agents.outputs import (
    AdCopySet,
    AudienceResearch,
    CampaignBrief,
    ComplianceReport,
    CreativeDirection,
    CreativeScore,
)
from app.core.errors import ValidationFailure
from app.llm import fake_outputs
from app.llm.base import LLMError, OutputT, TokenUsage

_FENCE = re.compile(r"<untrusted[^>]*>\s*(.*?)\s*</untrusted>", re.DOTALL)


class FakePipelineLLM:
    """Return one valid canned output per agent output model."""

    def __init__(self) -> None:
        self.calls: list[list[Mapping[str, str]]] = []

    async def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        output_model: type[OutputT] | None = None,
    ) -> tuple[OutputT | str, TokenUsage]:
        self.calls.append(list(messages))
        if output_model is None:
            raise LLMError("fake pipeline mode requires a structured output model")
        return self._build(output_model, _context(messages)), TokenUsage()

    def _build(self, model: type[OutputT], context: Mapping[str, Any]) -> OutputT:
        if model is CampaignBrief:
            return fake_outputs.brief()  # type: ignore[return-value]
        if model is AudienceResearch:
            return fake_outputs.research(context)  # type: ignore[return-value]
        if model is AdCopySet:
            return fake_outputs.copy()  # type: ignore[return-value]
        if model is CreativeDirection:
            return fake_outputs.direction()  # type: ignore[return-value]
        if model is ComplianceReport:
            return fake_outputs.compliance(context)  # type: ignore[return-value]
        if model is CreativeScore:
            return fake_outputs.score()  # type: ignore[return-value]
        raise ValidationFailure(model.__name__, "fake pipeline has no canned output")


def _context(messages: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    for message in reversed(messages):
        match = _FENCE.search(str(message.get("content", "")))
        if match is None:
            continue
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}
