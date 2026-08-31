from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class MemberSplit(BaseModel):
    user_id: UUID
    personal_total: Decimal
    shared_share: Decimal
    owed_total: Decimal


class SplitResult(BaseModel):
    shared_total: Decimal
    excluded_total: Decimal
    member_splits: list[MemberSplit]
    mismatch: bool


class Settlement(BaseModel):
    from_user: UUID
    to_user: UUID
    amount: Decimal


class SettleUpOut(BaseModel):
    settlements: list[Settlement]
