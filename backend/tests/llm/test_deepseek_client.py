"""Tests for the DeepSeek client using a mocked HTTP transport."""

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from app.agents.outputs import CampaignBrief
from app.core.config import Settings
from app.core.errors import ToolError, ValidationFailure
from app.llm.base import LLMError
from app.llm.deepseek import DeepSeekClient

VALID = {
    "product": "Lumen Hair Serum",
    "goal": "Increase trial among adults aged 25 to 40",
    "audience": "Busy professionals who want low-effort hair care",
    "tone": "Confident and calm",
    "channels": ["instagram", "search"],
    "constraints": ["No medical claims"],
}

MESSAGES = [{"role": "user", "content": "Write a brief as JSON."}]
Handler = Callable[[httpx.Request], httpx.Response]


def settings() -> Settings:
    return Settings(
        deepseek_api_key="test-key",
        database_url="postgresql+asyncpg://user:pass@localhost:5432/marketpilot",
        redis_url="redis://localhost:6379/0",
        _env_file=None,
    )


def response(content: str, usage: dict[str, Any] | None = None) -> httpx.Response:
    body: dict[str, Any] = {"choices": [{"message": {"content": content}}]}
    if usage is not None:
        body["usage"] = usage
    return httpx.Response(200, json=body)


async def call(
    handler: Handler,
    *,
    output_model: type[CampaignBrief] | None = CampaignBrief,
) -> tuple[CampaignBrief | str, Any]:
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = DeepSeekClient(settings=settings(), http_client=http_client)
        return await client.complete(MESSAGES, output_model)


async def test_complete_parses_model_usage_and_request() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers["authorization"]
        captured["body"] = json.loads(request.content)
        return response(
            json.dumps(VALID),
            {"prompt_tokens": 11, "completion_tokens": 22, "total_tokens": 33},
        )

    result, usage = await call(handler)

    assert isinstance(result, CampaignBrief)
    assert result.channels == ["instagram", "search"]
    assert usage.prompt_tokens == 11
    assert usage.completion_tokens == 22
    assert usage.total_tokens == 33
    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["auth"] == "Bearer test-key"
    assert captured["body"]["model"] == "deepseek-chat"
    assert captured["body"]["response_format"] == {"type": "json_object"}
    assert captured["body"]["messages"] == MESSAGES


async def test_code_fenced_json_is_accepted() -> None:
    content = "Here is the brief:\n```json\n" + json.dumps(VALID) + "\n```"

    result, _ = await call(lambda request: response(content))

    assert isinstance(result, CampaignBrief)
    assert result.product == "Lumen Hair Serum"


async def test_missing_total_tokens_is_summed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return response(
            json.dumps(VALID),
            {"prompt_tokens": 5, "completion_tokens": 7},
        )

    _, usage = await call(handler)

    assert usage.total_tokens == 12


async def test_text_reply_is_returned_without_a_model() -> None:
    result, usage = await call(lambda request: response("hello"), output_model=None)

    assert result == "hello"
    assert usage.total_tokens == 0


async def test_timeout_raises_retryable_tool_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    with pytest.raises(ToolError) as excinfo:
        await call(handler)

    assert excinfo.value.tool == "deepseek"
    assert excinfo.value.retryable is True
    assert excinfo.value.details["retryable"] is True
    assert "timed out" in str(excinfo.value)


async def test_http_5xx_raises_retryable_tool_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="upstream unavailable")

    with pytest.raises(ToolError) as excinfo:
        await call(handler)

    assert excinfo.value.retryable is True
    assert "HTTP 503" in str(excinfo.value)


async def test_http_4xx_remains_non_retryable_llm_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="bad request")

    with pytest.raises(LLMError, match="request failed"):
        await call(handler)


async def test_malformed_json_raises_validation_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return response("not json at all")

    with pytest.raises(ValidationFailure) as excinfo:
        await call(handler)

    assert "Invalid JSON" in excinfo.value.reason
    assert "Invalid JSON" in str(excinfo.value)
    assert excinfo.value.agent == "CampaignBrief"


async def test_schema_mismatch_raises_validation_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return response(json.dumps({"product": "only a product"}))

    with pytest.raises(ValidationFailure) as excinfo:
        await call(handler)

    assert "goal" in excinfo.value.reason
    assert "Field required" in excinfo.value.reason
    assert "goal" in str(excinfo.value)


async def test_missing_content_is_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": []})

    with pytest.raises(LLMError, match="missing choices"):
        await call(handler)


async def test_empty_messages_are_rejected_without_a_request() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("HTTP should not be called")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = DeepSeekClient(settings=settings(), http_client=http_client)
        with pytest.raises(LLMError, match="at least one message"):
            await client.complete([], CampaignBrief)
