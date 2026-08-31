import base64

import anthropic
from anthropic import AsyncAnthropic
from pydantic import ValidationError

from app.services.ocr.prompts import EXTRACT_RECEIPT_TOOL, RECEIPT_TOOL_NAME, SYSTEM_PROMPT, build_user_message
from app.services.ocr.provider import OcrProviderError, ParsedReceipt

MODEL = "claude-sonnet-5"
MAX_TOKENS = 8192  # headroom for a long grocery receipt; tune after live testing


class ClaudeVisionOcrProvider:
    """OcrProvider backed by Claude's vision API via forced tool-use."""

    def __init__(self, client: AsyncAnthropic) -> None:
        self._client = client

    async def extract_receipt(self, image_bytes: bytes, mime_type: str) -> ParsedReceipt:
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        try:
            response = await self._client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=[EXTRACT_RECEIPT_TOOL],
                tool_choice={"type": "tool", "name": RECEIPT_TOOL_NAME},
                messages=[build_user_message(image_b64, mime_type)],
            )
        except anthropic.APIError as exc:
            # Single broad catch is deliberate: the pipeline treats every
            # provider failure identically (mark the receipt failed). The
            # SDK already retries 429/5xx/connection errors internally.
            raise OcrProviderError("Claude API request failed") from exc

        tool_use = next(
            (b for b in response.content if b.type == "tool_use" and b.name == RECEIPT_TOOL_NAME), None
        )
        if tool_use is None:
            raise OcrProviderError(f"Model did not call {RECEIPT_TOOL_NAME}; stop_reason={response.stop_reason}")

        try:
            return ParsedReceipt.model_validate(tool_use.input)
        except ValidationError as exc:
            raise OcrProviderError("Model tool input failed ParsedReceipt validation") from exc
