"""Seed data is stable across repeated runs."""

import pytest
from sqlalchemy import func, select

from app.database.models import Campaign, PolicyDocument
from app.database.seed import DEMO_CAMPAIGN_ID, POLICY_DOCUMENTS, seed
from app.llm.embeddings import FakeEmbedder, fake_embedding


async def test_seed_is_idempotent(db_session):
    embedder = FakeEmbedder()
    await seed(db_session, embedder)
    await seed(db_session, embedder)

    campaign = await db_session.get(Campaign, DEMO_CAMPAIGN_ID)
    campaign_count = await db_session.scalar(select(func.count()).select_from(Campaign))
    document_count = await db_session.scalar(select(func.count()).select_from(PolicyDocument))

    assert campaign is not None
    assert campaign.idea.startswith("Create an advertising campaign")
    assert campaign_count == 1
    assert document_count == len(POLICY_DOCUMENTS) == 3

    document = await db_session.get(PolicyDocument, POLICY_DOCUMENTS[0].id)
    assert document is not None
    expected = fake_embedding(f"{POLICY_DOCUMENTS[0].title}\n{POLICY_DOCUMENTS[0].content}")
    assert document.embedding == pytest.approx(expected, rel=1e-6)
