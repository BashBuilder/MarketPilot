"""Version snapshot and continuation-node helpers for the human gate."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import CampaignVersion, WorkflowRun
from app.database.repositories import CheckpointRepository, VersionRepository
from app.graph.state import WorkflowState
from app.harness.pipeline import HUMAN_GATE, PIPELINE_NODES, next_node


async def ensure_version(
    session: AsyncSession,
    run: WorkflowRun,
    state: WorkflowState,
    version_id: uuid.UUID | None,
) -> CampaignVersion:
    """Return the version under review, snapshotting the latest state if needed."""
    repository = VersionRepository(session)
    if version_id is not None:
        version = await repository.get_by_id(version_id)
        if version is None or version.campaign_id != run.campaign_id:
            raise LookupError(f"version {version_id} does not belong to this campaign")
        return version

    latest = await repository.latest(run.campaign_id)
    if latest is not None:
        return latest
    return await repository.create(
        run.campaign_id,
        package_from_state(state),
        score=state.score.total if state.score is not None else None,
    )


async def next_after_last_agent(session: AsyncSession, run_id: uuid.UUID) -> str:
    """Return the node after the newest checkpoint that is not the human gate."""
    checkpoint = await CheckpointRepository(session).latest_excluding(run_id, HUMAN_GATE)
    if checkpoint is None:
        return PIPELINE_NODES[0]
    return next_node(checkpoint.node)


def package_from_state(state: WorkflowState) -> dict[str, Any]:
    """Project workflow state onto the seven package sections."""
    return {
        "brief": _dump(state.brief),
        "research": _dump(state.research),
        "copy": _dump(state.copy),
        "direction": _dump(state.direction),
        "assets": _dump(state.assets),
        "compliance": _dump(state.compliance),
        "score": _dump(state.score),
    }


def _dump(value: Any) -> Any:
    return value.model_dump(mode="json") if value is not None else None
