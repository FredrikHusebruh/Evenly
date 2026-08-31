from uuid import UUID

from supabase import AsyncClient

from app.errors import NotFoundError
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate


async def list_categories(db: AsyncClient, group_id: UUID) -> list[CategoryOut]:
    res = await db.table("categories").select("*").eq("group_id", str(group_id)).order("name").execute()
    return [CategoryOut.model_validate(c) for c in res.data]


async def create_category(db: AsyncClient, group_id: UUID, body: CategoryCreate) -> CategoryOut:
    res = await db.table("categories").insert({"group_id": str(group_id), "name": body.name}).execute()
    return CategoryOut.model_validate(res.data[0])


async def rename_category(db: AsyncClient, category_id: UUID, body: CategoryUpdate) -> CategoryOut:
    res = await db.table("categories").update({"name": body.name}).eq("id", str(category_id)).execute()
    if not res.data:
        raise NotFoundError("Category not found")
    return CategoryOut.model_validate(res.data[0])


async def delete_category(db: AsyncClient, category_id: UUID) -> None:
    res = await db.table("categories").delete().eq("id", str(category_id)).execute()
    if not res.data:
        raise NotFoundError("Category not found")
