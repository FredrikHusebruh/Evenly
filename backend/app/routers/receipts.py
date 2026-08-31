from datetime import date
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from supabase import AsyncClient

from app.dependencies import CurrentUser, get_current_user, get_request_supabase_client
from app.schemas.receipt import ReceiptCreate, ReceiptDetail, ReceiptOut, ReceiptStatusOut, ReceiptUpdate
from app.services import receipts as receipts_service

router = APIRouter(prefix="/api/v1", tags=["receipts"])


@router.post(
    "/groups/{group_id}/receipts",
    response_model=ReceiptOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a receipt from an already-uploaded image",
)
async def create_receipt(
    group_id: UUID,
    body: ReceiptCreate,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> ReceiptOut:
    return await receipts_service.create_receipt(db, background_tasks, group_id, user.id, body)


@router.get("/groups/{group_id}/receipts", response_model=list[ReceiptOut], summary="Browse/filter a group's receipts")
async def list_receipts(
    group_id: UUID,
    date_from: date | None = None,
    date_to: date | None = None,
    store: str | None = None,
    category_id: UUID | None = None,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> list[ReceiptOut]:
    return await receipts_service.list_receipts(db, group_id, date_from, date_to, store, category_id)


@router.get("/receipts/{receipt_id}", response_model=ReceiptDetail, summary="Get a receipt with line items and mismatch flag")
async def get_receipt(
    receipt_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> ReceiptDetail:
    return await receipts_service.get_receipt_detail(db, receipt_id)


@router.get("/receipts/{receipt_id}/status", response_model=ReceiptStatusOut, summary="Poll OCR processing status")
async def get_receipt_status(
    receipt_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> ReceiptStatusOut:
    return await receipts_service.get_receipt_status(db, receipt_id)


@router.patch("/receipts/{receipt_id}", response_model=ReceiptOut, summary="Correct receipt fields")
async def update_receipt(
    receipt_id: UUID,
    body: ReceiptUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> ReceiptOut:
    return await receipts_service.update_receipt(db, receipt_id, body)


@router.delete("/receipts/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a receipt and its image")
async def delete_receipt(
    receipt_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> None:
    await receipts_service.delete_receipt(db, receipt_id)


@router.post(
    "/receipts/{receipt_id}/retry-ocr",
    response_model=ReceiptStatusOut,
    summary="Re-queue OCR processing for a receipt that previously failed",
)
async def retry_ocr(
    receipt_id: UUID,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> ReceiptStatusOut:
    return await receipts_service.retry_ocr(db, background_tasks, receipt_id)
