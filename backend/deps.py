"""Shared FastAPI dependencies: settings, DB/storage singletons, current-user auth guard."""
from functools import lru_cache

from fastapi import Depends, Header, HTTPException, status

from backend.config import Settings, get_settings
from backend.utils.security import decode_access_token
from cloud.database_service import DatabaseService, build_database
from cloud.errors import CloudServiceError
from cloud.storage_service import StorageService, build_storage


@lru_cache
def get_settings_cached() -> Settings:
    return get_settings()


@lru_cache
def get_db() -> DatabaseService:
    s = get_settings_cached()
    return build_database(s.db_backend, s.sqlite_path, s.firebase_credentials, s.firebase_storage_bucket)


@lru_cache
def get_storage() -> StorageService:
    s = get_settings_cached()
    return build_storage(s.storage_backend, s.local_storage_dir, s.firebase_credentials, s.firebase_storage_bucket)


def get_current_user(
    authorization: str = Header(default=""),
    settings: Settings = Depends(get_settings_cached),
    db: DatabaseService = Depends(get_db),
) -> dict:
    """Reads 'Authorization: Bearer <token>', verifies the JWT, and loads the owning user."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    user_id = decode_access_token(token, settings.jwt_secret)
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    try:
        user = db.get_user_by_id(user_id)
    except CloudServiceError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database temporarily unavailable")
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    return user
