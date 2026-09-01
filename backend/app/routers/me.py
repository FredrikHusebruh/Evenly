from fastapi import APIRouter, Depends
from supabase import AsyncClient

from app.dependencies import CurrentUser, get_current_user, get_request_supabase_client
from app.schemas.me import MeOut, MeUpdate
from app.services import me as me_service

router = APIRouter(prefix="/api/v1/me", tags=["me"])


@router.get("", response_model=MeOut, summary="Get the caller's identity")
async def get_me(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> MeOut:
    return await me_service.get_me(db, user)


@router.patch("", response_model=MeOut, summary="Update the caller's username")
async def update_me(
    body: MeUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> MeOut:
    return await me_service.update_me(db, user, body)
