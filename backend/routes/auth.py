"""POST /register, POST /login."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from backend.config import Settings
from backend.deps import get_db, get_settings_cached
from backend.models.schemas import LoginRequest, RegisterRequest, TokenResponse
from backend.utils.security import create_access_token, hash_password, verify_password
from backend.utils.validators import ValidationError, require_email, require_name, require_password
from cloud.database_service import DatabaseService
from cloud.errors import CloudServiceError, DuplicateEmailError

router = APIRouter(tags=["auth"])
logger = logging.getLogger("diet_planner.auth")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: DatabaseService = Depends(get_db),
            settings: Settings = Depends(get_settings_cached)):
    try:
        name = require_name(body.name)
        email = require_email(body.email)
        password = require_password(body.password)
    except ValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, exc.message)

    try:
        user = db.create_user(name, email, hash_password(password))
    except DuplicateEmailError:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    except CloudServiceError:
        logger.exception("Database error during registration")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database temporarily unavailable")

    token = create_access_token(user["user_id"], settings.jwt_secret)
    return TokenResponse(access_token=token, user_id=user["user_id"], name=user["name"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DatabaseService = Depends(get_db),
         settings: Settings = Depends(get_settings_cached)):
    try:
        email = require_email(body.email)
    except ValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, exc.message)

    try:
        user = db.get_user_by_email(email)
    except CloudServiceError:
        logger.exception("Database error during login")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database temporarily unavailable")

    # Same error for "no such user" and "wrong password" - don't leak which one it was.
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    token = create_access_token(user["user_id"], settings.jwt_secret)
    return TokenResponse(access_token=token, user_id=user["user_id"], name=user["name"])
