from app.services.groups import DEFAULT_CATEGORIES

RECEIPT_TOOL_NAME = "extract_receipt"

SYSTEM_PROMPT = """You are an expert OCR system specialized in extracting structured data from Norwegian retail receipts (kvitteringer). You will be shown a photo of a receipt and must extract merchant, date, total, and line items using the extract_receipt tool.

Follow these rules precisely:

1. Norwegian number formatting: receipts use comma (,) as the decimal separator and space as the thousands separator. For example, "1 249,50" means 1249.50, and "89,90" means 89.90. Always convert amounts to plain numbers with a period decimal separator (e.g. 1249.50) in your output — never include spaces, commas, or currency symbols (kr, NOK, ,-) in numeric fields.
2. Dates on Norwegian receipts are usually written DD.MM.YYYY (e.g. "14.03.2026"). Convert every date to ISO 8601 format YYYY-MM-DD.
3. If a field is unreadable, cut off, obscured, or simply absent from the image, return null for that field. Never guess or estimate a value you cannot actually read.
4. Discounts (rabatt) and bottle/can deposits (pant) must be emitted as their own separate line items, in the order they appear on the receipt, immediately after the item they apply to — do not net them into the preceding item's total_price. Represent a discount or pant as a negative total_price (and unit_price) when the receipt shows it as a deduction, with quantity 1 and a description naming what it is (e.g. "Pant" or "Rabatt").
5. suggested_category must be your best guess at which single category this receipt as a whole belongs to, chosen from exactly this list: Dagligvarer, Husholdning, Alkohol, Snacks, Annet. Dagligvarer is groceries/everyday food, Husholdning is household/cleaning goods, Alkohol is alcoholic beverages, Snacks is snacks/candy/soft drinks, Annet is anything else. If you cannot confidently tell, return null rather than guessing Annet.
6. quantity defaults to 1 when the receipt does not show an explicit quantity for a line.
7. total_price for a line item should equal quantity times unit_price as printed on the receipt; encode any per-item discount as its own separate line per rule 4 rather than adjusting unit_price.
8. You must attempt to extract every line item visible on the receipt into the line_items array. An empty line_items array should only be used if the receipt genuinely contains no purchased items at all — if you can read the merchant name and total, the itemized lines directly above the total are almost certainly legible too, so make your best effort to transcribe them individually. Do not leave line_items empty just because the receipt has many items, repeated items, or an unfamiliar layout.
9. If the same item appears on multiple separate printed lines — even with an identical description and price — extract each occurrence as its own separate entry in line_items, matching the receipt's own layout. Do not combine repeated lines into a single entry with a higher quantity.
10. Norwegian receipts often print a VAT/discount-rate percentage (e.g. "15%") next to each line item's price — this percentage is not part of the item's price and should be ignored; use only the printed currency amount for unit_price and total_price.
11. Call the extract_receipt tool exactly once with your full extraction. Do not respond with plain text."""

USER_INSTRUCTION = "Extract the structured data from this Norwegian receipt image using the extract_receipt tool."


def build_user_message(image_b64: str, mime_type: str) -> dict:
    """The single user-turn message sent to Claude — the image followed by
    the extraction instruction. Pure/deterministic, so it's testable
    without any network call."""
    return {
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", "media_type": mime_type, "data": image_b64}},
            {"type": "text", "text": USER_INSTRUCTION},
        ],
    }


EXTRACT_RECEIPT_TOOL = {
    "name": RECEIPT_TOOL_NAME,
    "description": "Record the structured data extracted from a Norwegian receipt image.",
    "strict": True,
    "input_examples": [
        {
            "merchant": "Kiwi 364 Byporten",
            "receipt_date": "2024-12-10",
            "total_amount": 91.20,
            "suggested_category": "Dagligvarer",
            "line_items": [
                {"description": "Laban Seigmenn 260g", "quantity": 1, "unit_price": 12.90, "total_price": 12.90},
                {"description": "Laban Seigmenn 260g", "quantity": 1, "unit_price": 12.90, "total_price": 12.90},
                {"description": "Laban Seigmenn 260g", "quantity": 1, "unit_price": 12.90, "total_price": 12.90},
                {"description": "Marsipanpølser 5stk", "quantity": 1, "unit_price": 9.90, "total_price": 9.90},
                {"description": "Marsipanpølser 5stk", "quantity": 1, "unit_price": 9.90, "total_price": 9.90},
                {"description": "Marsipanpølser 5stk", "quantity": 1, "unit_price": 9.90, "total_price": 9.90},
                {"description": "Marsipanpølser 5stk", "quantity": 1, "unit_price": 9.90, "total_price": 9.90},
                {"description": "Laban Seigmenn 260g", "quantity": 1, "unit_price": 12.90, "total_price": 12.90},
            ],
        },
    ],
    "input_schema": {
        "type": "object",
        "properties": {
            "merchant": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "description": "Store/merchant name, or null if unreadable.",
            },
            "receipt_date": {
                "anyOf": [{"type": "string", "format": "date"}, {"type": "null"}],
                "description": "ISO 8601 YYYY-MM-DD, or null if unreadable.",
            },
            "total_amount": {
                "anyOf": [{"type": "number"}, {"type": "null"}],
                "description": "Grand total as a plain decimal, or null if unreadable.",
            },
            "suggested_category": {
                "anyOf": [{"type": "string", "enum": list(DEFAULT_CATEGORIES)}, {"type": "null"}],
                "description": "Best-guess category for the receipt as a whole, or null if unclear.",
            },
            "line_items": {
                "type": "array",
                "description": "Every line item, including discount/pant lines as separate entries, in receipt order.",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit_price": {"type": "number"},
                        "total_price": {"type": "number"},
                    },
                    "required": ["description", "quantity", "unit_price", "total_price"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["merchant", "receipt_date", "total_amount", "suggested_category", "line_items"],
        "additionalProperties": False,
    },
}
