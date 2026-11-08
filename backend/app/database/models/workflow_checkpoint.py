"""Append-only workflow checkpoint after every completed node."""

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class WorkflowCheckpoint(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Append-only: one row per (run, step)."""

    __tablename__ = "workflow_checkpoints"
    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "step",
            name="uq_workflow_checkpoints_run_id_step",
        ),
        {"info": {"append_only": True}},
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workflow_runs.id"),
        nullable=False,
        index=True,
    )
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    node: Mapped[str] = mapped_column(String(50), nullable=False)
    state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
