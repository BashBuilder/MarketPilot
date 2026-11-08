"""Database triggers reject mutations to agent outputs and tool calls."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.database.models import AgentOutput, RunStatus, ToolCall
from app.database.repositories import CampaignRepository, RunRepository


async def create_run_records(db_session):
    campaign = await CampaignRepository(db_session).create("Campaign")
    run = await RunRepository(db_session).create(campaign.id, RunStatus.RUNNING)
    output = AgentOutput(
        run_id=run.id,
        agent="brief",
        output={"product": "Shampoo"},
    )
    call = ToolCall(
        run_id=run.id,
        agent="research",
        tool="search",
        args_hash="0" * 64,
        duration_ms=5,
        status="success",
        cost=0.0,
    )
    db_session.add_all([output, call])
    await db_session.commit()
    return output, call


async def test_agent_output_update_is_rejected(db_session):
    output, _ = await create_run_records(db_session)

    with pytest.raises(DBAPIError, match="append-only"):
        await db_session.execute(
            text("UPDATE agent_outputs SET agent = 'reviewer' WHERE id = CAST(:id AS uuid)"),
            {"id": str(output.id)},
        )
        await db_session.commit()

    await db_session.rollback()


async def test_tool_call_update_is_rejected(db_session):
    _, call = await create_run_records(db_session)

    with pytest.raises(DBAPIError, match="append-only"):
        await db_session.execute(
            text("UPDATE tool_calls SET duration_ms = 999 WHERE id = CAST(:id AS uuid)"),
            {"id": str(call.id)},
        )
        await db_session.commit()

    await db_session.rollback()
