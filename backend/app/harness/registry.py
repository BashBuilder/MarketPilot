"""Per-agent tool registry with a default-deny allowlist."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from app.core.errors import GuardrailViolation

AGENT_ALLOWLISTS: dict[str, frozenset[str]] = {
    "brief": frozenset({"read_state"}),
    "research": frozenset({"search_tools", "read_state"}),
    "copywriter": frozenset({"policy_lookup", "read_state"}),
    "creative_director": frozenset(),
    "designer": frozenset({"generate_image", "edit_image", "generate_video", "read_state"}),
    "compliance": frozenset({"policy_lookup", "read_state"}),
    "reviewer": frozenset({"policy_lookup", "read_state"}),
    "supervisor": frozenset(),
}


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """A typed, callable tool exposed to the agents."""

    name: str
    args_model: type[BaseModel]
    handler: Callable[..., Awaitable[Any]]
    side_effecting: bool


class ToolRegistry:
    """Built-in per-agent permissions plus registered tool implementations."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register_tool(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Tool {spec.name} is already registered")
        self._tools[spec.name] = spec

    def allowed_tools(self, agent: str) -> frozenset[str]:
        """Return the agent's allowlist; unknown agents get no tools."""
        return AGENT_ALLOWLISTS.get(agent, frozenset())

    def get_tool(self, agent: str, name: str) -> ToolSpec:
        """Return a registered tool, enforcing the agent's allowlist."""
        if name not in self.allowed_tools(agent):
            raise GuardrailViolation(f"Agent {agent} is not allowed to use tool {name}")
        spec = self._tools.get(name)
        if spec is None:
            raise GuardrailViolation(f"Tool {name} is not registered")
        return spec
