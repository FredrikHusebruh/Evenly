from uuid import UUID

import jwt
from fastapi import Depends, Header
from supabase import AsyncClient

from app.clients.jwt import verify_access_token
from app.clients.supabase import create_request_client
from app.errors import UnauthorizedError


class CurrentUser:
    def __init__(self, id: UUID, email: str | None) -> None:
        self.id = id
        self.email = email


def get_bearer_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError()
    return authorization.split(" ", 1)[1].strip()


def get_current_user(token: str = Depends(get_bearer_token)) -> CurrentUser:
    try:
        claims = verify_access_token(token)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError() from exc
    return CurrentUser(id=UUID(claims["sub"]), email=claims.get("email"))


async def get_request_supabase_client(token: str = Depends(get_bearer_token)) -> AsyncClient:
    return await create_request_client(token)
