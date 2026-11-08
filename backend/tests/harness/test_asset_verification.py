"""Tests for semantic checks on generated asset files."""

import hashlib
import struct
import zlib
from pathlib import Path

from app.agents.outputs.asset_set import AssetSet
from app.harness.verification import AssetSemanticValidator


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
