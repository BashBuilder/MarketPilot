"""Shared campaign/run fixtures for checkpoint and human-gate tests."""

from app.agents.outputs import CampaignBrief
from app.database.models import RunStatus, WorkflowRun
from app.database.repositories import CampaignRepository, RunRepository
from app.graph.state import WorkflowState


def make_state(idea: str = "Checkpoint campaign") -> WorkflowState:
    return WorkflowState(
        idea=idea,
        brief=CampaignBrief(
            product="HydraSilk Shampoo",
            goal="Launch a hydrating shampoo for adults with dry hair.",
            audience="Adults aged 25 to 40 who style their hair daily.",
            tone="Warm and confident",
            channels=["Instagram", "Email"],
            constraints=["No medical claims"],
        ),
        status="running",
        errors=["compliance: claim needs evidence"],
    )


async def make_run(db_session) -> WorkflowRun:
    campaign = await CampaignRepository(db_session).create("Checkpoint campaign")
    return await RunRepository(db_session).create(campaign.id, RunStatus.RUNNING)
