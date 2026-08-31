from fastapi import APIRouter, Depends

from app.dependencies import CurrentUser, get_current_user
from app.schemas.me import MeOut

router = APIRouter(prefix="/api/v1/me", tags=["me"])


@router.get("", response_model=MeOut, summary="Get the caller's identity")
def get_me(user: CurrentUser = Depends(get_current_user)) -> MeOut:
    return MeOut(id=user.id, email=user.email)
