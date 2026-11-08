"""Pure package diffing plus a thin version loader."""

import uuid
from collections.abc import Mapping
from typing import Any, Final, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import VersionNotFound
from app.database.repositories import VersionRepository
from app.graph.versioning import PACKAGE_SECTIONS

_MISSING: Final = object()


class VersionLike(Protocol):
    """Anything carrying a version number and its package."""

    version: int
    package: dict[str, Any]


def compute_diff(version_a: VersionLike, version_b: VersionLike) -> dict[str, Any]:
    """Return dotted-path changes between two immutable packages."""
    changes: list[dict[str, Any]] = []
    keys = [*PACKAGE_SECTIONS]
    keys.extend(sorted((set(version_a.package) | set(version_b.package)) - set(PACKAGE_SECTIONS)))
    for section in keys:
        _diff_value(
            section,
            version_a.package.get(section, _MISSING),
            version_b.package.get(section, _MISSING),
            changes,
        )
    return {"from": version_a.version, "to": version_b.version, "changes": changes}


async def load_diff(
    session: AsyncSession,
    campaign_id: uuid.UUID,
    from_version: int,
    to_version: int,
) -> dict[str, Any]:
    """Fetch two versions and return their package diff."""
    repository = VersionRepository(session)
    version_a = await repository.get(campaign_id, from_version)
    if version_a is None:
        raise VersionNotFound(str(campaign_id), from_version)
    version_b = await repository.get(campaign_id, to_version)
    if version_b is None:
        raise VersionNotFound(str(campaign_id), to_version)
    return compute_diff(version_a, version_b)


def _diff_value(
    path: str,
    before: Any,
    after: Any,
    changes: list[dict[str, Any]],
) -> None:
    if before is _MISSING or after is _MISSING:
        before_value = None if before is _MISSING else before
        after_value = None if after is _MISSING else after
        if before_value != after_value:
            changes.append({"path": path, "before": before_value, "after": after_value})
        return

    if before == after:
        return

    if isinstance(before, Mapping) and isinstance(after, Mapping):
        for key in sorted(set(before) | set(after)):
            _diff_value(
                f"{path}.{key}",
                before.get(key, _MISSING),
                after.get(key, _MISSING),
                changes,
            )
        return

    if isinstance(before, list) and isinstance(after, list):
        for index in range(max(len(before), len(after))):
            _diff_value(
                f"{path}.{index}",
                before[index] if index < len(before) else _MISSING,
                after[index] if index < len(after) else _MISSING,
                changes,
            )
        return

    changes.append({"path": path, "before": before, "after": after})
