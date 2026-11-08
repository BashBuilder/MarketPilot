"""Immutable campaign-version snapshots and package/state conversion."""

import uuid
from typing import Any, Final

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.outputs import (
    AdCopySet,
    AssetSet,
    AudienceResearch,
    CampaignBrief,
    ComplianceReport,
    CreativeDirection,
    CreativeScore,
    OutputModel,
)
from app.database.models import CampaignVersion, WorkflowRun
from app.database.repositories import VersionRepository
from app.graph.state import WorkflowState

PACKAGE_SECTIONS: Final[tuple[str, ...]] = (
    "brief",
    "research",
    "copy",
    "direction",
    "assets",
    "compliance",
    "score",
)


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


def state_from_package(
    idea: str,
    package: dict[str, Any],
    *,
    target_node: str | None = None,
    revision_feedback: str | None = None,
) -> WorkflowState:
    """Rebuild workflow state from an immutable version package."""
    return WorkflowState(
        idea=idea,
        brief=_load(package, "brief", CampaignBrief),
        research=_load(package, "research", AudienceResearch),
        copy=_load(package, "copy", AdCopySet),
        direction=_load(package, "direction", CreativeDirection),
        assets=_load(package, "assets", AssetSet),
        compliance=_load(package, "compliance", ComplianceReport),
        score=_load(package, "score", CreativeScore),
        target_node=target_node,
        revision_feedback=revision_feedback,
        status="running",
    )


async def snapshot_version(
    session: AsyncSession,
    run: WorkflowRun,
    state: WorkflowState,
) -> CampaignVersion:
    """Append a new version whose parent is the previous latest version."""
    repository = VersionRepository(session)
    latest = await repository.latest(run.campaign_id)
    return await repository.create(
        run.campaign_id,
        package_from_state(state),
        parent_version_id=latest.id if latest is not None else None,
        score=state.score.total if state.score is not None else None,
    )


async def ensure_version(
    session: AsyncSession,
    run: WorkflowRun,
    state: WorkflowState,
    version_id: uuid.UUID | None,
) -> CampaignVersion:
    """Return the version under review, creating the first one if a legacy run lacks it."""
    repository = VersionRepository(session)
    if version_id is not None:
        version = await repository.get_by_id(version_id)
        if version is None or version.campaign_id != run.campaign_id:
            raise LookupError(f"version {version_id} does not belong to this campaign")
        return version

    latest = await repository.latest(run.campaign_id)
    if latest is not None:
        return latest
    return await snapshot_version(session, run, state)


def _dump[ModelT: OutputModel](value: ModelT | None) -> dict[str, Any] | None:
    return value.model_dump(mode="json") if value is not None else None


def _load[ModelT: OutputModel](
    package: dict[str, Any],
    section: str,
    model: type[ModelT],
) -> ModelT | None:
    value = package.get(section)
    return model.model_validate(value) if value is not None else None
