import logging
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import BackgroundTasks
from supabase import AsyncClient

from app.clients.supabase import unwrap_maybe_single
from app.errors import ForbiddenError, NotFoundError
from app.schemas.line_item import LineItemOut
from app.schemas.receipt import ReceiptCreate, ReceiptDetail, ReceiptOut, ReceiptStatusOut, ReceiptUpdate
from app.services.ocr import pipeline as ocr_pipeline
from app.services.split import compute_mismatch

logger = logging.getLogger("app")


def image_path_belongs_to_group(image_path: str, group_id: UUID) -> bool:
    """True iff image_path's leading storage-path segment is this group's id.

    Storage RLS restricts reads/writes under <group_id>/... to that group's
    members, but the OCR pipeline downloads image_path with the service-role
    client, which bypasses that RLS entirely — so a client-supplied
    image_path pointing at a path belonging to a *different* group (one the
    caller has no current access to) must be rejected here explicitly,
    before it's ever trusted by that privileged download.
    """
    return image_path.split("/", 1)[0] == str(group_id)


async def create_receipt(
    db: AsyncClient,
    background_tasks: BackgroundTasks,
    group_id: UUID,
    uploaded_by: UUID,
    body: ReceiptCreate,
) -> ReceiptOut:
    if not image_path_belongs_to_group(body.image_path, group_id):
        raise ForbiddenError("Image path must belong to this group")

    res = (
        await db.table("receipts")
        .insert({"group_id": str(group_id), "uploaded_by": str(uploaded_by), "image_path": body.image_path})
        .execute()
    )
    receipt = res.data[0]
    background_tasks.add_task(ocr_pipeline.process_receipt_ocr, receipt["id"])
    return ReceiptOut.model_validate(receipt)


async def list_receipts(
    db: AsyncClient,
    group_id: UUID,
    date_from: date | None,
    date_to: date | None,
    store: str | None,
    category_id: UUID | None,
) -> list[ReceiptOut]:
    query = db.table("receipts").select("*").eq("group_id", str(group_id))
    if date_from is not None:
        query = query.gte("receipt_date", date_from.isoformat())
    if date_to is not None:
        query = query.lte("receipt_date", date_to.isoformat())
    if store is not None:
        query = query.ilike("merchant", f"%{store}%")
    if category_id is not None:
        query = query.eq("category_id", str(category_id))
    res = await query.order("receipt_date", desc=True).execute()
    return [ReceiptOut.model_validate(r) for r in res.data]


async def get_receipt_detail(db: AsyncClient, receipt_id: UUID) -> ReceiptDetail:
    receipt_res = await db.table("receipts").select("*").eq("id", str(receipt_id)).maybe_single().execute()
    receipt = unwrap_maybe_single(receipt_res)
    if not receipt:
        raise NotFoundError("Receipt not found")

    items_res = (
        await db.table("line_items").select("*").eq("receipt_id", str(receipt_id)).order("created_at").execute()
    )
    line_items = [LineItemOut.model_validate(i) for i in items_res.data]
    items_total = sum((li.total_price for li in line_items), Decimal(0))

    total_amount = receipt.get("total_amount")
    mismatch = compute_mismatch(items_total, Decimal(str(total_amount)) if total_amount is not None else None)

    return ReceiptDetail(**receipt, line_items=line_items, items_total=items_total, mismatch=mismatch)


async def get_receipt_status(db: AsyncClient, receipt_id: UUID) -> ReceiptStatusOut:
    res = await db.table("receipts").select("ocr_status, ocr_error").eq("id", str(receipt_id)).maybe_single().execute()
    data = unwrap_maybe_single(res)
    if not data:
        raise NotFoundError("Receipt not found")
    return ReceiptStatusOut.model_validate(data)


async def update_receipt(db: AsyncClient, receipt_id: UUID, body: ReceiptUpdate) -> ReceiptOut:
    patch = body.model_dump(exclude_unset=True, mode="json")
    if not patch:
        res = await db.table("receipts").select("*").eq("id", str(receipt_id)).maybe_single().execute()
        data = unwrap_maybe_single(res)
        if not data:
            raise NotFoundError("Receipt not found")
        return ReceiptOut.model_validate(data)

    res = await db.table("receipts").update(patch).eq("id", str(receipt_id)).execute()
    if not res.data:
        raise NotFoundError("Receipt not found")
    return ReceiptOut.model_validate(res.data[0])


async def delete_receipt(db: AsyncClient, receipt_id: UUID) -> None:
    receipt_res = await db.table("receipts").select("image_path").eq("id", str(receipt_id)).maybe_single().execute()
    receipt = unwrap_maybe_single(receipt_res)
    if not receipt:
        raise NotFoundError("Receipt not found")
    image_path = receipt.get("image_path")

    res = await db.table("receipts").delete().eq("id", str(receipt_id)).execute()
    if not res.data:
        raise NotFoundError("Receipt not found")

    if image_path:
        try:
            await db.storage.from_("receipts").remove([image_path])
        except Exception:
            logger.exception("Failed to delete storage object %s for receipt %s", image_path, receipt_id)


async def retry_ocr(db: AsyncClient, background_tasks: BackgroundTasks, receipt_id: UUID) -> ReceiptStatusOut:
    """Re-queue OCR for a receipt stuck in 'failed'. The conditional update
    (only transitions rows currently 'failed') makes the state change
    atomic at the DB level, so a stray double-click can't race a second
    background task against one still in flight."""
    res = (
        await db.table("receipts")
        .update({"ocr_status": "pending", "ocr_error": None})
        .eq("id", str(receipt_id))
        .eq("ocr_status", "failed")
        .execute()
    )
    if not res.data:
        raise NotFoundError("Receipt not found or not currently failed")
    background_tasks.add_task(ocr_pipeline.process_receipt_ocr, res.data[0]["id"])
    return ReceiptStatusOut.model_validate(res.data[0])
