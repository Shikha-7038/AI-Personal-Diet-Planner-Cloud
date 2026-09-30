"""Central configuration read from environment variables. Never hardcode secrets here."""
import os
from dataclasses import dataclass

from ai_engine.ai_client import AISettings


def _bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class Settings:
    jwt_secret: str
    db_backend: str
    storage_backend: str
    sqlite_path: str
    local_storage_dir: str
    firebase_credentials: str
    firebase_storage_bucket: str
    cors_origins: list
    max_upload_bytes: int
    ai_settings: AISettings


def get_settings() -> Settings:
    secret = os.getenv("JWT_SECRET", "")
    if not secret:
        if _bool("ALLOW_INSECURE_DEV_SECRET", "true" if os.getenv("ENV", "dev") == "dev" else "false"):
            secret = "dev-only-insecure-secret-CHANGE-ME"
        else:
            raise RuntimeError("JWT_SECRET environment variable must be set")
    origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
    return Settings(
        jwt_secret=secret,
        db_backend=os.getenv("DB_BACKEND", "sqlite"),
        storage_backend=os.getenv("STORAGE_BACKEND", "local"),
        sqlite_path=os.getenv("SQLITE_PATH", "data/diet_planner.db"),
        local_storage_dir=os.getenv("LOCAL_STORAGE_DIR", "data/storage"),
        firebase_credentials=os.getenv("FIREBASE_CREDENTIALS_PATH", ""),
        firebase_storage_bucket=os.getenv("FIREBASE_STORAGE_BUCKET", ""),
        cors_origins=origins,
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(2 * 1024 * 1024))),
        ai_settings=AISettings(
            provider=os.getenv("AI_PROVIDER", "none"),
            api_key=os.getenv("AI_API_KEY", ""),
            model=os.getenv("AI_MODEL", ""),
            base_url=os.getenv("AI_BASE_URL", ""),
        ),
    )
