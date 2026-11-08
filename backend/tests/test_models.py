"""Metadata-level tests for the SQLAlchemy models."""

from pgvector.sqlalchemy import Vector
from sqlalchemy import UniqueConstraint

from app.database.models import (
    AgentOutput,
    Approval,
    Asset,
    Base,
    Campaign,
    CampaignVersion,
    ComplianceReport,
    CreativeScore,
    PolicyDocument,
    ToolCall,
    WorkflowCheckpoint,
    WorkflowRun,
)

MODELS = (
    AgentOutput,
    Approval,
    Asset,
    Campaign,
    CampaignVersion,
    ComplianceReport,
    CreativeScore,
    PolicyDocument,
    ToolCall,
    WorkflowCheckpoint,
    WorkflowRun,
)

EXPECTED_TABLES = {
    "agent_outputs",
    "approvals",
    "assets",
    "campaign_versions",
    "campaigns",
    "compliance_reports",
    "creative_scores",
    "policy_documents",
    "tool_calls",
    "workflow_checkpoints",
    "workflow_runs",
}


def test_all_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_every_model_has_a_single_uuid_primary_key() -> None:
    for model in MODELS:
        primary_key = list(model.__table__.primary_key.columns)
        assert len(primary_key) == 1
        assert primary_key[0].name == "id"


def test_campaign_version_is_append_only_with_parent_link() -> None:
    table = CampaignVersion.__table__

    assert table.c.parent_version_id.nullable is True
    assert table.info["append_only"] is True

    composite = [
        index
        for index in table.indexes
        if {column.name for column in index.columns} == {"campaign_id", "version"}
    ]
    assert composite
    assert composite[0].unique is True


def test_immutable_tables_are_flagged() -> None:
    for model in (CampaignVersion, WorkflowCheckpoint, AgentOutput, ToolCall):
        assert model.__table__.info["append_only"] is True


def test_assets_store_generation_metadata() -> None:
    columns = set(Asset.__table__.c.keys())
    assert {"uri", "checksum", "model", "seed", "prompt"} <= columns


def test_policy_embedding_is_384_dimensional() -> None:
    embedding = PolicyDocument.__table__.c.embedding
    assert isinstance(embedding.type, Vector)
    assert embedding.type.dim == 384


def test_checkpoint_is_unique_per_run_and_step() -> None:
    unique_sets = [
        tuple(constraint.columns.keys())
        for constraint in WorkflowCheckpoint.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    ]
    assert ("run_id", "step") in unique_sets
