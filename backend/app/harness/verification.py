"""Schema and semantic verification for validated agent outputs."""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from app.agents.outputs.ad_copy_set import AdCopySet
from app.agents.outputs.asset_set import AssetSet, GeneratedAsset
from app.harness.image_checks import is_decodable_png

T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=BaseModel)

MIN_HEADLINE_LENGTH = 5
MAX_HEADLINE_LENGTH = 90


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One readable verification failure."""

    code: str
    message: str
    path: str | None = None


class Validator(Protocol[T]):
    """A check that turns an output into a list of issues."""

    def validate(self, output: T, /) -> list[ValidationIssue]:
        """Return every issue found in ``output``; an empty list means valid."""
        ...


class SchemaValidator(Generic[ModelT]):
    """Re-run Pydantic's schema validation at the verification boundary."""

    def __init__(self, model: type[ModelT]) -> None:
        self._model = model

    def validate(self, output: object, /) -> list[ValidationIssue]:
        try:
            self._model.model_validate(output)
        except ValidationError as error:
            return [
                ValidationIssue(
                    code="schema",
                    message=item["msg"],
                    path=".".join(str(part) for part in item["loc"]) or None,
                )
                for item in error.errors()
            ]
        return []


class CopySemanticValidator:
    """Checks that ad copy is usable, beyond what the schema guarantees."""

    def validate(self, output: AdCopySet, /) -> list[ValidationIssue]:
        if not output.variants:
            return [ValidationIssue("copy.empty", "copy contains no variants")]

        issues: list[ValidationIssue] = []
        for index, variant in enumerate(output.variants, start=1):
            label = f"variant {index} ({variant.channel or 'unknown channel'})"
            headline_length = len(variant.headline.strip())
            if headline_length == 0:
                issues.append(ValidationIssue("copy.headline", f"{label}: headline is empty"))
            elif headline_length < MIN_HEADLINE_LENGTH:
                issues.append(
                    ValidationIssue(
                        "copy.headline",
                        f"{label}: headline is {headline_length} characters "
                        f"(minimum {MIN_HEADLINE_LENGTH})",
                    )
                )
            elif headline_length > MAX_HEADLINE_LENGTH:
                issues.append(
                    ValidationIssue(
                        "copy.headline",
                        f"{label}: headline is {headline_length} characters "
                        f"(maximum {MAX_HEADLINE_LENGTH})",
                    )
                )
            if not variant.description.strip():
                issues.append(ValidationIssue("copy.description", f"{label}: description is empty"))
            if not variant.cta.strip():
                issues.append(ValidationIssue("copy.cta", f"{label}: call to action is empty"))
            if not variant.channel.strip():
                issues.append(ValidationIssue("copy.channel", f"{label}: channel is empty"))
        return issues


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
