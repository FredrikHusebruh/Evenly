from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class GroupCreate(BaseModel):
    name: str


class GroupUpdate(BaseModel):
    name: str


class GroupOut(BaseModel):
    id: UUID
    name: str
    created_by: UUID
    created_at: datetime


class GroupMemberOut(BaseModel):
    group_id: UUID
    user_id: UUID
    role: Literal["owner", "member"]
    joined_at: datetime
    email: str | None = None
    username: str | None = None


class GroupDetail(GroupOut):
    members: list[GroupMemberOut]
