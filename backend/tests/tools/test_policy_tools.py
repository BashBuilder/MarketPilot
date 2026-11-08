"""Tests for read-only policy retrieval with the fake embedder."""

import pytest
from sqlalchemy import func, select

from app.database.models import PolicyDocument
from app.database.seed import POLICY_DOCUMENTS, seed
from app.llm.embeddings import FakeEmbedder
from app.tools.policy_tools import PolicyLookupArgs, PolicySearcher, policy_lookup


async def test_closest_seeded_policy_is_returned(db_session) -> None:
    embedder = FakeEmbedder()
    await seed(db_session, embedder)
    document = POLICY_DOCUMENTS[0]

    matches = await PolicySearcher(db_session, embedder).search(
        f"{document.title}\n{document.content}", 2
    )

    assert matches[0].id == document.id
    assert matches[0].distance == pytest.approx(0.0, abs=1e-5)
    assert matches[1].id != document.id


async def test_policy_lookup_does_not_write(db_session) -> None:
    embedder = FakeEmbedder()
    await seed(db_session, embedder)
    before = await db_session.scalar(select(func.count()).select_from(PolicyDocument))

    matches = await policy_lookup(
        PolicyLookupArgs(query="medical outcomes for cosmetic products", top_k=1),
        searcher=PolicySearcher(db_session, embedder),
    )

    after = await db_session.scalar(select(func.count()).select_from(PolicyDocument))
    assert len(matches) == 1
    assert before == after
