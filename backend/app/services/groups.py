from uuid import UUID

from supabase import AsyncClient

from app.clients.supabase import unwrap_maybe_single
from app.errors import NotFoundError
from app.schemas.group import GroupCreate, GroupDetail, GroupMemberOut, GroupOut, GroupUpdate

DEFAULT_CATEGORIES = ["Dagligvarer", "Husholdning", "Alkohol", "Snacks", "Annet"]


async def create_group(db: AsyncClient, user_id: UUID, body: GroupCreate) -> GroupOut:
    group_res = await db.table("groups").insert({"name": body.name, "created_by": str(user_id)}).execute()
    group = group_res.data[0]

    await db.table("group_members").insert(
        {"group_id": group["id"], "user_id": str(user_id), "role": "owner"}
    ).execute()

    await db.table("categories").insert(
        [{"group_id": group["id"], "name": name} for name in DEFAULT_CATEGORIES]
    ).execute()

    return GroupOut.model_validate(group)


async def list_groups_for_user(db: AsyncClient) -> list[GroupOut]:
    res = await db.table("groups").select("*").order("created_at", desc=True).execute()
    return [GroupOut.model_validate(g) for g in res.data]


async def get_group(db: AsyncClient, group_id: UUID) -> GroupDetail:
    group_res = await db.table("groups").select("*").eq("id", str(group_id)).maybe_single().execute()
    group = unwrap_maybe_single(group_res)
    if not group:
        raise NotFoundError("Group not found")

    members_res = await db.table("group_members").select("*").eq("group_id", str(group_id)).execute()

    return GroupDetail(
        **group,
        members=[GroupMemberOut.model_validate(m) for m in members_res.data],
    )


async def list_members(db: AsyncClient, group_id: UUID) -> list[GroupMemberOut]:
    res = await db.table("group_members").select("*").eq("group_id", str(group_id)).execute()
    return [GroupMemberOut.model_validate(m) for m in res.data]


async def rename_group(db: AsyncClient, group_id: UUID, body: GroupUpdate) -> GroupOut:
    res = await db.table("groups").update({"name": body.name}).eq("id", str(group_id)).execute()
    if not res.data:
        raise NotFoundError("Group not found")
    return GroupOut.model_validate(res.data[0])


async def delete_group(db: AsyncClient, group_id: UUID) -> None:
    res = await db.table("groups").delete().eq("id", str(group_id)).execute()
    if not res.data:
        raise NotFoundError("Group not found")


async def remove_member(db: AsyncClient, group_id: UUID, user_id: UUID) -> None:
    res = (
        await db.table("group_members")
        .delete()
        .eq("group_id", str(group_id))
        .eq("user_id", str(user_id))
        .execute()
    )
    if not res.data:
        raise NotFoundError("Membership not found")
