"""Creative score attached to one campaign version."""

import uuid
from typing import Any

from sqlalchemy import Float, ForeignKey, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class CreativeScore(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "creative_scores"

    campaign_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("campaign_versions.id"),
        nullable=False,
        unique=True,
    )
    breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)
