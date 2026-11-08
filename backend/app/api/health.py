"""Liveness endpoint served under the versioned prefix."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Return ok when the process is serving requests."""
    return {"status": "ok"}
