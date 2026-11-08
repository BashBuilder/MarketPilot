"""Expected package, diff and decision shapes from section 2 of the guide."""

import uuid
from datetime import datetime
from typing import Any

BRIEF_KEYS = {"product", "goal", "audience", "tone", "channels", "constraints"}
RESEARCH_KEYS = {"segments", "pain_points", "messaging_angles", "sources"}
DIRECTION_KEYS = {
    "style_guide",
    "composition",
    "image_prompts",
    "video_prompts",
    "negative_prompts",
}
SCORE_DIMENSIONS = {
    "brief_alignment",
    "audience_fit",
    "copy_quality",
    "visual_quality",
    "compliance_risk",
}
PACKAGE_KEYS = {"brief", "research", "copy", "direction", "assets", "compliance", "score"}


def assert_keys(value: Any, expected: set[str]) -> dict[str, Any]:
    assert isinstance(value, dict)
    assert set(value) == expected
    return value


def assert_uuid(value: Any) -> None:
    assert isinstance(value, str)
    uuid.UUID(value)


def assert_timestamp(value: Any) -> None:
    assert isinstance(value, str)
    datetime.fromisoformat(value)


def assert_package(body: dict[str, Any]) -> None:
    assert_keys(body, PACKAGE_KEYS)
    _assert_brief(body["brief"])
    _assert_research(body["research"])
    variants = assert_keys(body["copy"], {"variants"})["variants"]
    assert isinstance(variants, list) and variants
    for variant in variants:
        assert_keys(variant, {"channel", "headline", "description", "cta"})
    assert_keys(body["direction"], DIRECTION_KEYS)
    assets = assert_keys(body["assets"], {"assets"})["assets"]
    assert isinstance(assets, list) and assets
    for asset in assets:
        assert_keys(asset, {"uri", "checksum", "model", "seed", "prompt"})
        assert isinstance(asset["seed"], int) and asset["seed"] >= 0
        assert len(asset["checksum"]) == 64
    items = assert_keys(body["compliance"], {"items"})["items"]
    assert isinstance(items, list) and items
    for item in items:
        assert_keys(item, {"check", "passed", "reason"})
        assert isinstance(item["passed"], bool)
    _assert_score(body["score"])


def _assert_brief(brief: Any) -> None:
    assert_keys(brief, BRIEF_KEYS)
    assert isinstance(brief["channels"], list) and brief["channels"]
    assert isinstance(brief["constraints"], list) and brief["constraints"]


def _assert_research(research: Any) -> None:
    assert_keys(research, RESEARCH_KEYS)
    for segment in research["segments"]:
        assert_keys(segment, {"name", "description"})
    for source in research["sources"]:
        assert_keys(source, {"title", "url"})
        assert str(source["url"]).startswith("http")
    assert research["pain_points"] and research["messaging_angles"]


def _assert_score(score: Any) -> None:
    assert_keys(score, SCORE_DIMENSIONS | {"total"})
    for name in SCORE_DIMENSIONS:
        dimension = assert_keys(score[name], {"score", "justification"})
        assert 0 <= dimension["score"] <= 10
        assert isinstance(dimension["justification"], str)
    assert 0 <= score["total"] <= 100


def assert_diff(body: dict[str, Any]) -> None:
    assert_keys(body, {"from", "to", "changes"})
    assert isinstance(body["from"], int) and isinstance(body["to"], int)
    assert isinstance(body["changes"], list)
    for change in body["changes"]:
        assert_keys(change, {"path", "before", "after"})


def assert_approve(body: dict[str, Any]) -> None:
    assert_keys(body, {"status", "version"})
    assert body["status"] == "completed"
    assert isinstance(body["version"], int)


def assert_revise(body: dict[str, Any]) -> None:
    assert_keys(body, {"run_id", "version"})
    assert_uuid(body["run_id"])
    assert isinstance(body["version"], int)
