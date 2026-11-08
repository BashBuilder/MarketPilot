"""Semantic checks for local generated asset files."""

import hashlib
from pathlib import Path

from app.agents.outputs.asset_set import AssetSet, GeneratedAsset
from app.harness.image_checks import is_decodable_png
from app.harness.issues import ValidationIssue


class AssetSemanticValidator:
    """Checks local asset files exist, match their checksum and decode."""

    def __init__(self, asset_root: Path = Path("assets")) -> None:
        self._asset_root = asset_root

    def validate(self, output: AssetSet, /) -> list[ValidationIssue]:
        if not output.assets:
            return [ValidationIssue("assets.empty", "asset set contains no assets")]

        issues: list[ValidationIssue] = []
        for index, asset in enumerate(output.assets, start=1):
            issues.extend(self._validate_asset(index, asset))
        return issues

    def _validate_asset(self, index: int, asset: GeneratedAsset) -> list[ValidationIssue]:
        label = f"asset {index} ({asset.uri})"
        if asset.uri.lower().startswith(("http://", "https://")):
            return [
                ValidationIssue(
                    "assets.remote",
                    f"{label}: remote assets cannot be verified locally",
                )
            ]

        path = self._resolve(asset.uri)
        if path is None:
            return [ValidationIssue("assets.path", f"{label}: path escapes the asset root")]
        if not path.is_file():
            return [ValidationIssue("assets.missing", f"{label}: file does not exist")]

        try:
            data = path.read_bytes()
        except OSError as error:
            return [ValidationIssue("assets.unreadable", f"{label}: could not read file: {error}")]

        issues: list[ValidationIssue] = []
        actual_checksum = hashlib.sha256(data).hexdigest()
        if actual_checksum != asset.checksum.lower():
            issues.append(
                ValidationIssue(
                    "assets.checksum",
                    f"{label}: checksum mismatch "
                    f"(expected {asset.checksum}, got {actual_checksum})",
                )
            )
        if not is_decodable_png(data):
            issues.append(
                ValidationIssue("assets.image", f"{label}: file does not decode as a PNG image")
            )
        return issues

    def _resolve(self, uri: str) -> Path | None:
        path = Path(uri)
        if path.is_absolute():
            return path
        root = self._asset_root.resolve()
        resolved = (root / path).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            return None
        return resolved
