"""Copywriter agent: channel copy with compliance-driven revisions."""

from collections.abc import Mapping, Sequence
from typing import Any

from app.agents.base import BaseAgent
from app.agents.outputs import AdCopySet, AdVariant, ComplianceItem
from app.core.config import Settings
from app.graph.state import WorkflowState
from app.harness.issues import ValidationIssue, Validator
from app.harness.tool_runner import ToolRunner
from app.harness.verification import CopySemanticValidator


class CopyRevisionValidator:
    """Keep every unflagged variant identical to the previous copy."""

    def __init__(self, previous: AdCopySet, flagged_channels: frozenset[str]) -> None:
        self._previous = previous
        self._flagged = frozenset(channel.casefold() for channel in flagged_channels)

    def validate(self, output: AdCopySet, /) -> list[ValidationIssue]:
        by_channel: dict[str, list[AdVariant]] = {}
        for variant in output.variants:
            by_channel.setdefault(variant.channel.casefold(), []).append(variant)

        issues: list[ValidationIssue] = []
        for index, variant in enumerate(self._previous.variants, start=1):
            channel = variant.channel.casefold()
            if channel in self._flagged:
                continue
            matches = by_channel.get(channel, [])
            label = f"variant {index} ({variant.channel})"
            if not matches:
                issues.append(
                    ValidationIssue("copy.revision", f"{label}: unflagged variant was removed")
                )
            elif any(match != variant for match in matches):
                issues.append(
                    ValidationIssue("copy.revision", f"{label}: unflagged variant changed")
                )
        return issues


class CopywriterAgent(BaseAgent[AdCopySet]):
    """Produce copy and rewrite only variants flagged by compliance."""

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(
            name="copywriter",
            output_model=AdCopySet,
            prompt_name="copywriter",
            validators=[CopySemanticValidator()],
            settings=settings,
        )

    async def _prepare(
        self,
        state: WorkflowState,
        tools: ToolRunner | None,
    ) -> tuple[Mapping[str, Any], Sequence[Validator[AdCopySet]]]:
        context, validators = await super()._prepare(state, tools)
        failed = _failed_items(state)
        if not failed or state.copy is None:
            return context, validators

        flagged = _flagged_channels(state.copy, failed)
        revision_context = {
            **context,
            "compliance": {"items": [item.model_dump(mode="json") for item in failed]},
            "copy": state.copy.model_dump(mode="json"),
            "revision_mode": True,
            "flagged_channels": sorted(flagged),
        }
        revision_validator = CopyRevisionValidator(state.copy, flagged)
        return revision_context, (*validators, revision_validator)


def _failed_items(state: WorkflowState) -> list[ComplianceItem]:
    if state.compliance is None:
        return []
    return [item for item in state.compliance.items if not item.passed]


def _flagged_channels(previous: AdCopySet, failed: Sequence[ComplianceItem]) -> frozenset[str]:
    text = " ".join(f"{item.check} {item.reason}" for item in failed).casefold()
    matched = {
        variant.channel.casefold()
        for variant in previous.variants
        if variant.channel.casefold() in text
    }
    if matched:
        return frozenset(matched)
    return frozenset(variant.channel.casefold() for variant in previous.variants)
