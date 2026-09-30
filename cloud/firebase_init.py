"""One-time Firebase Admin SDK initialisation (used only when Firebase backends are enabled)."""
from typing import Optional

from cloud.errors import CloudServiceError


def init_firebase(credentials_path: Optional[str], storage_bucket: Optional[str]):
    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError as exc:  # pragma: no cover
        raise CloudServiceError("firebase-admin is not installed. Run: pip install -r requirements-cloud.txt") from exc
    if not firebase_admin._apps:
        cred = credentials.Certificate(credentials_path) if credentials_path else credentials.ApplicationDefault()
        options = {"storageBucket": storage_bucket} if storage_bucket else {}
        firebase_admin.initialize_app(cred, options)
    return firebase_admin.get_app()
