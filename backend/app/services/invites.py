import secrets
from datetime import UTC, datetime
from uuid import UUID

from supabase import AsyncClient

from app.clients.supabase import get_service_client, unwrap_maybe_single
from app.errors import ForbiddenError, NotFoundError
from app.schemas.group import GroupOut
from app.schemas.invite import InviteCreate, InviteOut, InvitePreview

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8
MAX_CODE_ATTEMPTS = 5


def _generate_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


async def _require_owner(user_id: UUID, group_id: UUID) -> None:
    service = await get_service_client()
    res = (
        await service.table("group_members")
        .select("role")
        .eq("group_id", str(group_id))
        .eq("user_id", str(user_id))
        .maybe_single()
        .execute()
    )
    membership = unwrap_maybe_single(res)
    if not membership or membership["role"] != "owner":
        raise ForbiddenError("Only the group owner can manage invites")


async def create_invite(user_id: UUID, group_id: UUID, body: InviteCreate) -> InviteOut:
    await _require_owner(user_id, group_id)
    service = await get_service_client()

    for _ in range(MAX_CODE_ATTEMPTS):
        code = _generate_code()
        existing = await service.table("group_invites").select("id").eq("code", code).maybe_single().execute()
        if unwrap_maybe_single(existing):
            continue
        res = (
            await service.table("group_invites")
            .insert(
                {
                    "group_id": str(group_id),
                    "code": code,
                    "created_by": str(user_id),
                    "expires_at": body.expires_at.isoformat() if body.expires_at else None,
                    "max_uses": body.max_uses,
                }
            )
            .execute()
        )
        return InviteOut.model_validate(res.data[0])

    raise RuntimeError("Failed to generate a unique invite code")


async def list_invites(db: AsyncClient, group_id: UUID) -> list[InviteOut]:
    res = (
        await db.table("group_invites")
        .select("*")
        .eq("group_id", str(group_id))
        .is_("revoked_at", "null")
        .order("created_at", desc=True)
        .execute()
    )
    return [InviteOut.model_validate(i) for i in res.data]


async def revoke_invite(user_id: UUID, group_id: UUID, invite_id: UUID) -> None:
    await _require_owner(user_id, group_id)
    service = await get_service_client()
    res = (
        await service.table("group_invites")
        .update({"revoked_at": datetime.now(UTC).isoformat()})
        .eq("id", str(invite_id))
        .eq("group_id", str(group_id))
        .execute()
    )
    if not res.data:
        raise NotFoundError("Invite not found")


def check_invite_validity(invite: dict, now: datetime) -> None:
    """Pure validity check, kept separate from the DB fetch so it's testable
    without a Supabase client double."""
    if invite["revoked_at"] is not None:
        raise NotFoundError("Invite has been revoked")
    if invite["expires_at"] and datetime.fromisoformat(invite["expires_at"]) < now:
        raise NotFoundError("Invite has expired")
    if invite["max_uses"] is not None and invite["use_count"] >= invite["max_uses"]:
        raise NotFoundError("Invite has reached its use limit")


async def _get_valid_invite(service: AsyncClient, code: str) -> dict:
    res = await service.table("group_invites").select("*").eq("code", code).maybe_single().execute()
    invite = unwrap_maybe_single(res)
    if not invite:
        raise NotFoundError("Invite not found")

    check_invite_validity(invite, datetime.now(UTC))
    return invite


async def preview_invite(code: str) -> InvitePreview:
    service = await get_service_client()
    invite = await _get_valid_invite(service, code)

    group_res = await service.table("groups").select("name").eq("id", invite["group_id"]).maybe_single().execute()
    group = unwrap_maybe_single(group_res)
    if not group:
        raise NotFoundError("Group not found")

    members_res = (
        await service.table("group_members")
        .select("user_id", count="exact")
        .eq("group_id", invite["group_id"])
        .execute()
    )

    return InvitePreview(
        group_id=invite["group_id"],
        group_name=group["name"],
        member_count=members_res.count or 0,
    )


async def redeem_invite(user_id: UUID, code: str) -> GroupOut:
    service = await get_service_client()
    invite = await _get_valid_invite(service, code)

    existing = (
        await service.table("group_members")
        .select("user_id")
        .eq("group_id", invite["group_id"])
        .eq("user_id", str(user_id))
        .maybe_single()
        .execute()
    )
    if not unwrap_maybe_single(existing):
        await service.table("group_members").insert(
            {"group_id": invite["group_id"], "user_id": str(user_id), "role": "member"}
        ).execute()
        await service.table("group_invites").update({"use_count": invite["use_count"] + 1}).eq(
            "id", invite["id"]
        ).execute()

    group_res = await service.table("groups").select("*").eq("id", invite["group_id"]).maybe_single().execute()
    group = unwrap_maybe_single(group_res)
    if not group:
        raise NotFoundError("Group not found")
    return GroupOut.model_validate(group)
