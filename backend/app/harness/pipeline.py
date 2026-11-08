"""Canonical pipeline order and terminal gate markers."""

from typing import Final

PIPELINE_NODES: Final[tuple[str, ...]] = (
    "brief",
    "research",
    "copywriter",
    "creative_director",
    "designer",
    "compliance",
    "reviewer",
    "supervisor",
)
HUMAN_GATE: Final = "human"
DONE: Final = "done"

_NEXT_NODE: Final[dict[str, str]] = {
    **{node: PIPELINE_NODES[index + 1] for index, node in enumerate(PIPELINE_NODES[:-1])},
    PIPELINE_NODES[-1]: HUMAN_GATE,
    HUMAN_GATE: DONE,
    DONE: DONE,
}


def next_node(node: str) -> str:
    """Return the node that follows ``node`` in the pipeline."""
    try:
        return _NEXT_NODE[node]
    except KeyError as error:
        raise ValueError(f"unknown pipeline node: {node}") from error
