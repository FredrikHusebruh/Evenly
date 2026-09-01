from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.line_item import LineItemOut

OcrStatus = Literal["pending", "processing", "succeeded", "failed"]


class ReceiptCreate(BaseModel):
    image_path: str


class ReceiptUpdate(BaseModel):
    merchant: str | None = None
    total_amount: Decimal | None = None
    receipt_date: date | None = None
    category_id: UUID | None = None
    is_done: bool | None = None


class ReceiptOut(BaseModel):
    id: UUID
    group_id: UUID
    uploaded_by: UUID
    category_id: UUID | None
    merchant: str | None
    total_amount: Decimal | None
    currency: str
    receipt_date: date | None
    image_path: str | None
    created_at: datetime
    ocr_status: OcrStatus
    ocr_error: str | None
    is_done: bool
    # Only populated by list_receipts (the receipt history view) — None elsewhere.
    shared_total: Decimal | None = None


class ReceiptDetail(ReceiptOut):
    line_items: list[LineItemOut]
    items_total: Decimal
    mismatch: bool


class ReceiptStatusOut(BaseModel):
    ocr_status: OcrStatus
    ocr_error: str | None
