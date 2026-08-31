from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

LineItemStatus = Literal["shared", "personal", "excluded"]


class LineItemCreate(BaseModel):
    description: str
    quantity: Decimal = Decimal(1)
    unit_price: Decimal
    total_price: Decimal


class LineItemUpdate(BaseModel):
    description: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    total_price: Decimal | None = None
    status: LineItemStatus | None = None
    assigned_to: UUID | None = None


class LineItemOut(BaseModel):
    id: UUID
    receipt_id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    created_at: datetime
    status: LineItemStatus
    assigned_to: UUID | None
