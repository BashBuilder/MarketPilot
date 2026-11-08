"""Continuation-node helpers for the human gate."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import CheckpointRepository
from app.harness.pipeline import HUMAN_GATE, PIPELINE_NODES, next_node


async def next_after_last_agent(session: AsyncSession, run_id: uuid.UUID) -> str:
    """Return the node after the newest checkpoint that is not the human gate."""
    checkpoint = await CheckpointRepository(session).latest_excluding(run_id, HUMAN_GATE)
    if checkpoint is None:
        return PIPELINE_NODES[0]
    return next_node(checkpoint.node)
