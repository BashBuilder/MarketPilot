"""Tests for the queued fake LLM client."""

import pytest

from app.agents.outputs import CampaignBrief, RouteDecision
from app.core.errors import ValidationFailure
from app.llm.base import LLMError, TokenUsage
from app.llm.fake import FakeLLMClient

VALID = {
    "product": "Lumen Hair Serum",
    "goal": "Increase trial among adults aged 25 to 40",
    "audience": "Busy professionals who want low-effort hair care",
    "tone": "Confident and calm",
    "channels": ["instagram", "search"],
    "constraints": ["No medical claims"],
}

MESSAGES = [{"role": "user", "content": "Write a brief."}]


async def test_queued_mapping_is_validated_into_requested_model() -> None:
    usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    client = FakeLLMClient([VALID], usage=usage)

    result, result_usage = await client.complete(MESSAGES, CampaignBrief)

    assert isinstance(result, CampaignBrief)
    assert result.product == "Lumen Hair Serum"
    assert result_usage == usage
    assert client.remaining == 0


async def test_queued_text_is_returned_without_a_model() -> None:
    client = FakeLLMClient(["plain text reply"])

    result, usage = await client.complete(MESSAGES)

    assert result == "plain text reply"
    assert usage == TokenUsage()


async def test_queued_model_instance_is_returned_as_is() -> None:
    brief = CampaignBrief.model_validate(VALID)
    client = FakeLLMClient([brief])

    result, _ = await client.complete(MESSAGES, CampaignBrief)

    assert result is brief


async def test_empty_queue_raises_llm_error() -> None:
    client = FakeLLMClient()

    with pytest.raises(LLMError, match="no queued responses"):
        await client.complete(MESSAGES, CampaignBrief)


async def test_wrong_pydantic_model_is_rejected() -> None:
    brief = CampaignBrief.model_validate(VALID)
    client = FakeLLMClient([brief])

    with pytest.raises(LLMError, match="expected RouteDecision"):
        await client.complete(MESSAGES, RouteDecision)


async def test_invalid_payload_is_rejected() -> None:
    client = FakeLLMClient([{"product": "only a product"}])

    with pytest.raises(ValidationFailure, match="CampaignBrief output failed validation"):
        await client.complete(MESSAGES, CampaignBrief)


async def test_calls_are_recorded() -> None:
    client = FakeLLMClient(["one", "two"])

    await client.complete(MESSAGES)
    await client.complete([{"role": "system", "content": "second"}])

    assert client.calls == [
        MESSAGES,
        [{"role": "system", "content": "second"}],
    ]
