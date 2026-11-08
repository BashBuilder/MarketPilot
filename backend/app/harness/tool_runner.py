"""Agent-facing contract for executing one registered tool."""

from typing import Any, Protocol

from pydantic import BaseModel


class ToolRunner(Protocol):
    """Bound executor supplied to an agent by the graph node."""

    async def __call__(self, tool: str, args: BaseModel, *, step: str = "") -> Any:
        """Run ``tool`` for the current agent and return its typed result."""
        ...
