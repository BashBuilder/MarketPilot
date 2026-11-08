"""Embedding providers for policy retrieval."""

import hashlib
import math
from typing import Protocol

from app.core.config import Settings, get_settings

POLICY_EMBEDDING_DIMENSIONS = 384


class Embedder(Protocol):
    """Provider contract for turning text into a fixed-size vector."""

    dimensions: int

    async def embed(self, text: str) -> list[float]: ...


class FakeEmbedder:
    """Deterministic hash-based vectors for offline development and tests."""

    def __init__(self, dimensions: int = POLICY_EMBEDDING_DIMENSIONS) -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be at least 1")
        self.dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        return fake_embedding(text, self.dimensions)


def fake_embedding(text: str, dimensions: int = POLICY_EMBEDDING_DIMENSIONS) -> list[float]:
    """Return a stable, L2-normalised vector derived from the text hash."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    raw = [digest[index % len(digest)] / 255.0 for index in range(dimensions)]
    norm = math.sqrt(sum(value * value for value in raw)) or 1.0
    return [value / norm for value in raw]


def build_embedder(settings: Settings | None = None) -> Embedder:
    """Return the embedder selected by configuration; only fake exists today."""
    _ = settings or get_settings()
    return FakeEmbedder()
