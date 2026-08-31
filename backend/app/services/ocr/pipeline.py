import logging
import mimetypes

from supabase import AsyncClient

from app.clients.anthropic import get_anthropic_client
from app.clients.supabase import get_service_client, unwrap_maybe_single
from app.services.ocr.claude_provider import ClaudeVisionOcrProvider
from app.services.ocr.provider import OcrProvider, OcrProviderError, ParsedReceipt

logger = logging.getLogger("app")

_SAFE_ERROR_MESSAGE = "Couldn't read this receipt automatically. Please add items manually."
_SUPPORTED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def get_ocr_provider() -> OcrProvider | None:
    """The configured OcrProvider, or None if OCR isn't configured (no
    ANTHROPIC_API_KEY) — the pipeline treats None as an immediate,
    well-defined failure instead of a call that would error less clearly
    deep inside the SDK."""
    client = get_anthropic_client()
    return ClaudeVisionOcrProvider(client) if client is not None else None


def guess_image_mime_type(image_path: str) -> str:
    """Best-effort mime type from the storage path's extension, restricted
    to the four types Claude's vision API accepts. Falls back to
    image/jpeg — the common case for phone-camera photos — for anything
    outside that set (e.g. .heic) rather than sending a type Claude rejects."""
    guessed, _ = mimetypes.guess_type(image_path)
    return guessed if guessed in _SUPPORTED_MIME_TYPES else "image/jpeg"


def match_category_id(categories: list[dict], suggested_category: str | None) -> str | None:
    """Case-insensitive match of an OCR-suggested category name against a
    group's actual categories (seeded defaults, or since renamed/added) —
    pure function, no DB access, directly unit-testable."""
    if suggested_category is None:
        return None
    target = suggested_category.strip().lower()
    for cat in categories:
        if cat["name"].strip().lower() == target:
            return cat["id"]
    return None


def build_receipt_patch(receipt: dict, parsed: ParsedReceipt, category_id: str | None) -> dict:
    """Compute which receipt columns to write from OCR results — never
    overwrites a field the receipt already has a value for (e.g. a human
    correction from a prior partial run), so this is safe on a first run
    and on a retry-after-partial-failure alike."""
    patch: dict = {"ocr_status": "succeeded"}
    if receipt.get("merchant") is None and parsed.merchant is not None:
        patch["merchant"] = parsed.merchant
    if receipt.get("receipt_date") is None and parsed.receipt_date is not None:
        patch["receipt_date"] = parsed.receipt_date.isoformat()
    if receipt.get("total_amount") is None and parsed.total_amount is not None:
        patch["total_amount"] = str(parsed.total_amount)
    if receipt.get("category_id") is None and category_id is not None:
        patch["category_id"] = category_id
    return patch


async def run_ocr_pipeline(receipt_id: str, service: AsyncClient, provider: OcrProvider) -> None:
    """The actual OCR sequence — takes its dependencies as arguments so it's
    directly unit-testable against a fake AsyncClient/OcrProvider, with all
    business logic delegated to the pure helpers above. Raises on any
    failure; the caller (process_receipt_ocr) is responsible for catching
    and marking the receipt failed."""
    await service.table("receipts").update({"ocr_status": "processing"}).eq("id", receipt_id).execute()

    receipt_res = await service.table("receipts").select("*").eq("id", receipt_id).maybe_single().execute()
    receipt = unwrap_maybe_single(receipt_res)
    if not receipt:
        raise ValueError(f"Receipt {receipt_id} not found")
    image_path = receipt.get("image_path")
    if not image_path:
        raise ValueError(f"Receipt {receipt_id} has no image_path")

    image_bytes = await service.storage.from_("receipts").download(image_path)
    mime_type = guess_image_mime_type(image_path)

    parsed = await provider.extract_receipt(image_bytes, mime_type)

    category_id = None
    if receipt.get("category_id") is None and parsed.suggested_category is not None:
        categories_res = (
            await service.table("categories").select("id, name").eq("group_id", receipt["group_id"]).execute()
        )
        category_id = match_category_id(categories_res.data, parsed.suggested_category)

    if parsed.line_items:
        await service.table("line_items").insert(
            [
                {
                    "receipt_id": receipt_id,
                    "description": li.description,
                    "quantity": str(li.quantity),
                    "unit_price": str(li.unit_price),
                    "total_price": str(li.total_price),
                }
                for li in parsed.line_items
            ]
        ).execute()

    patch = build_receipt_patch(receipt, parsed, category_id)
    await service.table("receipts").update(patch).eq("id", receipt_id).execute()


async def process_receipt_ocr(receipt_id: str) -> None:
    """Background-task entry point for OCR processing. Wrapped top-to-bottom
    in try/except: an uncaught exception in a FastAPI BackgroundTasks task
    vanishes silently and would leave ocr_status stuck forever otherwise."""
    try:
        service = await get_service_client()
        provider = get_ocr_provider()
        if provider is None:
            raise OcrProviderError("OCR is not configured (ANTHROPIC_API_KEY unset)")
        await run_ocr_pipeline(receipt_id, service, provider)
    except Exception:
        logger.exception("OCR pipeline failed for receipt %s", receipt_id)
        try:
            service = await get_service_client()
            await service.table("receipts").update(
                {"ocr_status": "failed", "ocr_error": _SAFE_ERROR_MESSAGE}
            ).eq("id", receipt_id).execute()
        except Exception:
            logger.exception("Failed to mark receipt %s as failed after pipeline error", receipt_id)
