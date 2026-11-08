"""Validated compliance report produced by the Compliance agent."""

from typing import Annotated

from pydantic import Field

from app.agents.outputs.base import OutputModel


class ComplianceItem(OutputModel):
    check: Annotated[str, Field(min_length=2, max_length=200)]
    passed: bool
    reason: Annotated[str, Field(min_length=3, max_length=1000)]


class ComplianceReport(OutputModel):
    items: Annotated[list[ComplianceItem], Field(min_length=1, max_length=50)]
