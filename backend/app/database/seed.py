"""Idempotent demo campaign and policy document seed data."""

import asyncio
import hashlib
import math
import uuid
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Campaign, CampaignStatus, PolicyDocument
from app.database.session import session_scope

DEMO_CAMPAIGN_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
DEMO_CAMPAIGN_IDEA = (
    "Create an advertising campaign for a fictional hair-care product "
    "targeting adults aged 25 to 40"
)


class PolicySeed(NamedTuple):
    id: uuid.UUID
    title: str
    source: str
    content: str


POLICY_DOCUMENTS: tuple[PolicySeed, ...] = (
    PolicySeed(
        id=uuid.UUID("00000000-0000-4000-8000-000000000011"),
        title="Advertising claims and substantiation",
        source="internal://policies/advertising-claims",
        content=(
            "Every objective claim must be substantiated before publication. "
            "Avoid absolute language such as 'best' or 'guaranteed' unless "
            "the claim cites evidence a reviewer can check."
        ),
    ),
    PolicySeed(
        id=uuid.UUID("00000000-0000-4000-8000-000000000012"),
        title="Health and beauty claims",
        source="internal://policies/health-beauty-claims",
        content=(
            "Do not promise medical outcomes for cosmetic products. Phrases "
            "such as 'cures', 'treats' or 'clinically proven' require "
            "qualified substantiation and must not imply a diagnosis."
        ),
    ),
    PolicySeed(
        id=uuid.UUID("00000000-0000-4000-8000-000000000013"),
        title="Data and privacy in advertising",
        source="internal://policies/data-privacy",
        content=(
            "Use only aggregated or fictional audience data in campaign "
            "materials. Never include personal data, sensitive attributes or "
            "targeting language that could discriminate against a group."
        ),
    ),
)


def fake_embedding(text: str, dimensions: int = 384) -> list[float]:
    """Deterministic stand-in for the fake embedder used before Phase 3."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    raw = [digest[index % len(digest)] / 255.0 for index in range(dimensions)]
    norm = math.sqrt(sum(value * value for value in raw)) or 1.0
    return [value / norm for value in raw]


async def seed(session: AsyncSession) -> None:
    """Insert missing seed rows; running it twice is a no-op."""
    if await session.get(Campaign, DEMO_CAMPAIGN_ID) is None:
        session.add(
            Campaign(
                id=DEMO_CAMPAIGN_ID,
                idea=DEMO_CAMPAIGN_IDEA,
                status=CampaignStatus.DRAFT,
            )
        )

    existing = await session.scalars(select(PolicyDocument.id))
    existing_ids = set(existing.all())
    for document in POLICY_DOCUMENTS:
        if document.id in existing_ids:
            continue
        session.add(
            PolicyDocument(
                id=document.id,
                title=document.title,
                source=document.source,
                content=document.content,
                doc_metadata={"sample": True},
                embedding=fake_embedding(f"{document.title}\n{document.content}"),
            )
        )

    await session.commit()


async def main() -> None:
    async with session_scope() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())
