"""Search tools with a fake provider that keeps source provenance."""

from typing import Annotated, Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.harness.registry import ToolRegistry, ToolSpec

SourceUrl = Annotated[str, Field(pattern=r"^https?://\S+$", max_length=2000)]


class SearchResult(BaseModel):
    """One search hit with enough provenance to cite it."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    title: Annotated[str, Field(min_length=1, max_length=300)]
    url: SourceUrl
    snippet: Annotated[str, Field(min_length=1, max_length=1000)]


class SearchProvider(Protocol):
    """Provider contract for web research."""

    async def search(self, query: str, *, max_results: int) -> list[SearchResult]: ...


FIXED_RESULTS: tuple[SearchResult, ...] = (
    SearchResult(
        title="Hair care market overview",
        url="https://example.com/research/hair-care-market",
        snippet="Category growth is driven by premium conditioning and scalp-care routines.",
    ),
    SearchResult(
        title="Audience needs for adults aged 25 to 40",
        url="https://example.com/research/audience-needs",
        snippet="Buyers want visible results without a heavy routine or harsh ingredients.",
    ),
    SearchResult(
        title="Clean labelling and claims guidance",
        url="https://example.com/research/claims-guidance",
        snippet="Substantiate performance claims and avoid medical or absolute language.",
    ),
)


class FakeSearchProvider:
    """Return a fixed, deterministic result set for offline development."""

    async def search(self, query: str, *, max_results: int) -> list[SearchResult]:
        return list(FIXED_RESULTS[:max_results])


class SearchArgs(BaseModel):
    """Inputs for one research search call."""

    query: Annotated[str, Field(min_length=1, max_length=500)]
    max_results: Annotated[int, Field(ge=1, le=10)] = 5


def _default_provider() -> SearchProvider:
    return FakeSearchProvider()


async def search_tools(
    args: SearchArgs,
    provider: SearchProvider | None = None,
) -> list[SearchResult]:
    """Search through the configured provider and return cited results."""
    return await (provider or _default_provider()).search(
        args.query,
        max_results=args.max_results,
    )


def register_search_tools(
    registry: ToolRegistry,
    provider: SearchProvider | None = None,
) -> None:
    """Register the Research agent's search tool with the harness registry."""
    active = provider or _default_provider()

    async def bound_search(args: SearchArgs) -> list[SearchResult]:
        return await search_tools(args, provider=active)

    registry.register_tool(
        ToolSpec(
            name="search_tools",
            args_model=SearchArgs,
            handler=bound_search,
            side_effecting=False,
        )
    )
