"""Per-run tool-call and cost guardrails, plus prompt fencing."""

import html
import re
from collections.abc import Mapping

from app.core.config import Settings, get_settings
from app.core.errors import GuardrailViolation

IMAGE_TOOLS = frozenset({"generate_image", "edit_image", "generate_video"})
SEARCH_TOOLS = frozenset({"search_tools"})

_TOOL_BUCKETS: Mapping[str, str] = {
    **{tool: "image" for tool in IMAGE_TOOLS},
    **{tool: "search" for tool in SEARCH_TOOLS},
}

_CLOSING_TAG = re.compile(r"</\s*untrusted\s*>", re.IGNORECASE)


class RunGuardrails:
    """Track one run's tool usage and reject calls that exceed configured caps."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._counts = {"image": 0, "search": 0}
        self._spent = 0.0

    @property
    def spent(self) -> float:
        """Total actual spend recorded for this run."""
        return self._spent

    def check_call(self, tool: str) -> None:
        """Count a tool call or raise when its shared per-run cap is exhausted."""
        bucket = _TOOL_BUCKETS.get(tool)
        if bucket is None:
            return
        cap = self._cap_for(bucket)
        used = self._counts[bucket]
        if used >= cap:
            raise GuardrailViolation(f"Per-run {bucket} call cap of {cap} exceeded by tool {tool}")
        self._counts[bucket] = used + 1

    def check_cost(self, projected_cost: float) -> None:
        """Raise when projected spend would exceed the per-run cost cap."""
        self._validate_cost(projected_cost)
        projected = self._spent + projected_cost
        if projected > self._settings.cost_cap_per_run:
            raise GuardrailViolation(
                f"Per-run cost cap of {self._settings.cost_cap_per_run:.2f} exceeded "
                f"(projected {projected:.2f})"
            )

    def record_cost(self, actual_cost: float) -> None:
        """Add actual spend after a successful call, enforcing the cost cap."""
        self._validate_cost(actual_cost)
        self.check_cost(actual_cost)
        self._spent += actual_cost

    def _cap_for(self, bucket: str) -> int:
        if bucket == "image":
            return self._settings.max_image_calls_per_run
        return self._settings.max_search_calls_per_run

    @staticmethod
    def _validate_cost(cost: float) -> None:
        if cost < 0:
            raise ValueError("cost must be non-negative")


def fence_untrusted(text: str, source: str) -> str:
    """Wrap untrusted prompt text in a source-labelled delimiter block."""
    safe_source = html.escape(source, quote=True)
    safe_text = _CLOSING_TAG.sub("&lt;/untrusted&gt;", text)
    return f'<untrusted source="{safe_source}">\n{safe_text}\n</untrusted>'
