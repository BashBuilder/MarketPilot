"""DeepSeek client using the OpenAI-compatible chat-completions API."""

from collections.abc import Mapping, Sequence
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.errors import ToolError, ValidationFailure
from app.llm.base import LLMError, OutputT, TokenUsage

DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TIMEOUT_SECONDS = 60.0


class DeepSeekClient:
    """Async DeepSeek client with JSON-mode replies and hard request timeouts."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        model: str = DEFAULT_MODEL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._http_client = http_client

    async def complete(
        self,
        messages: Sequence[Mapping[str, str]],
        output_model: type[OutputT] | None = None,
    ) -> tuple[OutputT | str, TokenUsage]:
        if not messages:
            raise LLMError("DeepSeek requires at least one message")
        payload = await self._post(messages)
        content = self._extract_content(payload)
        usage = self._extract_usage(payload)
        if output_model is None:
            return content, usage
        return self._parse(content, output_model), usage

    async def _post(self, messages: Sequence[Mapping[str, str]]) -> dict[str, Any]:
        url = f"{self._settings.deepseek_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model,
            "messages": [dict(message) for message in messages],
            "response_format": {"type": "json_object"},
            "stream": False,
        }
        try:
            if self._http_client is None:
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    response = await client.post(url, json=body, headers=headers)
            else:
                response = await self._http_client.post(
                    url,
                    json=body,
                    headers=headers,
                    timeout=self._timeout_seconds,
                )
            response.raise_for_status()
        except httpx.TimeoutException as error:
            raise ToolError("deepseek", "request timed out", retryable=True) from error
        except httpx.HTTPStatusError as error:
            status = error.response.status_code
            if 500 <= status < 600:
                raise ToolError(
                    "deepseek",
                    f"HTTP {status} response",
                    retryable=True,
                ) from error
            raise LLMError(f"DeepSeek request failed: {error}") from error
        except httpx.HTTPError as error:
            raise LLMError(f"DeepSeek request failed: {error}") from error
        try:
            payload = response.json()
        except ValueError as error:
            raise LLMError("DeepSeek returned invalid JSON") from error
        if not isinstance(payload, dict):
            raise LLMError("DeepSeek returned an unexpected payload")
        return payload

    @staticmethod
    def _extract_content(payload: dict[str, Any]) -> str:
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise LLMError("DeepSeek response is missing choices[0].message.content") from error
        if not isinstance(content, str) or not content.strip():
            raise LLMError("DeepSeek returned empty content")
        return content

    @staticmethod
    def _extract_usage(payload: dict[str, Any]) -> TokenUsage:
        raw = payload.get("usage")
        if not isinstance(raw, dict):
            return TokenUsage()
        prompt_tokens = _non_negative_int(raw.get("prompt_tokens"))
        completion_tokens = _non_negative_int(raw.get("completion_tokens"))
        total_tokens = _non_negative_int(raw.get("total_tokens"))
        if total_tokens == 0:
            total_tokens = prompt_tokens + completion_tokens
        return TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    @staticmethod
    def _parse(content: str, output_model: type[OutputT]) -> OutputT:
        try:
            return output_model.model_validate_json(_json_payload(content))
        except ValidationError as error:
            raise ValidationFailure(output_model.__name__, str(error)) from error


def _non_negative_int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return 0
    return value


def _json_payload(content: str) -> str:
    """Strip Markdown fences and surrounding prose from a JSON object reply."""
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return text[start : end + 1]
    return text
