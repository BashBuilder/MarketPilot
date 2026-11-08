"""Brief agent: turn a campaign idea into a validated brief."""

from app.agents.base import BaseAgent
from app.agents.outputs import CampaignBrief
from app.core.config import Settings
from app.harness.issues import ValidationIssue

EMPTY_FIELD_ISSUES = {
    "product": "product must not be empty",
    "goal": "goal must not be empty",
    "audience": "audience must not be empty",
}


class BriefSemanticValidator:
    """Reject structurally valid briefs with empty required content."""

    def validate(self, output: CampaignBrief, /) -> list[ValidationIssue]:
        issues = [
            ValidationIssue(field, message)
            for field, message in EMPTY_FIELD_ISSUES.items()
            if not getattr(output, field).strip()
        ]
        if not any(channel.strip() for channel in output.channels):
            issues.append(ValidationIssue("channels", "at least one channel is required"))
        return issues


class BriefAgent(BaseAgent[CampaignBrief]):
    """Produce a campaign brief without inventing unsupported claims."""

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(
            name="brief",
            output_model=CampaignBrief,
            prompt_name="brief",
            validators=[BriefSemanticValidator()],
            settings=settings,
        )
