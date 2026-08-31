from uuid import UUID

from fastapi import APIRouter, Depends, status
from supabase import AsyncClient

from app.dependencies import CurrentUser, get_current_user, get_request_supabase_client
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services import categories as categories_service

router = APIRouter(prefix="/api/v1", tags=["categories"])


@router.get("/groups/{group_id}/categories", response_model=list[CategoryOut], summary="List a group's categories")
async def list_categories(
    group_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> list[CategoryOut]:
    return await categories_service.list_categories(db, group_id)


@router.post(
    "/groups/{group_id}/categories",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a category",
)
async def create_category(
    group_id: UUID,
    body: CategoryCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> CategoryOut:
    return await categories_service.create_category(db, group_id, body)


@router.patch("/categories/{category_id}", response_model=CategoryOut, summary="Rename a category")
async def rename_category(
    category_id: UUID,
    body: CategoryUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> CategoryOut:
    return await categories_service.rename_category(db, category_id, body)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a category")
async def delete_category(
    category_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncClient = Depends(get_request_supabase_client),
) -> None:
    await categories_service.delete_category(db, category_id)
