from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class InviteCreate(BaseModel):
    expires_at: datetime | None = None
    max_uses: int | None = None


class InviteOut(BaseModel):
    id: UUID
    group_id: UUID
    code: str
    created_by: UUID
    created_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    max_uses: int | None
    use_count: int


class InvitePreview(BaseModel):
    group_id: UUID
    group_name: str
    member_count: int
