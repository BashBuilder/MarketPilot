"""Workflow state carried between graph nodes."""

import warnings
from collections.abc import Mapping
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.agents.outputs import (
    AdCopySet,
    AssetSet,
    AudienceResearch,
    CampaignBrief,
    ComplianceReport,
    CreativeDirection,
    CreativeScore,
    OutputModel,
)
from app.core.errors import ValidationFailure

# The package names this section "copy"; keep the contract name and silence the
# Pydantic warning about shadowing the deprecated BaseModel.copy().
warnings.filterwarnings(
    "ignore",
    message=('Field name "copy" in "WorkflowState" shadows an attribute in parent "BaseModel"'),
    category=UserWarning,
)

WorkflowStatus = Literal[
    "pending",
    "running",
    "awaiting_approval",
    "escalated",
    "completed",
    "failed",
]


class WorkflowState(BaseModel):
    """Mutable state shared by the pipeline; package sections fill in as agents run."""

    model_config = ConfigDict(extra="forbid")

    idea: Annotated[str, Field(min_length=1, max_length=2000)]
    brief: CampaignBrief | None = None
    research: AudienceResearch | None = None
    copy: AdCopySet | None = None  # type: ignore[assignment]
    direction: CreativeDirection | None = None
    assets: AssetSet | None = None
    compliance: ComplianceReport | None = None
    score: CreativeScore | None = None
    target_node: str | None = None
    revision_feedback: str | None = None
    versions: list[int] = Field(default_factory=list)
    status: WorkflowStatus = "pending"
    retry_counters: dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


def parse_agent_output[OutputT: OutputModel](
    model: type[OutputT],
    payload: str | Mapping[str, Any],
) -> OutputT:
    """Validate raw agent output, raising ValidationFailure on a bad payload."""
    try:
        if isinstance(payload, str):
            return model.model_validate_json(payload)
        return model.model_validate(payload)
    except ValidationError as error:
        raise ValidationFailure(model.__name__, str(error)) from error
