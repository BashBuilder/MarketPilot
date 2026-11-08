"""Tests for schema and semantic output verification."""

import hashlib
import struct
import zlib
from pathlib import Path

from app.agents.outputs.ad_copy_set import AdCopySet, AdVariant
from app.agents.outputs.asset_set import AssetSet
from app.harness.verification import (
    MAX_HEADLINE_LENGTH,
    AssetSemanticValidator,
    CopySemanticValidator,
    SchemaValidator,
)

VALID_COPY = {
    "variants": [
        {
            "channel": "instagram",
            "headline": "Morning hair, handled",
            "description": "A lightweight serum that keeps frizz away all day.",
            "cta": "Shop the serum",
        }
    ]
}


def png_bytes(*, width: int = 1, height: int = 1) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    rows = b"".join(b"\x00" + b"\xff\x00\x00" * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(rows))
        + chunk(b"IEND", b"")
    )


def asset_set(uri: str, checksum: str) -> AssetSet:
    return AssetSet.model_validate(
        {
            "assets": [
                {
                    "uri": uri,
                    "checksum": checksum,
                    "model": "fake-sdxl",
                    "seed": 1,
                    "prompt": "Soft daylight portrait of glossy hair",
                }
            ]
        }
    )


def test_schema_validator_accepts_a_valid_model() -> None:
    assert SchemaValidator(AdCopySet).validate(AdCopySet.model_validate(VALID_COPY)) == []


def test_schema_validator_reports_invalid_payloads() -> None:
    issues = SchemaValidator(AdCopySet).validate({"variants": []})

    assert len(issues) == 1
    assert issues[0].code == "schema"
    assert issues[0].path == "variants"
    assert issues[0].message


def test_copy_semantic_validator_accepts_valid_copy() -> None:
    assert CopySemanticValidator().validate(AdCopySet.model_validate(VALID_COPY)) == []


def test_copy_semantic_validator_rejects_an_empty_variant_list() -> None:
    copy = AdCopySet.model_construct(variants=[])

    issues = CopySemanticValidator().validate(copy)

    assert [issue.code for issue in issues] == ["copy.empty"]
    assert "no variants" in issues[0].message


def test_copy_semantic_validator_rejects_long_and_short_headlines() -> None:
    long_copy = AdCopySet.model_validate(
        {
            "variants": [
                {
                    **VALID_COPY["variants"][0],
                    "headline": "x" * (MAX_HEADLINE_LENGTH + 1),
                }
            ]
        }
    )
    short_variant = AdVariant.model_construct(
        channel="instagram",
        headline="abc",
        description="A valid description.",
        cta="Go",
    )
    short_copy = AdCopySet.model_construct(variants=[short_variant])

    long_issues = CopySemanticValidator().validate(long_copy)
    short_issues = CopySemanticValidator().validate(short_copy)

    assert [issue.code for issue in long_issues] == ["copy.headline"]
    assert "maximum 90" in long_issues[0].message
    assert [issue.code for issue in short_issues] == ["copy.headline"]
    assert "minimum 5" in short_issues[0].message


def test_copy_semantic_validator_reports_every_empty_field() -> None:
    variant = AdVariant.model_construct(channel="", headline="", description="", cta="")
    copy = AdCopySet.model_construct(variants=[variant])

    issues = CopySemanticValidator().validate(copy)

    assert [issue.code for issue in issues] == [
        "copy.headline",
        "copy.description",
        "copy.cta",
        "copy.channel",
    ]


def test_asset_semantic_validator_accepts_a_matching_png(tmp_path: Path) -> None:
    data = png_bytes()
    (tmp_path / "hero.png").write_bytes(data)
    assets = asset_set("hero.png", hashlib.sha256(data).hexdigest())

    assert AssetSemanticValidator(tmp_path).validate(assets) == []


def test_asset_semantic_validator_reports_a_missing_file(tmp_path: Path) -> None:
    issues = AssetSemanticValidator(tmp_path).validate(asset_set("missing.png", "a" * 64))

    assert [issue.code for issue in issues] == ["assets.missing"]
    assert "does not exist" in issues[0].message


def test_asset_semantic_validator_reports_a_checksum_mismatch(tmp_path: Path) -> None:
    data = png_bytes()
    (tmp_path / "hero.png").write_bytes(data)

    issues = AssetSemanticValidator(tmp_path).validate(asset_set("hero.png", "0" * 64))

    assert [issue.code for issue in issues] == ["assets.checksum"]
    assert "checksum mismatch" in issues[0].message


def test_asset_semantic_validator_rejects_non_image_bytes(tmp_path: Path) -> None:
    data = b"not an image"
    (tmp_path / "hero.png").write_bytes(data)

    issues = AssetSemanticValidator(tmp_path).validate(
        asset_set("hero.png", hashlib.sha256(data).hexdigest())
    )

    assert [issue.code for issue in issues] == ["assets.image"]
    assert "does not decode" in issues[0].message


def test_asset_semantic_validator_rejects_paths_outside_the_root(tmp_path: Path) -> None:
    issues = AssetSemanticValidator(tmp_path).validate(asset_set("../outside.png", "a" * 64))

    assert [issue.code for issue in issues] == ["assets.path"]


def test_asset_semantic_validator_rejects_remote_uris(tmp_path: Path) -> None:
    issues = AssetSemanticValidator(tmp_path).validate(
        asset_set("https://res.cloudinary.com/demo/hero.png", "a" * 64)
    )

    assert [issue.code for issue in issues] == ["assets.remote"]
