from uuid import UUID

from fastapi import APIRouter, Depends, status
from supabase import AsyncClient

from app.dependencies import CurrentUser, get_current_user, get_request_supabase_client
from app.schemas.line_item import LineItemCreate, LineItemOut, LineItemUpdate
from app.services import line_items as line_items_service

router = APIRouter(prefix="/api/v1", tags=["line-items"])


@router.get("/receipts/{receipt_id}/line-items", response_model=list[LineItemOut], summary="List a receipt's line items")
async def list_line_items(
    receipt_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> list[LineItemOut]:
    return await line_items_service.list_line_items(db, receipt_id)


@router.post(
    "/receipts/{receipt_id}/line-items",
    response_model=LineItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Manually add a line item",
)
async def create_line_item(
    receipt_id: UUID,
    body: LineItemCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> LineItemOut:
    return await line_items_service.create_line_item(db, receipt_id, body)


@router.patch(
    "/line-items/{line_item_id}",
    response_model=LineItemOut,
    summary="Correct fields and/or toggle shared/personal/excluded",
)
async def update_line_item(
    line_item_id: UUID,
    body: LineItemUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> LineItemOut:
    return await line_items_service.update_line_item(db, line_item_id, body)


@router.delete("/line-items/{line_item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove a line item entirely")
async def delete_line_item(
    line_item_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> None:
    await line_items_service.delete_line_item(db, line_item_id)
