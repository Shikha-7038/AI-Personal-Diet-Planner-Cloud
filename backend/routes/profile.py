"""GET /profile, PUT /profile."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from backend.deps import get_current_user, get_db
from backend.models.schemas import ProfileUpdateRequest
from backend.utils.validators import ValidationError, validate_profile_fields
from cloud.database_service import DatabaseService
from cloud.errors import CloudServiceError

router = APIRouter(tags=["profile"])
logger = logging.getLogger("diet_planner.profile")


def _public(user: dict) -> dict:
    return {k: v for k, v in user.items() if k not in ("password_hash",)}


@router.get("/profile")
def get_profile(user: dict = Depends(get_current_user)):
    return _public(user)


@router.put("/profile")
def update_profile(body: ProfileUpdateRequest, user: dict = Depends(get_current_user),
                   db: DatabaseService = Depends(get_db)):
    try:
        fields = validate_profile_fields(body.model_dump(exclude_unset=True))
    except ValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, exc.message)
    try:
        updated = db.update_user(user["user_id"], fields)
    except CloudServiceError:
        logger.exception("Database error updating profile")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database temporarily unavailable")
    return _public(updated)
