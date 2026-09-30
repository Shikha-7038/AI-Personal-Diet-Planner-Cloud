"""POST /upload, GET /files, DELETE /files/{id}."""
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from backend.deps import get_current_user, get_db, get_settings_cached, get_storage
from cloud.database_service import DatabaseService
from cloud.errors import CloudServiceError
from cloud.storage_service import StorageService, safe_filename

router = APIRouter(tags=["files"])
logger = logging.getLogger("diet_planner.files")

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp", "application/pdf",
                         "application/json", "text/plain"}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...), user: dict = Depends(get_current_user),
                      db: DatabaseService = Depends(get_db), storage: StorageService = Depends(get_storage),
                      settings=Depends(get_settings_cached)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Unsupported file type '{file.content_type}'. Allowed: images, PDF, JSON, text.")
    data = await file.read()
    if len(data) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Uploaded file is empty")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"File too large - max {settings.max_upload_bytes // (1024*1024)} MB")
    try:
        storage_path = storage.save(user["user_id"], safe_filename(file.filename), data, file.content_type)
        record = db.create_file(user["user_id"], safe_filename(file.filename), storage_path,
                                file.content_type, len(data), kind="upload")
    except CloudServiceError:
        logger.exception("Cloud error during upload")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Storage temporarily unavailable")
    return record


@router.get("/files")
def list_files(user: dict = Depends(get_current_user), db: DatabaseService = Depends(get_db)):
    try:
        return db.list_files(user["user_id"])
    except CloudServiceError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database temporarily unavailable")


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(file_id: str, user: dict = Depends(get_current_user), db: DatabaseService = Depends(get_db),
                storage: StorageService = Depends(get_storage)):
    try:
        record = db.get_file(user["user_id"], file_id)
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found")
        storage.delete(record["storage_path"])
        db.delete_file(user["user_id"], file_id)
    except CloudServiceError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Storage temporarily unavailable")
