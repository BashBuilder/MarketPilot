"""Audited async wrapper for every tool invocation."""

import hashlib
import json
import logging
import time
import uuid
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel

from app.core.errors import GuardrailViolation
from app.core.logging import log_context
from app.database.repositories.tool_calls import ToolCallRepository
from app.harness.guardrails import RunGuardrails
from app.harness.registry import ToolRegistry


class ToolCallMiddleware:
    """Check, execute, time and audit one tool call for a run."""

    def __init__(
        self,
        *,
        registry: ToolRegistry,
        guardrails: RunGuardrails,
        repository: ToolCallRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self._registry = registry
        self._guardrails = guardrails
        self._repository = repository
        self._logger = logger or logging.getLogger(__name__)

    async def call_tool(
        self,
        *,
        run_id: uuid.UUID,
        agent: str,
        step: str,
        tool: str,
        args: BaseModel | Mapping[str, Any],
        cost: float = 0.0,
    ) -> Any:
        args_hash = _hash_tool_args(args)
        started = time.perf_counter()
        with log_context(run_id=str(run_id), agent=agent, step=step):
            try:
                spec = self._registry.get_tool(agent, tool)
                self._guardrails.check_call(tool)
                self._guardrails.check_cost(cost)
                validated = spec.args_model.model_validate(args)
                result = await spec.handler(validated)
            except GuardrailViolation as error:
                await self._record(
                    run_id=run_id,
                    agent=agent,
                    tool=tool,
                    args_hash=args_hash,
                    duration_ms=_elapsed_ms(started),
                    status="denied",
                    cost=0.0,
                    error=str(error),
                )
                self._logger.warning("tool call denied: %s", tool)
                raise
            except Exception as error:
                await self._record(
                    run_id=run_id,
                    agent=agent,
                    tool=tool,
                    args_hash=args_hash,
                    duration_ms=_elapsed_ms(started),
                    status="error",
                    cost=0.0,
                    error=str(error),
                )
                self._logger.exception("tool call failed: %s", tool)
                raise

            self._guardrails.record_cost(cost)
            await self._record(
                run_id=run_id,
                agent=agent,
                tool=tool,
                args_hash=args_hash,
                duration_ms=_elapsed_ms(started),
                status="success",
                cost=cost,
            )
            self._logger.info("tool call succeeded: %s", tool)
            return result

    async def _record(
        self,
        *,
        run_id: uuid.UUID,
        agent: str,
        tool: str,
        args_hash: str,
        duration_ms: int,
        status: str,
        cost: float,
        error: str | None = None,
    ) -> None:
        await self._repository.create(
            run_id=run_id,
            agent=agent,
            tool=tool,
            args_hash=args_hash,
            duration_ms=duration_ms,
            status=status,
            cost=cost,
            error=error,
        )


def _hash_tool_args(args: BaseModel | Mapping[str, Any]) -> str:
    payload = args.model_dump(mode="json") if isinstance(args, BaseModel) else dict(args)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _elapsed_ms(started: float) -> int:
    return max(0, int((time.perf_counter() - started) * 1000))
