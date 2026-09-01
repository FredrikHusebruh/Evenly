from uuid import UUID

from supabase import AsyncClient

from app.clients.supabase import unwrap_maybe_single
from app.errors import NotFoundError, ValidationError
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

    if "status" in patch or "assigned_to" in patch:
        await _validate_personal_assignment(db, line_item_id, patch)

    res = await db.table("line_items").update(patch).eq("id", str(line_item_id)).execute()
    if not res.data:
        raise NotFoundError("Line item not found")
    return LineItemOut.model_validate(res.data[0])


async def _validate_personal_assignment(db: AsyncClient, line_item_id: UUID, patch: dict) -> None:
    """A "personal" item with no valid assignee silently drops out of every split total —
    its cost is never counted toward anyone's share. Reject that state at the boundary
    instead of persisting it.
    """
    current_res = (
        await db.table("line_items")
        .select("status, assigned_to, receipt_id")
        .eq("id", str(line_item_id))
        .maybe_single()
        .execute()
    )
    current = unwrap_maybe_single(current_res)
    if not current:
        raise NotFoundError("Line item not found")

    resulting_status = patch.get("status", current["status"])
    resulting_assigned_to = patch["assigned_to"] if "assigned_to" in patch else current["assigned_to"]

    if resulting_status != "personal":
        return

    if not resulting_assigned_to:
        raise ValidationError("A personal item must be assigned to a group member")

    receipt_res = (
        await db.table("receipts").select("group_id").eq("id", current["receipt_id"]).maybe_single().execute()
    )
    receipt = unwrap_maybe_single(receipt_res)
    if not receipt:
        raise NotFoundError("Receipt not found")

    membership_res = (
        await db.table("group_members")
        .select("user_id")
        .eq("group_id", receipt["group_id"])
        .eq("user_id", resulting_assigned_to)
        .maybe_single()
        .execute()
    )
    if not unwrap_maybe_single(membership_res):
        raise ValidationError("assigned_to must be a member of the receipt's group")


async def delete_line_item(db: AsyncClient, line_item_id: UUID) -> None:
    res = await db.table("line_items").delete().eq("id", str(line_item_id)).execute()
    if not res.data:
        raise NotFoundError("Line item not found")
