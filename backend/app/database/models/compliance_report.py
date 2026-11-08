"""Compliance report attached to one campaign version."""

import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class ComplianceReport(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "compliance_reports"

    campaign_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("campaign_versions.id"),
        nullable=False,
        unique=True,
    )
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
