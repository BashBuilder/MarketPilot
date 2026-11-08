"""Pure package diffing and the database-backed version loader."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from app.core.errors import VersionNotFound
from app.database.repositories import CampaignRepository, VersionRepository
from app.graph.diff import compute_diff, load_diff
from app.graph.versioning import package_from_state
from tests.harness.context_fixtures import make_state


def versions(package_a: dict, package_b: dict):
    return (
        SimpleNamespace(version=1, package=package_a),
        SimpleNamespace(version=2, package=package_b),
    )


def test_identical_packages_have_no_changes():
    package = package_from_state(make_state())

    result = compute_diff(*versions(package, deepcopy(package)))

    assert result == {"from": 1, "to": 2, "changes": []}


def test_nested_list_change_uses_a_dotted_path():
    first = package_from_state(make_state())
    second = deepcopy(first)
    second["copy"]["variants"][0]["headline"] = "Evening hair, handled"

    result = compute_diff(*versions(first, second))

    assert result["changes"] == [
        {
            "path": "copy.variants.0.headline",
            "before": "Morning hair, handled",
            "after": "Evening hair, handled",
        }
    ]


def test_missing_section_is_reported_at_the_section_path():
    first = package_from_state(make_state())
    second = deepcopy(first)
    second.pop("score")

    result = compute_diff(*versions(first, second))

    assert [change["path"] for change in result["changes"]] == ["score"]
    assert result["changes"][0]["after"] is None


def test_new_list_item_is_reported_with_a_null_before():
    first = package_from_state(make_state())
    second = deepcopy(first)
    second["assets"]["assets"].append(
        {
            "uri": "assets/second.png",
            "checksum": "b" * 64,
            "model": "fake",
            "seed": 1,
            "prompt": "second image",
        }
    )

    result = compute_diff(*versions(first, second))

    assert result["changes"][0]["path"] == "assets.assets.1"
    assert result["changes"][0]["before"] is None


async def test_loader_reads_both_versions(db_session):
    campaign = await CampaignRepository(db_session).create("Campaign")
    repository = VersionRepository(db_session)
    first = await repository.create(campaign.id, package_from_state(make_state()))
    second_package = deepcopy(first.package)
    second_package["copy"]["variants"][0]["headline"] = "Evening hair, handled"
    await repository.create(campaign.id, second_package, parent_version_id=first.id)

    result = await load_diff(db_session, campaign.id, 1, 2)

    assert result["from"] == 1 and result["to"] == 2
    assert [change["path"] for change in result["changes"]] == ["copy.variants.0.headline"]


async def test_loader_reports_a_missing_version(db_session):
    campaign = await CampaignRepository(db_session).create("Campaign")
    await VersionRepository(db_session).create(campaign.id, {})

    with pytest.raises(VersionNotFound):
        await load_diff(db_session, campaign.id, 1, 2)
