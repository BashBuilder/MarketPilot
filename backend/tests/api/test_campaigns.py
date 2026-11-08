"""Campaign endpoints: create, list, detail, errors and CORS."""

import uuid

from app.database.models import CampaignStatus, RunStatus
from app.database.repositories import (
    CampaignRepository,
    RunRepository,
    VersionRepository,
)
from tests.api.helpers import Harness


async def seed_campaign(db_session, *, idea: str = "Hair care for adults") -> uuid.UUID:
    campaign = await CampaignRepository(db_session).create(idea, CampaignStatus.RUNNING)
    await RunRepository(db_session).create(campaign.id, RunStatus.COMPLETED)
    await VersionRepository(db_session).create(campaign.id, {"brief": None}, score=84.0)
    await db_session.commit()
    return campaign.id


async def test_create_campaign_starts_a_run(client, harness: Harness, db_session) -> None:
    response = await client.post("/api/v1/campaigns", json={"idea": "  Hair care launch  "})

    assert response.status_code == 201
    body = response.json()
    campaign = await CampaignRepository(db_session).get(uuid.UUID(body["campaign_id"]))
    run = await RunRepository(db_session).get(uuid.UUID(body["run_id"]))

    assert campaign is not None and campaign.idea == "Hair care launch"
    assert campaign.status is CampaignStatus.RUNNING
    assert run is not None and run.campaign_id == campaign.id
    assert harness.launcher.started == [body["run_id"]]


async def test_list_and_get_campaign_summary(client, db_session) -> None:
    campaign_id = await seed_campaign(db_session)

    listed = await client.get("/api/v1/campaigns")
    detail = await client.get(f"/api/v1/campaigns/{campaign_id}")

    assert listed.status_code == 200
    assert detail.status_code == 200
    summary = detail.json()
    assert summary["id"] == str(campaign_id)
    assert summary["latest_version"] == 1
    assert summary["latest_score"] == 84.0
    assert summary["active_run_id"] is None
    assert listed.json()[0]["id"] == str(campaign_id)


async def test_unknown_campaign_returns_the_error_envelope(client) -> None:
    campaign_id = uuid.uuid4()

    response = await client.get(f"/api/v1/campaigns/{campaign_id}")

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "campaign_not_found"
    assert str(campaign_id) in error["message"]


async def test_long_idea_is_rejected_with_422(client, harness: Harness) -> None:
    idea = "x" * (harness.settings.max_idea_length + 1)

    response = await client.post("/api/v1/campaigns", json={"idea": idea})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_failed"
    assert error["details"]["field"] == "idea"


async def test_empty_idea_is_rejected_with_422(client) -> None:
    response = await client.post("/api/v1/campaigns", json={"idea": "   "})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_failed"


async def test_cors_allows_only_the_frontend_origins(client) -> None:
    allowed = await client.options(
        "/api/v1/campaigns",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    denied = await client.options(
        "/api/v1/campaigns",
        headers={
            "Origin": "http://evil.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-origin" not in denied.headers


async def test_health_is_available_at_both_paths(client) -> None:
    root = await client.get("/health")
    versioned = await client.get("/api/v1/health")

    assert root.json() == {"status": "ok"}
    assert versioned.json() == {"status": "ok"}
