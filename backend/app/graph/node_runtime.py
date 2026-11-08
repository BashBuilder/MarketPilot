"""Injected dependencies and shared helpers for graph nodes."""

import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.outputs import OutputModel
from app.core.config import Settings
from app.graph.state import WorkflowState
from app.harness.tool_runner import ToolRunner
from app.harness.verification import EventCallback
from app.llm.base import LLMClient

ToolResolver = Callable[[str], ToolRunner | None]


class Agent(Protocol):
    """Minimal surface the node factory needs from an agent."""

    name: str

    async def run(
        self,
        state: WorkflowState,
        llm: LLMClient,
        emit: EventCallback,
        tools: ToolRunner | None = None,
    ) -> OutputModel:
        """Run the agent and return its verified output."""
        ...


@dataclass(slots=True)
class NodeRuntime:
    """Everything a node needs from its caller, injected rather than global."""

    run_id: uuid.UUID
    session: AsyncSession
    llm: LLMClient
    emit: EventCallback
    tools_for: ToolResolver
    settings: Settings | None = None


def event_data(
    runtime: NodeRuntime,
    agent: str,
    extra: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Build the common SSE payload fields plus any event-specific values."""
    payload: dict[str, object] = {
        "run_id": str(runtime.run_id),
        "timestamp": datetime.now(UTC).isoformat(),
        "agent": agent,
    }
    if extra is not None:
        payload.update(extra)
    return payload
