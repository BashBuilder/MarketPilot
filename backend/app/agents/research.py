"""Research agent: audience research grounded in search-tool sources."""

from collections.abc import Mapping, Sequence
from typing import Any, cast

from app.agents.base import BaseAgent
from app.agents.outputs import AudienceResearch
from app.core.config import Settings
from app.core.errors import ToolError
from app.graph.state import WorkflowState
from app.harness.issues import ValidationIssue, Validator
from app.harness.tool_runner import ToolRunner
from app.tools.search_tools import SearchArgs, SearchResult

MAX_QUERY_LENGTH = 500


class SourceProvenanceValidator:
    """Require every cited URL to have come from this run's search results."""

    def __init__(self, retrieved_urls: set[str]) -> None:
        self._retrieved = frozenset(retrieved_urls)

    def validate(self, output: AudienceResearch, /) -> list[ValidationIssue]:
        return [
            ValidationIssue(
                "sources.unretrieved",
                f"source URL was not returned by the search tool: {source.url}",
            )
            for source in output.sources
            if str(source.url) not in self._retrieved
        ]


class ResearchAgent(BaseAgent[AudienceResearch]):
    """Search first, then produce research that cites only returned sources."""

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(
            name="research",
            output_model=AudienceResearch,
            prompt_name="research",
            settings=settings,
        )

    async def _prepare(
        self,
        state: WorkflowState,
        tools: ToolRunner | None,
    ) -> tuple[Mapping[str, Any], Sequence[Validator[AudienceResearch]]]:
        context, validators = await super()._prepare(state, tools)
        results = await self._search(state, tools)
        augmented = {
            **context,
            "search_results": [result.model_dump(mode="json") for result in results],
        }
        provenance = SourceProvenanceValidator({str(result.url) for result in results})
        return augmented, (*validators, provenance)

    async def _search(
        self,
        state: WorkflowState,
        tools: ToolRunner | None,
    ) -> list[SearchResult]:
        if tools is None:
            raise ToolError("search_tools", "research requires the search tool")
        raw = await tools(
            "search_tools",
            SearchArgs(query=_query_for(state)),
            step="research-search",
        )
        if not isinstance(raw, list) or not all(isinstance(result, SearchResult) for result in raw):
            raise ToolError("search_tools", "search tool returned an unexpected result")
        return cast(list[SearchResult], raw)


def _query_for(state: WorkflowState) -> str:
    parts = [state.idea]
    if state.brief is not None:
        parts.append(f"{state.brief.product} {state.brief.audience}")
    return " ".join(parts)[:MAX_QUERY_LENGTH]
