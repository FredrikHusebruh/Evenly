from uuid import UUID

from fastapi import APIRouter, Depends
from supabase import AsyncClient

from app.dependencies import CurrentUser, get_current_user, get_request_supabase_client
from app.schemas.analytics import GroupAnalyticsOut
from app.services import analytics as analytics_service

router = APIRouter(prefix="/api/v1", tags=["analytics"])


@router.get(
    "/groups/{group_id}/analytics",
    response_model=GroupAnalyticsOut,
    summary="Spending breakdown, trends, and owed history for a group",
)
async def get_group_analytics(
    group_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> GroupAnalyticsOut:
    return await analytics_service.get_group_analytics(db, group_id, user.id)
