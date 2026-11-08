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
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.tool = tool
        self.retryable = retryable
        merged_details = {**(details or {}), "retryable": retryable}
        super().__init__(f"{tool}: {message}", details=merged_details)


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


class RunNotAwaitingApproval(MarketPilotError):
    code = "run_not_awaiting_approval"
    status_code = 409

    def __init__(self, run_id: str, status: str) -> None:
        self.run_id = run_id
        self.status = status
        super().__init__(
            f"run {run_id} is {status}, not awaiting approval",
            details={"run_id": run_id, "status": status},
        )


class RevisionCommentRequired(MarketPilotError):
    code = "revision_comment_required"
    status_code = 422

    def __init__(self) -> None:
        super().__init__("a revision requires a non-empty comment")


class VersionNotFound(MarketPilotError):
    code = "version_not_found"
    status_code = 404

    def __init__(self, campaign_id: str, version: int) -> None:
        self.campaign_id = campaign_id
        self.version = version
        super().__init__(
            f"campaign {campaign_id} has no version {version}",
            details={"campaign_id": campaign_id, "version": version},
        )


class ExportNotApproved(MarketPilotError):
    code = "export_not_approved"
    status_code = 409

    def __init__(self, campaign_id: str, version: int) -> None:
        self.campaign_id = campaign_id
        self.version = version
        super().__init__(
            f"version {version} of campaign {campaign_id} has not been approved",
            details={"campaign_id": campaign_id, "version": version},
        )
