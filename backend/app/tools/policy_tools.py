"""Read-only retrieval over the policy document vectors."""

import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import PolicyDocument
from app.database.session import session_scope
from app.harness.registry import ToolRegistry, ToolSpec
from app.llm.embeddings import Embedder, build_embedder


class PolicyLookupArgs(BaseModel):
    """Inputs for one policy similarity lookup."""

    query: Annotated[str, Field(min_length=1, max_length=1000)]
    top_k: Annotated[int, Field(ge=1, le=10)] = 3


class PolicyMatch(BaseModel):
    """One policy document and its cosine distance from the query."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    id: uuid.UUID
    title: Annotated[str, Field(min_length=1, max_length=200)]
    source: Annotated[str, Field(min_length=1, max_length=500)]
    content: Annotated[str, Field(min_length=1)]
    distance: float


class PolicySearcher:
    """Execute a parameterized, read-only pgvector similarity query."""

    def __init__(self, session: AsyncSession, embedder: Embedder | None = None) -> None:
        self._session = session
        self._embedder = embedder or build_embedder()

    async def search(self, query: str, top_k: int) -> list[PolicyMatch]:
        vector = await self._embedder.embed(query)
        distance = PolicyDocument.embedding.cosine_distance(vector).label("distance")
        statement = select(PolicyDocument, distance).order_by(distance).limit(top_k)
        rows = (await self._session.execute(statement)).all()
        return [
            PolicyMatch(
                id=document.id,
                title=document.title,
                source=document.source,
                content=document.content,
                distance=float(score),
            )
            for document, score in rows
        ]


async def policy_lookup(
    args: PolicyLookupArgs,
    searcher: PolicySearcher | None = None,
) -> list[PolicyMatch]:
    """Return the closest policy documents without writing anything."""
    if searcher is not None:
        return await searcher.search(args.query, args.top_k)
    async with session_scope() as session:
        return await PolicySearcher(session).search(args.query, args.top_k)


def register_policy_tools(
    registry: ToolRegistry,
    searcher: PolicySearcher | None = None,
) -> None:
    """Register the read-only policy lookup tool with the harness registry."""

    async def bound_lookup(args: PolicyLookupArgs) -> list[PolicyMatch]:
        return await policy_lookup(args, searcher=searcher)

    registry.register_tool(
        ToolSpec(
            name="policy_lookup",
            args_model=PolicyLookupArgs,
            handler=bound_lookup,
            side_effecting=False,
        )
    )
