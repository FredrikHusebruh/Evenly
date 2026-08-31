from uuid import UUID

from pydantic import BaseModel


class MeOut(BaseModel):
    id: UUID
    email: str | None
