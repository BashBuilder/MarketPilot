"""Turn every error into the shared ``{error: {code, message, details?}}`` body."""

import logging
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.errors import MarketPilotError

logger = logging.getLogger(__name__)

STATUS_CODES = {
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_failed",
}


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Build the documented error envelope."""
    payload: dict[str, Any] = {"code": code, "message": message}
    if details:
        payload["details"] = details
    return JSONResponse(status_code=status_code, content={"error": payload})


async def marketpilot_handler(request: Request, exc: Exception) -> JSONResponse:
    error = cast(MarketPilotError, exc)
    return error_response(error.status_code, error.code, error.message, error.details)


async def validation_handler(request: Request, exc: Exception) -> JSONResponse:
    error = cast(RequestValidationError, exc)
    details = {
        "errors": [
            {
                "loc": [str(part) for part in item.get("loc", ())],
                "msg": str(item.get("msg", "")),
                "type": str(item.get("type", "")),
            }
            for item in error.errors()
        ]
    }
    return error_response(422, "validation_failed", "request validation failed", details)


async def lookup_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(404, "not_found", str(exc) or "not found")


async def http_handler(request: Request, exc: Exception) -> JSONResponse:
    error = cast(HTTPException, exc)
    message = error.detail if isinstance(error.detail, str) else "request failed"
    code = STATUS_CODES.get(error.status_code, "http_error")
    return error_response(error.status_code, code, message)


async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error on %s %s", request.method, request.url.path)
    return error_response(500, "internal_error", "internal server error")


def register_error_handlers(app: FastAPI) -> None:
    """Install handlers for typed, validation, lookup and unknown errors."""
    app.add_exception_handler(MarketPilotError, marketpilot_handler)
    app.add_exception_handler(RequestValidationError, validation_handler)
    app.add_exception_handler(LookupError, lookup_handler)
    app.add_exception_handler(HTTPException, http_handler)
    app.add_exception_handler(Exception, unhandled_handler)
