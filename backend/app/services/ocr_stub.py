"""Phase 2 stand-in for the real OCR pipeline (deferred to a later phase).

Immediately marks a freshly-created receipt as succeeded with zero line
items, so the reviewer adds items by hand through the same review/edit UI a
real OCR provider will later populate automatically — no UI code gets
thrown away when OCR is added.
"""

import logging

from app.clients.supabase import get_service_client

logger = logging.getLogger("app")


async def mark_succeeded_stub(receipt_id: str) -> None:
    try:
        service = await get_service_client()
        await service.table("receipts").update({"ocr_status": "succeeded"}).eq("id", receipt_id).execute()
    except Exception:
        # An uncaught exception in a background task vanishes silently and
        # would leave ocr_status stuck at 'pending' forever — log loudly and
        # best-effort mark the receipt failed instead.
        logger.exception("OCR stub failed for receipt %s", receipt_id)
        try:
            service = await get_service_client()
            await service.table("receipts").update(
                {"ocr_status": "failed", "ocr_error": "Processing failed. Please add items manually."}
            ).eq("id", receipt_id).execute()
        except Exception:
            logger.exception("Failed to mark receipt %s as failed after stub error", receipt_id)
