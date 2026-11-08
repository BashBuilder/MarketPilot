"""Versioned prompt loading for the LLM agents."""

import re
from pathlib import Path
from typing import NamedTuple

PROMPTS_DIR = Path(__file__).resolve().parent
_AGENT_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


class PromptDocument(NamedTuple):
    """Prompt body and the version declared on its first line."""

    text: str
    version: str


def load_prompt(agent_name: str) -> PromptDocument:
    """Load ``<agent_name>.md`` and split its ``version:`` header from the body."""
    if not _AGENT_NAME.fullmatch(agent_name):
        raise ValueError(f"invalid agent name: {agent_name!r}")

    path = PROMPTS_DIR / f"{agent_name}.md"
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise FileNotFoundError(f"no prompt found for agent {agent_name}") from error

    first_line, _, body = raw.partition("\n")
    label, separator, version = first_line.partition(":")
    if not separator or label.strip().lower() != "version" or not version.strip():
        raise ValueError(f"prompt {path.name} must start with a 'version:' line")

    text = body.strip()
    if not text:
        raise ValueError(f"prompt {path.name} has no body")
    return PromptDocument(text=text, version=version.strip())
