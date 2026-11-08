"""Immutable validated output produced by one agent in one run."""

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class AgentOutput(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Append-only: one validated output per (run, agent)."""

    __tablename__ = "agent_outputs"
    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "agent",
            name="uq_agent_outputs_run_id_agent",
        ),
        {"info": {"append_only": True}},
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workflow_runs.id"),
        nullable=False,
        index=True,
    )
    agent: Mapped[str] = mapped_column(String(50), nullable=False)
    output: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
