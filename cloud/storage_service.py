"""
Cloud object storage layer (files, images, exported plans).

  * LocalStorage     - saves files in a local folder (simulates a bucket)
  * FirebaseStorage  - Firebase Storage / Google Cloud Storage bucket (free Spark tier)
Switch with STORAGE_BACKEND. Objects are stored under  users/<user_id>/<random>_<name>
so each user's files live in their own "folder" (prefix).
"""
import os
import re
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from cloud.errors import CloudServiceError


def safe_filename(name: str) -> str:
    """Keep only a safe basename (blocks path traversal like ../../etc/passwd)."""
    name = os.path.basename(name or "file").strip().replace(" ", "_")
    name = re.sub(r"[^A-Za-z0-9._-]", "", name)
    return name[:80] or "file"


class StorageService(ABC):
    @abstractmethod
    def save(self, user_id: str, filename: str, data: bytes, content_type: str) -> str:
        """Store bytes and return the storage_path."""
    @abstractmethod
    def read(self, storage_path: str) -> bytes: ...
    @abstractmethod
    def delete(self, storage_path: str) -> None: ...

    @staticmethod
    def make_path(user_id: str, filename: str) -> str:
        return f"users/{user_id}/{uuid.uuid4().hex[:12]}_{safe_filename(filename)}"


class LocalStorage(StorageService):
    def __init__(self, base_dir: str):
        self.base = Path(base_dir).resolve()
        self.base.mkdir(parents=True, exist_ok=True)

    def _resolve(self, storage_path: str) -> Path:
        target = (self.base / storage_path).resolve()
        if self.base not in target.parents:
            raise CloudServiceError("Invalid storage path")
        return target

    def save(self, user_id, filename, data, content_type):
        path = self.make_path(user_id, filename)
        try:
            target = self._resolve(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        except OSError as exc:
            raise CloudServiceError("Could not write file to storage") from exc
        return path

    def read(self, storage_path):
        try:
            return self._resolve(storage_path).read_bytes()
        except OSError as exc:
            raise CloudServiceError("Could not read file from storage") from exc

    def delete(self, storage_path):
        try:
            self._resolve(storage_path).unlink(missing_ok=True)
        except OSError as exc:
            raise CloudServiceError("Could not delete file from storage") from exc


class FirebaseStorage(StorageService):
    def __init__(self, credentials_path=None, storage_bucket=None):
        from cloud.firebase_init import init_firebase
        init_firebase(credentials_path, storage_bucket)
        try:
            from firebase_admin import storage
            self.bucket = storage.bucket()
        except Exception as exc:  # pragma: no cover
            raise CloudServiceError("Could not connect to Firebase Storage") from exc

    def save(self, user_id, filename, data, content_type):
        path = self.make_path(user_id, filename)
        try:
            self.bucket.blob(path).upload_from_string(data, content_type=content_type)
        except Exception as exc:
            raise CloudServiceError("Could not upload file to cloud storage") from exc
        return path

    def read(self, storage_path):
        try:
            return self.bucket.blob(storage_path).download_as_bytes()
        except Exception as exc:
            raise CloudServiceError("Could not download file from cloud storage") from exc

    def delete(self, storage_path):
        try:
            self.bucket.blob(storage_path).delete()
        except Exception as exc:
            raise CloudServiceError("Could not delete file from cloud storage") from exc


def build_storage(backend, local_dir="data/storage", credentials_path=None, storage_bucket=None):
    if backend == "supabase":
        from cloud.supabase_service import SupabaseStorage
        return SupabaseStorage()
    if backend == "firebase":
        return FirebaseStorage(credentials_path, storage_bucket)
    return LocalStorage(local_dir)
