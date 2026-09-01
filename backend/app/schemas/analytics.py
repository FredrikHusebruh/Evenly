from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class CategoryBreakdown(BaseModel):
    category_id: UUID | None
    category_name: str
    total: Decimal
    receipt_count: int


class SpendingTrendPoint(BaseModel):
    period: str
    total: Decimal


class MemberHistoryPoint(BaseModel):
    period: str
    paid: Decimal
    owed: Decimal


class TopItem(BaseModel):
    description: str
    count: int
    total: Decimal


class TopMerchant(BaseModel):
    merchant: str
    count: int
    total: Decimal


class TopReceipt(BaseModel):
    id: UUID
    merchant: str | None
    receipt_date: date | None
    total_amount: Decimal


class GroupAnalyticsOut(BaseModel):
    total_spent: Decimal
    receipt_count: int
    category_breakdown: list[CategoryBreakdown]
    spending_trend: list[SpendingTrendPoint]
    member_history: list[MemberHistoryPoint]
    top_items: list[TopItem]
    top_merchants: list[TopMerchant]
    top_receipts: list[TopReceipt]
