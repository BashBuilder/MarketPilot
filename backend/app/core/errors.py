"""Typed application errors with stable API codes."""

from typing import Any


class MarketPilotError(Exception):
    """Base error carrying an API code, HTTP status and optional details."""

    code = "internal_error"
    status_code = 500

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ToolError(MarketPilotError):
    code = "tool_error"

    def __init__(
        self,
        tool: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.tool = tool
        super().__init__(f"{tool}: {message}", details=details)


class ValidationFailure(MarketPilotError):
    code = "validation_failed"

    def __init__(self, agent: str, reason: str) -> None:
        self.agent = agent
        self.reason = reason
        super().__init__(f"{agent} output failed validation: {reason}")


class GuardrailViolation(MarketPilotError):
    code = "guardrail_violation"


class RetryExhausted(MarketPilotError):
    code = "retry_exhausted"

    def __init__(self, agent: str, attempts: int, last_error: str) -> None:
        self.agent = agent
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"{agent} exhausted {attempts} attempts: {last_error}",
            details={"attempts": attempts, "last_error": last_error},
        )
