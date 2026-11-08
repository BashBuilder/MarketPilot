"""Approval-gated filesystem export for immutable campaign versions."""

import json
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ExportNotApproved, VersionNotFound
from app.database.repositories import ApprovalRepository, VersionRepository


async def export_version(
    session: AsyncSession,
    campaign_id: uuid.UUID,
    version_number: int,
    directory: str | Path,
) -> Path:
    """Write one approved version's package to a JSON file."""
    version = await VersionRepository(session).get(campaign_id, version_number)
    if version is None:
        raise VersionNotFound(str(campaign_id), version_number)
    approval = await ApprovalRepository(session).approved_for_version(version.id)
    if approval is None:
        raise ExportNotApproved(str(campaign_id), version_number)

    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"campaign-{campaign_id}-v{version.version}.json"
    path.write_text(
        json.dumps(
            {
                "campaign_id": str(campaign_id),
                "version": version.version,
                "score": version.score,
                "package": version.package,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path
