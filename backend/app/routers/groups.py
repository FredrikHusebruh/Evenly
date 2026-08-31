from uuid import UUID

from fastapi import APIRouter, Depends, status
from supabase import AsyncClient

from app.dependencies import CurrentUser, get_current_user, get_request_supabase_client
from app.schemas.group import GroupCreate, GroupDetail, GroupMemberOut, GroupOut, GroupUpdate
from app.services import groups as groups_service

router = APIRouter(prefix="/api/v1/groups", tags=["groups"])


@router.post("", response_model=GroupOut, status_code=status.HTTP_201_CREATED, summary="Create a group")
async def create_group(
    body: GroupCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> GroupOut:
    return await groups_service.create_group(db, user.id, body)


@router.get("", response_model=list[GroupOut], summary="List the caller's groups")
async def list_groups(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> list[GroupOut]:
    return await groups_service.list_groups_for_user(db)


@router.get("/{group_id}", response_model=GroupDetail, summary="Get a group and its members")
async def get_group(
    group_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> GroupDetail:
    return await groups_service.get_group(db, group_id)


@router.patch("/{group_id}", response_model=GroupOut, summary="Rename a group (owner only)")
async def rename_group(
    group_id: UUID,
    body: GroupUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> GroupOut:
    return await groups_service.rename_group(db, group_id, body)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a group (owner only)")
async def delete_group(
    group_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> None:
    await groups_service.delete_group(db, group_id)


@router.get("/{group_id}/members", response_model=list[GroupMemberOut], summary="List group members")
async def list_members(
    group_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> list[GroupMemberOut]:
    return await groups_service.list_members(db, group_id)


@router.delete(
    "/{group_id}/members/{member_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Leave a group, or remove a member (owner)",
)
async def remove_member(
    group_id: UUID,
    member_user_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> None:
    await groups_service.remove_member(db, group_id, member_user_id)
