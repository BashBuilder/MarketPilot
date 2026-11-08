"""End-to-end revision, diff and approval-gated export."""

import json
import uuid
from pathlib import Path

import pytest

from app.core.errors import ExportNotApproved
from app.database.models import RunStatus
from app.database.repositories import RunRepository, VersionRepository
from app.graph.approvals import approve_run, revise_run
from app.graph.diff import load_diff
from app.graph.workflow import run_workflow
from app.llm.fake import FakeLLMClient
from app.tools.export_tools import export_version
from tests.graph.workflow_fixtures import generated_asset, settings
from tests.graph.workflow_outputs import brief, compliance, copy, direction, research, score
from tests.graph.workflow_test_helpers import start_run


def revised_copy():
    original = copy()
    return original.model_copy(
        update={
            "variants": [
                original.variants[0].model_copy(update={"headline": "Evening hair, handled"})
            ]
        }
    )


async def test_run_revise_approve_export_and_diff(db_session, tmp_path: Path):
    run = await start_run(db_session)
    asset = await generated_asset(tmp_path)
    await run_workflow(
        run.id,
        llm=FakeLLMClient(
            [brief(), research(), copy(), direction(), compliance(asset.path), score()]
        ),
        settings=settings(tmp_path),
        session=db_session,
    )
    repository = VersionRepository(db_session)
    first = await repository.get(run.campaign_id, 1)
    assert first is not None

    exports = tmp_path / "exports"
    with pytest.raises(ExportNotApproved):
        await export_version(db_session, run.campaign_id, 1, exports)

    revised = await revise_run(
        run.id,
        "Tighten the headline",
        target_node="copywriter",
        llm=FakeLLMClient([revised_copy(), direction(), compliance(asset.path), score()]),
        settings=settings(tmp_path),
        session=db_session,
    )
    continuation_id = uuid.UUID(revised["run_id"])
    second = await repository.get(run.campaign_id, 2)
    assert second is not None
    assert second.parent_version_id == first.id

    with pytest.raises(ExportNotApproved):
        await export_version(db_session, run.campaign_id, 2, exports)

    approved = await approve_run(
        continuation_id,
        "Approved after revision",
        settings=settings(tmp_path),
        session=db_session,
    )
    assert approved == {"status": "completed", "version": 2}
    stored = await RunRepository(db_session).get(continuation_id)
    assert stored is not None and stored.status == RunStatus.COMPLETED

    path = await export_version(db_session, run.campaign_id, 2, exports)
    exported = json.loads(path.read_text(encoding="utf-8"))
    assert exported["version"] == 2
    assert exported["package"] == second.package

    diff = await load_diff(db_session, run.campaign_id, 1, 2)
    assert diff["from"] == 1 and diff["to"] == 2
    assert diff["changes"] == [
        {
            "path": "copy.variants.0.headline",
            "before": copy().variants[0].headline,
            "after": "Evening hair, handled",
        }
    ]
