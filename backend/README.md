# MarketPilot Backend

FastAPI service and LangGraph pipeline that turns a campaign idea into an
immutable, reviewable campaign package.

## Setup

```bash
uv sync
uv run uvicorn app.main:app --reload
```

## Checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy app
```

Only the health endpoint exists so far; the rest of the API is built in the
phases described in `agent.md`.
