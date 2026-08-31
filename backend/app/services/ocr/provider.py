from datetime import date
from decimal import Decimal
from typing import Literal, Protocol

from pydantic import BaseModel

CategoryName = Literal["Dagligvarer", "Husholdning", "Alkohol", "Snacks", "Annet"]


class ParsedLineItem(BaseModel):
    description: str
    quantity: Decimal = Decimal(1)
    unit_price: Decimal
    total_price: Decimal


class ParsedReceipt(BaseModel):
    merchant: str | None
    receipt_date: date | None
    total_amount: Decimal | None
    suggested_category: CategoryName | None
    line_items: list[ParsedLineItem]


class OcrProviderError(Exception):
    """Raised by any OcrProvider implementation for every failure mode — a
    network/API error, a response that didn't call the expected tool, or a
    tool response that fails ParsedReceipt validation. The pipeline layer
    catches this (and everything else) as one uniform failure case."""


class OcrProvider(Protocol):
    async def extract_receipt(self, image_bytes: bytes, mime_type: str) -> ParsedReceipt:
        """Extract structured data from a receipt image. Raises OcrProviderError on any failure."""
        ...
