"""Expected campaign, version-summary and error shapes."""

from typing import Any

from tests.contract_shapes import assert_keys, assert_timestamp, assert_uuid

CAMPAIGN_STATUSES = {"draft", "running", "awaiting_approval", "completed", "failed"}
SUMMARY_KEYS = {
    "id",
    "idea",
    "status",
    "latest_version",
    "latest_score",
    "active_run_id",
    "created_at",
    "updated_at",
}


def assert_create(body: dict[str, Any]) -> None:
    assert_keys(body, {"campaign_id", "run_id"})
    assert_uuid(body["campaign_id"])
    assert_uuid(body["run_id"])


def assert_summary(body: dict[str, Any]) -> None:
    assert_keys(body, SUMMARY_KEYS)
    assert_uuid(body["id"])
    assert isinstance(body["idea"], str)
    assert body["status"] in CAMPAIGN_STATUSES
    assert body["latest_version"] is None or isinstance(body["latest_version"], int)
    assert body["latest_score"] is None or isinstance(body["latest_score"], int | float)
    if body["active_run_id"] is not None:
        assert_uuid(body["active_run_id"])
    assert_timestamp(body["created_at"])
    assert_timestamp(body["updated_at"])


def assert_version_summary(body: dict[str, Any]) -> None:
    assert_keys(body, {"version", "parent_version_id", "score", "created_at"})
    assert isinstance(body["version"], int)
    if body["parent_version_id"] is not None:
        assert_uuid(body["parent_version_id"])
    assert body["score"] is None or isinstance(body["score"], int | float)
    assert_timestamp(body["created_at"])


def assert_error(body: dict[str, Any]) -> None:
    error = assert_keys(body, {"error"})["error"]
    assert isinstance(error, dict)
    assert {"code", "message"} <= set(error) <= {"code", "message", "details"}
    assert isinstance(error["code"], str) and error["code"]
    assert isinstance(error["message"], str) and error["message"]
