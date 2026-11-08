"""Immutable audit record for every tool invocation."""

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class ToolCall(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Append-only: calls are recorded once and never updated."""

    __tablename__ = "tool_calls"
    __table_args__ = {"info": {"append_only": True}}

    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workflow_runs.id"),
        nullable=False,
        index=True,
    )
    agent: Mapped[str] = mapped_column(String(50), nullable=False)
    tool: Mapped[str] = mapped_column(String(100), nullable=False)
    args_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
