"""Tests for the per-agent tool registry."""

import pytest
from pydantic import BaseModel

from app.core.errors import GuardrailViolation
from app.harness.registry import ToolRegistry, ToolSpec


class SearchArgs(BaseModel):
    query: str


async def search(args: SearchArgs) -> list[str]:
    return [args.query]


def make_spec() -> ToolSpec:
    return ToolSpec(
        name="search_tools",
        args_model=SearchArgs,
        handler=search,
        side_effecting=False,
    )


def test_allowed_tools_match_the_agent_allowlist() -> None:
    registry = ToolRegistry()

    assert registry.allowed_tools("research") == frozenset({"search_tools", "read_state"})
    assert registry.allowed_tools("designer") == frozenset(
        {"generate_image", "edit_image", "generate_video", "read_state"}
    )
    assert registry.allowed_tools("creative_director") == frozenset()


def test_unknown_agent_has_no_tools() -> None:
    registry = ToolRegistry()

    assert registry.allowed_tools("unknown_agent") == frozenset()


def test_registered_allowed_tool_is_returned() -> None:
    registry = ToolRegistry()
    spec = make_spec()
    registry.register_tool(spec)

    assert registry.get_tool("research", "search_tools") is spec
    assert spec.args_model is SearchArgs
    assert spec.side_effecting is False


def test_denied_tool_raises_guardrail_violation() -> None:
    registry = ToolRegistry()
    registry.register_tool(make_spec())

    with pytest.raises(GuardrailViolation, match="not allowed"):
        registry.get_tool("brief", "search_tools")


def test_unknown_agent_is_denied() -> None:
    registry = ToolRegistry()
    registry.register_tool(make_spec())

    with pytest.raises(GuardrailViolation, match="not allowed"):
        registry.get_tool("unknown_agent", "search_tools")


def test_allowed_but_unregistered_tool_is_unknown() -> None:
    registry = ToolRegistry()

    with pytest.raises(GuardrailViolation, match="not registered"):
        registry.get_tool("brief", "read_state")


def test_unknown_tool_name_is_rejected() -> None:
    registry = ToolRegistry()

    with pytest.raises(GuardrailViolation):
        registry.get_tool("research", "does_not_exist")
