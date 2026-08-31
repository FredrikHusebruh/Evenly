from uuid import UUID

from fastapi import APIRouter, Depends, status
from supabase import AsyncClient

from app.dependencies import CurrentUser, get_current_user, get_request_supabase_client
from app.schemas.group import GroupOut
from app.schemas.invite import InviteCreate, InviteOut, InvitePreview
from app.services import invites as invites_service

router = APIRouter(prefix="/api/v1", tags=["invites"])


@router.post(
    "/groups/{group_id}/invites",
    response_model=InviteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create an invite code (owner only)",
)
async def create_invite(
    group_id: UUID,
    body: InviteCreate,
    user: CurrentUser = Depends(get_current_user),
) -> InviteOut:
    return await invites_service.create_invite(user.id, group_id, body)


@router.get("/groups/{group_id}/invites", response_model=list[InviteOut], summary="List active invites")
async def list_invites(
    group_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> list[InviteOut]:
    return await invites_service.list_invites(db, group_id)


@router.delete(
    "/groups/{group_id}/invites/{invite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an invite (owner only)",
)
async def revoke_invite(
    group_id: UUID,
    invite_id: UUID,
    user: CurrentUser = Depends(get_current_user),
) -> None:
    await invites_service.revoke_invite(user.id, group_id, invite_id)


@router.get("/invites/{code}", response_model=InvitePreview, summary="Preview an invite by code")
async def preview_invite(code: str) -> InvitePreview:
    return await invites_service.preview_invite(code)


@router.post("/invites/{code}/redeem", response_model=GroupOut, summary="Join a group via invite code")
async def redeem_invite(code: str, user: CurrentUser = Depends(get_current_user)) -> GroupOut:
    return await invites_service.redeem_invite(user.id, code)
