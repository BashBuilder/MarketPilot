"""Pydantic request and response models mirroring the API contract."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.agents.outputs import (
    AdCopySet,
    AssetSet,
    AudienceResearch,
    CampaignBrief,
    ComplianceReport,
    CreativeDirection,
    CreativeScore,
)
from app.database.models import CampaignStatus

AgentName = Literal[
    "brief",
    "research",
    "copywriter",
    "creative_director",
    "designer",
    "compliance",
    "reviewer",
    "supervisor",
]


class _Request(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateCampaignRequest(_Request):
    idea: str = Field(min_length=1)


class CreateCampaignResponse(BaseModel):
    campaign_id: uuid.UUID
    run_id: uuid.UUID


class CampaignSummary(BaseModel):
    id: uuid.UUID
    idea: str
    status: CampaignStatus
    latest_version: int | None
    latest_score: float | None
    active_run_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class VersionSummary(BaseModel):
    version: int
    parent_version_id: uuid.UUID | None
    score: float | None
    created_at: datetime


class CampaignPackage(BaseModel):
    """Seven optional sections; `copy_set` is serialized as ``copy``."""

    brief: CampaignBrief | None = None
    research: AudienceResearch | None = None
    copy_set: AdCopySet | None = Field(default=None, alias="copy")
    direction: CreativeDirection | None = None
    assets: AssetSet | None = None
    compliance: ComplianceReport | None = None
    score: CreativeScore | None = None


class DiffChange(BaseModel):
    path: str
    before: Any
    after: Any


class DiffResponse(BaseModel):
    from_: int = Field(alias="from")
    to: int
    changes: list[DiffChange]

    model_config = ConfigDict(populate_by_name=True)


class ApproveRequest(_Request):
    comment: str | None = None


class ApproveResponse(BaseModel):
    status: Literal["completed"]
    version: int


class ReviseRequest(_Request):
    comment: str
    target_node: AgentName | None = None


class ReviseResponse(BaseModel):
    run_id: uuid.UUID
    version: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
