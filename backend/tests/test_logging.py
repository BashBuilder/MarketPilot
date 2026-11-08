"""Tests for JSON logging and run-scoped context."""

import json
import logging

import pytest

from app.core.logging import (
    JsonFormatter,
    agent,
    campaign_id,
    configure_logging,
    log_context,
    run_id,
    step,
)


def make_record(message: str = "hello") -> logging.LogRecord:
    return logging.LogRecord(
        name="marketpilot.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=None,
        exc_info=None,
    )


def test_formatter_includes_bound_context() -> None:
    with log_context(
        run_id="run-1",
        campaign_id="campaign-1",
        agent="brief",
        step="2",
    ):
        payload = json.loads(JsonFormatter().format(make_record()))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "marketpilot.test"
    assert payload["message"] == "hello"
    assert payload["run_id"] == "run-1"
    assert payload["campaign_id"] == "campaign-1"
    assert payload["agent"] == "brief"
    assert payload["step"] == "2"
    assert "T" in payload["timestamp"]


def test_formatter_omits_unset_context() -> None:
    payload = json.loads(JsonFormatter().format(make_record()))

    assert "run_id" not in payload
    assert "campaign_id" not in payload
    assert "agent" not in payload
    assert "step" not in payload


def test_context_is_reset_after_block() -> None:
    assert run_id.get() is None

    with log_context(run_id="run-1"):
        assert run_id.get() == "run-1"

    assert run_id.get() is None


def test_context_is_reset_after_exception() -> None:
    with pytest.raises(RuntimeError):
        with log_context(agent="copywriter"):
            raise RuntimeError("boom")

    assert agent.get() is None


def test_unknown_context_field_is_rejected() -> None:
    with pytest.raises(KeyError, match="unknown_field"):
        with log_context(unknown_field="x"):
            pass


def test_configure_logging_is_idempotent() -> None:
    configure_logging("DEBUG")
    configure_logging("WARNING")

    root = logging.getLogger()
    json_handlers = [
        handler for handler in root.handlers if isinstance(handler.formatter, JsonFormatter)
    ]

    assert root.level == logging.WARNING
    assert len(json_handlers) == 1


def test_context_variables_exist_for_all_fields() -> None:
    assert run_id.get() is None
    assert campaign_id.get() is None
    assert agent.get() is None
    assert step.get() is None
