"""Tests for versioned agent prompt loading."""

from pathlib import Path

import pytest

from app.agents.prompts import loader
from app.agents.prompts.loader import load_prompt


def test_load_prompt_returns_body_and_version() -> None:
    prompt = load_prompt("brief")

    assert prompt.version == "1"
    assert prompt.text.startswith("You are the Brief agent")
    assert "version:" not in prompt.text


def test_missing_prompt_raises_file_not_found() -> None:
    with pytest.raises(FileNotFoundError, match="no prompt found"):
        load_prompt("missing_agent")


def test_invalid_agent_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="invalid agent name"):
        load_prompt("../secret")


def test_prompt_without_version_header_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "broken.md").write_text("You are broken.\n", encoding="utf-8")
    monkeypatch.setattr(loader, "PROMPTS_DIR", tmp_path)

    with pytest.raises(ValueError, match="version:"):
        load_prompt("broken")


def test_prompt_without_a_body_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "empty.md").write_text("version: 1\n", encoding="utf-8")
    monkeypatch.setattr(loader, "PROMPTS_DIR", tmp_path)

    with pytest.raises(ValueError, match="no body"):
        load_prompt("empty")
