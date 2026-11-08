"""Versioned API router composed from the endpoint modules."""

from fastapi import APIRouter

from app.api import campaigns, health, runs, stream, versions

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(campaigns.router)
api_router.include_router(versions.router)
api_router.include_router(runs.router)
api_router.include_router(stream.router)
