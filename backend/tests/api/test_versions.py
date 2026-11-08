"""Version history, package and diff endpoints."""

import uuid

from app.database.models import CampaignStatus
from app.database.repositories import CampaignRepository, VersionRepository

COPY = {
    "variants": [
        {
            "channel": "Instagram",
            "headline": "Morning hair, handled",
            "description": "A lightweight serum for all-day smoothness.",
            "cta": "Shop the serum",
        }
    ]
}


def package(headline: str = "Morning hair, handled") -> dict:
    copy = {"variants": [{**COPY["variants"][0], "headline": headline}]}
    return {"copy": copy, "brief": None, "score": None}


async def seed_versions(db_session) -> tuple[uuid.UUID, uuid.UUID]:
    campaign = await CampaignRepository(db_session).create(
        "Hair care", CampaignStatus.AWAITING_APPROVAL
    )
    repository = VersionRepository(db_session)
    first = await repository.create(campaign.id, package(), score=70.0)
    second = await repository.create(
        campaign.id,
        package(headline="Evening hair, handled"),
        parent_version_id=first.id,
        score=82.0,
    )
    await db_session.commit()
    return campaign.id, second.id


async def test_versions_are_listed_oldest_first(client, db_session) -> None:
    campaign_id, _ = await seed_versions(db_session)

    response = await client.get(f"/api/v1/campaigns/{campaign_id}/versions")

    assert response.status_code == 200
    listed = response.json()
    assert [item["version"] for item in listed] == [1, 2]
    assert listed[1]["parent_version_id"] is not None
    assert listed[1]["score"] == 82.0


async def test_full_package_uses_the_contract_section_names(client, db_session) -> None:
    campaign_id, _ = await seed_versions(db_session)

    response = await client.get(f"/api/v1/campaigns/{campaign_id}/versions/2")

    assert response.status_code == 200
    body = response.json()
    assert body["copy"]["variants"][0]["headline"] == "Evening hair, handled"
    assert "research" not in body


async def test_unknown_campaign_or_version_is_404(client, db_session) -> None:
    campaign_id, _ = await seed_versions(db_session)

    missing_campaign = await client.get(f"/api/v1/campaigns/{uuid.uuid4()}/versions")
    missing_version = await client.get(f"/api/v1/campaigns/{campaign_id}/versions/9")

    assert missing_campaign.status_code == 404
    assert missing_campaign.json()["error"]["code"] == "campaign_not_found"
    assert missing_version.status_code == 404
    assert missing_version.json()["error"]["code"] == "version_not_found"


async def test_diff_of_identical_versions_is_empty(client, db_session) -> None:
    campaign = await CampaignRepository(db_session).create("Hair care", CampaignStatus.DRAFT)
    repository = VersionRepository(db_session)
    first = await repository.create(campaign.id, package())
    second = await repository.create(campaign.id, package())
    await db_session.commit()

    response = await client.get(
        f"/api/v1/campaigns/{campaign.id}/versions/{first.version}/diff/{second.version}"
    )

    assert response.status_code == 200
    assert response.json() == {"from": 1, "to": 2, "changes": []}


async def test_diff_reports_changed_paths(client, db_session) -> None:
    campaign_id, _ = await seed_versions(db_session)

    response = await client.get(f"/api/v1/campaigns/{campaign_id}/versions/1/diff/2")

    assert response.status_code == 200
    body = response.json()
    assert body["from"] == 1 and body["to"] == 2
    assert body["changes"] == [
        {
            "path": "copy.variants.0.headline",
            "before": "Morning hair, handled",
            "after": "Evening hair, handled",
        }
    ]


async def test_diff_with_a_missing_version_is_404(client, db_session) -> None:
    campaign_id, _ = await seed_versions(db_session)

    response = await client.get(f"/api/v1/campaigns/{campaign_id}/versions/1/diff/7")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "version_not_found"
