"""Human approval or revision decision for a run."""

import uuid
from enum import StrEnum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import (
    Base,
    CreatedAtMixin,
    UUIDPrimaryKeyMixin,
    enum_values,
)


class ApprovalDecision(StrEnum):
    APPROVE = "approve"
    REVISE = "revise"


class Approval(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "approvals"

    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workflow_runs.id"),
        nullable=False,
        index=True,
    )
    campaign_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("campaign_versions.id"),
        nullable=False,
        index=True,
    )
    decision: Mapped[ApprovalDecision] = mapped_column(
        SAEnum(
            ApprovalDecision,
            name="approval_decision",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_node: Mapped[str | None] = mapped_column(String(50), nullable=True)
