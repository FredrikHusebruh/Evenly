import httpx2
import pytest
from anthropic import APIConnectionError
from pydantic import ValidationError

from app.services.ocr.claude_provider import ClaudeVisionOcrProvider
from app.services.ocr.provider import OcrProviderError, ParsedReceipt

VALID_TOOL_INPUT = {
    "merchant": "Rema 1000",
    "receipt_date": "2026-03-14",
    "total_amount": 149.5,
    "suggested_category": "Dagligvarer",
    "line_items": [
        {"description": "Melk", "quantity": 1, "unit_price": 24.9, "total_price": 24.9},
    ],
}


class _FakeContentBlock:
    def __init__(self, type_, name=None, input_=None):
        self.type = type_
        self.name = name
        self.input = input_


class _FakeMessage:
    def __init__(self, content, stop_reason="tool_use"):
        self.content = content
        self.stop_reason = stop_reason


class _FakeMessagesResource:
    def __init__(self, response=None, exception=None):
        self._response = response
        self._exception = exception

    async def create(self, **kwargs):
        if self._exception:
            raise self._exception
        return self._response


class _FakeAnthropicClient:
    def __init__(self, response=None, exception=None):
        self.messages = _FakeMessagesResource(response, exception)


def test_parsed_receipt_validates_a_good_payload():
    parsed = ParsedReceipt.model_validate(VALID_TOOL_INPUT)
    assert parsed.merchant == "Rema 1000"
    assert parsed.line_items[0].description == "Melk"


def test_parsed_receipt_rejects_missing_required_field():
    bad = {k: v for k, v in VALID_TOOL_INPUT.items() if k != "line_items"}
    with pytest.raises(ValidationError):
        ParsedReceipt.model_validate(bad)


def test_parsed_receipt_rejects_wrong_type():
    bad = {**VALID_TOOL_INPUT, "line_items": "not a list"}
    with pytest.raises(ValidationError):
        ParsedReceipt.model_validate(bad)


async def test_extract_receipt_success():
    message = _FakeMessage([_FakeContentBlock("tool_use", name="extract_receipt", input_=VALID_TOOL_INPUT)])
    provider = ClaudeVisionOcrProvider(_FakeAnthropicClient(response=message))

    result = await provider.extract_receipt(b"fake-image-bytes", "image/jpeg")
    assert result.merchant == "Rema 1000"


async def test_extract_receipt_raises_when_no_tool_use_block():
    message = _FakeMessage([_FakeContentBlock("text")], stop_reason="end_turn")
    provider = ClaudeVisionOcrProvider(_FakeAnthropicClient(response=message))

    with pytest.raises(OcrProviderError):
        await provider.extract_receipt(b"fake-image-bytes", "image/jpeg")


async def test_extract_receipt_raises_on_invalid_tool_input():
    bad_input = {**VALID_TOOL_INPUT, "line_items": "not a list"}
    message = _FakeMessage([_FakeContentBlock("tool_use", name="extract_receipt", input_=bad_input)])
    provider = ClaudeVisionOcrProvider(_FakeAnthropicClient(response=message))

    with pytest.raises(OcrProviderError):
        await provider.extract_receipt(b"fake-image-bytes", "image/jpeg")


async def test_extract_receipt_raises_on_sdk_error():
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    provider = ClaudeVisionOcrProvider(_FakeAnthropicClient(exception=APIConnectionError(request=request)))

    with pytest.raises(OcrProviderError):
        await provider.extract_receipt(b"fake-image-bytes", "image/jpeg")
