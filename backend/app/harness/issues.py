"""Shared verification issue and validator contracts."""

from dataclasses import dataclass
from typing import Protocol, TypeVar

T = TypeVar("T", contravariant=True)


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
