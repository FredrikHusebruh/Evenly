from supabase import AsyncClient

from app.clients.supabase import unwrap_maybe_single
from app.dependencies import CurrentUser
from app.schemas.me import MeOut, MeUpdate


async def get_me(db: AsyncClient, user: CurrentUser) -> MeOut:
    res = await db.table("profiles").select("username").eq("id", str(user.id)).maybe_single().execute()
    data = unwrap_maybe_single(res)
    username = data.get("username") if data else None
    return MeOut(id=user.id, email=user.email, username=username)


async def update_me(db: AsyncClient, user: CurrentUser, body: MeUpdate) -> MeOut:
    patch = body.model_dump(exclude_unset=True)
    if patch:
        await db.table("profiles").update(patch).eq("id", str(user.id)).execute()
    return await get_me(db, user)
