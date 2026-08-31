from decimal import Decimal

from app.services.groups import DEFAULT_CATEGORIES
from app.services.ocr.prompts import EXTRACT_RECEIPT_TOOL, SYSTEM_PROMPT, build_user_message
from app.services.ocr.provider import ParsedReceipt


def test_user_message_includes_image_and_instruction():
    message = build_user_message("BASE64DATA", "image/jpeg")

    assert message["role"] == "user"
    image_block, text_block = message["content"]

    assert image_block["type"] == "image"
    assert image_block["source"] == {"type": "base64", "media_type": "image/jpeg", "data": "BASE64DATA"}
    assert text_block["type"] == "text"
    assert "extract_receipt" in text_block["text"]


def test_category_enum_stays_in_sync_with_default_categories():
    # suggested_category is expressed as anyOf[{enum: [...]}, {type: null}] rather than
    # a type-array + mixed enum — Anthropic's strict-mode JSON Schema subset documents
    # anyOf as the supported way to express a nullable field, not {"type": [x, "null"]}.
    category_branch = EXTRACT_RECEIPT_TOOL["input_schema"]["properties"]["suggested_category"]["anyOf"][0]
    assert category_branch["enum"] == list(DEFAULT_CATEGORIES)


def test_system_prompt_covers_key_norwegian_receipt_rules():
    assert "comma" in SYSTEM_PROMPT.lower()
    assert "yyyy-mm-dd" in SYSTEM_PROMPT.lower()
    assert "null" in SYSTEM_PROMPT.lower()
    assert "pant" in SYSTEM_PROMPT.lower()


def test_system_prompt_instructs_always_attempting_line_items():
    # Regression guard for the real bug this rule fixes: Claude returned a
    # correct merchant/date/total but an empty line_items array for a
    # receipt with 8 clearly legible items — the model needs to be told
    # explicitly not to default to an empty array out of caution.
    assert "empty line_items array" in SYSTEM_PROMPT
    assert "vat" in SYSTEM_PROMPT.lower()


def test_input_example_is_valid_and_internally_consistent():
    """The worked example must itself validate against ParsedReceipt (the
    API rejects an example that doesn't match input_schema with a 400), and
    its line items must actually sum to its total — an inconsistent example
    would actively teach the model the wrong thing."""
    example = EXTRACT_RECEIPT_TOOL["input_examples"][0]
    parsed = ParsedReceipt.model_validate(example)

    assert len(parsed.line_items) > 0
    items_total = sum((li.total_price for li in parsed.line_items), Decimal(0))
    assert items_total == parsed.total_amount
