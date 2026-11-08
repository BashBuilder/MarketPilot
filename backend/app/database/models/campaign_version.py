"""Immutable snapshot of a campaign package at one version."""

import uuid
from typing import Any

from sqlalchemy import Float, ForeignKey, Index, Integer, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class CampaignVersion(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Append-only: prior rows are never updated or deleted."""

    __tablename__ = "campaign_versions"
    __table_args__ = (
        Index(
            "ix_campaign_versions_campaign_id_version",
            "campaign_id",
            "version",
            unique=True,
        ),
        {"info": {"append_only": True}},
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("campaigns.id"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("campaign_versions.id"),
        nullable=True,
        index=True,
    )
    package: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
