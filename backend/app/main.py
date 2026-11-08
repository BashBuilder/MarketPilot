"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="MarketPilot API")


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}
