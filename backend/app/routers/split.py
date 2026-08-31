from uuid import UUID

from fastapi import APIRouter, Depends
from supabase import AsyncClient

from app.dependencies import CurrentUser, get_current_user, get_request_supabase_client
from app.schemas.split import SettleUpOut, SplitResult
from app.services import split as split_service

router = APIRouter(prefix="/api/v1", tags=["split"])


@router.get("/receipts/{receipt_id}/split", response_model=SplitResult, summary="Live split summary for a receipt")
async def get_receipt_split(
    receipt_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> SplitResult:
    return await split_service.get_receipt_split(db, receipt_id)


@router.get(
    "/groups/{group_id}/settle-up",
    response_model=SettleUpOut,
    summary="Net who-owes-whom across the group's receipts",
)
async def get_settle_up(
    group_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> SettleUpOut:
    return await split_service.get_settle_up(db, group_id)
