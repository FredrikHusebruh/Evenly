from uuid import UUID

from supabase import AsyncClient

from app.clients.supabase import unwrap_maybe_single
from app.errors import NotFoundError
from app.schemas.line_item import LineItemCreate, LineItemOut, LineItemUpdate


async def list_line_items(db: AsyncClient, receipt_id: UUID) -> list[LineItemOut]:
    res = await db.table("line_items").select("*").eq("receipt_id", str(receipt_id)).order("created_at").execute()
    return [LineItemOut.model_validate(i) for i in res.data]


async def create_line_item(db: AsyncClient, receipt_id: UUID, body: LineItemCreate) -> LineItemOut:
    res = (
        await db.table("line_items")
        .insert(
            {
                "receipt_id": str(receipt_id),
                "description": body.description,
                "quantity": str(body.quantity),
                "unit_price": str(body.unit_price),
                "total_price": str(body.total_price),
            }
        )
        .execute()
    )
    return LineItemOut.model_validate(res.data[0])


async def update_line_item(db: AsyncClient, line_item_id: UUID, body: LineItemUpdate) -> LineItemOut:
    patch = body.model_dump(exclude_unset=True, mode="json")
    if not patch:
        res = await db.table("line_items").select("*").eq("id", str(line_item_id)).maybe_single().execute()
        data = unwrap_maybe_single(res)
        if not data:
            raise NotFoundError("Line item not found")
        return LineItemOut.model_validate(data)

    res = await db.table("line_items").update(patch).eq("id", str(line_item_id)).execute()
    if not res.data:
        raise NotFoundError("Line item not found")
    return LineItemOut.model_validate(res.data[0])


async def delete_line_item(db: AsyncClient, line_item_id: UUID) -> None:
    res = await db.table("line_items").delete().eq("id", str(line_item_id)).execute()
    if not res.data:
        raise NotFoundError("Line item not found")
