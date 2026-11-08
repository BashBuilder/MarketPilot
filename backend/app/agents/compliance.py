"""Compliance agent: deterministic rule checks plus policy review."""

from collections.abc import Mapping, Sequence
from typing import Any, cast

from app.agents.base import BaseAgent
from app.agents.compliance_rules import RuleHit, check_text
from app.agents.outputs import ComplianceItem, ComplianceReport
from app.core.config import Settings
from app.core.errors import ToolError
from app.graph.state import WorkflowState
from app.harness.issues import ValidationIssue, Validator
from app.harness.tool_runner import ToolRunner
from app.tools.policy_tools import PolicyLookupArgs, PolicyMatch


class ComplianceCoverageValidator:
    """Require one item for every copy variant and every asset."""

    def __init__(self, labels: Sequence[str]) -> None:
        self._labels = tuple(labels)

    def validate(self, output: ComplianceReport, /) -> list[ValidationIssue]:
        checks = [item.check.casefold() for item in output.items]
        return [
            ValidationIssue("compliance.missing", f"missing compliance item for {label}")
            for label in self._labels
            if not any(check.startswith(label.casefold()) for check in checks)
        ]


class ComplianceReasonValidator:
    """Failed items must explain why they failed."""

    def validate(self, output: ComplianceReport, /) -> list[ValidationIssue]:
        return [
            ValidationIssue("compliance.reason", f"{item.check}: failed item needs a reason")
            for item in output.items
            if not item.passed and not item.reason.strip()
        ]


class ComplianceAgent(BaseAgent[ComplianceReport]):
    """Flag copy and asset problems without ever rewriting them."""

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(
            name="compliance",
            output_model=ComplianceReport,
            prompt_name="compliance",
            settings=settings,
        )

    async def _prepare(
        self,
        state: WorkflowState,
        tools: ToolRunner | None,
    ) -> tuple[Mapping[str, Any], Sequence[Validator[ComplianceReport]]]:
        context, validators = await super()._prepare(state, tools)
        if tools is None:
            raise ToolError("policy_lookup", "compliance requires the policy tool")

        hits = _rule_hits(state)
        raw = await tools(
            "policy_lookup",
            PolicyLookupArgs(query=_policy_query(state), top_k=3),
            step="compliance-policy",
        )
        matches = _policy_matches(raw)
        labels = _expected_labels(state)
        augmented = {
            **context,
            "rule_hits": [
                {"subject": label, "code": hit.code, "message": hit.message}
                for label, found in hits.items()
                for hit in found
            ],
            "policy_matches": [match.model_dump(mode="json") for match in matches],
            "subjects": list(labels),
        }
        deterministic = (
            ComplianceCoverageValidator(labels),
            ComplianceReasonValidator(),
        )
        return augmented, (*validators, *deterministic)

    def _finalize(
        self,
        output: ComplianceReport,
        state: WorkflowState,
        tools: ToolRunner | None,
    ) -> ComplianceReport:
        hits = {label.casefold(): found for label, found in _rule_hits(state).items()}
        labels = _expected_labels(state)
        items: list[ComplianceItem] = []
        for item in output.items:
            subject = _subject_for(item.check, labels).casefold()
            matched = hits.get(subject, [])
            if matched and item.passed:
                reason = "; ".join(hit.message for hit in matched)
                items.append(item.model_copy(update={"passed": False, "reason": reason}))
            else:
                items.append(item)
        return ComplianceReport(items=items)


def _rule_hits(state: WorkflowState) -> dict[str, list[RuleHit]]:
    hits: dict[str, list[RuleHit]] = {}
    if state.copy is not None:
        for variant in state.copy.variants:
            found = check_text(" ".join((variant.headline, variant.description, variant.cta)))
            if found:
                hits[f"copy:{variant.channel}"] = found
    if state.assets is not None:
        for asset in state.assets.assets:
            found = check_text(asset.prompt)
            if found:
                hits[f"asset:{asset.uri}"] = found
    return hits


def _expected_labels(state: WorkflowState) -> tuple[str, ...]:
    labels: list[str] = []
    if state.copy is not None:
        labels.extend(f"copy:{variant.channel}" for variant in state.copy.variants)
    if state.assets is not None:
        labels.extend(f"asset:{asset.uri}" for asset in state.assets.assets)
    return tuple(dict.fromkeys(labels))


def _subject_for(check: str, labels: Sequence[str]) -> str:
    folded = check.casefold()
    for label in sorted(labels, key=len, reverse=True):
        if folded.startswith(label.casefold()):
            return label
    return ""


def _policy_query(state: WorkflowState) -> str:
    parts: list[str] = []
    if state.copy is not None:
        parts.extend(
            f"{variant.headline} {variant.description} {variant.cta}"
            for variant in state.copy.variants
        )
    if state.assets is not None:
        parts.extend(asset.prompt for asset in state.assets.assets)
    return " ".join(parts)[:1000] or state.idea[:1000]


def _policy_matches(raw: object) -> list[PolicyMatch]:
    if not isinstance(raw, list) or not all(isinstance(match, PolicyMatch) for match in raw):
        raise ToolError("policy_lookup", "policy tool returned an unexpected result")
    return cast(list[PolicyMatch], raw)
