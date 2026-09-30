"""
FastAPI application entrypoint.

Run locally:   uvicorn backend.app:app --reload --port 8000
Docs:          http://localhost:8000/docs
"""
import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.rate_limit import limit_auth_routes
from backend.routes import auth, files, plans, profile
from cloud.errors import CloudServiceError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("diet_planner.app")

settings = get_settings()

app = FastAPI(
    title="AI-Powered Personal Diet Planner API",
    version="1.0.0",
    description="Educational Cloud Computing project. Generated diet plans are general "
                "wellness examples, NOT medical advice.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(limit_auth_routes)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(plans.router)
app.include_router(files.router)


@app.exception_handler(CloudServiceError)
async def cloud_error_handler(request: Request, exc: CloudServiceError):
    logger.error("Cloud service error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        content={"detail": "A cloud service is temporarily unavailable. Please try again shortly."})


@app.get("/", tags=["meta"])
def root():
    return {"service": "ai-diet-planner-api", "status": "ok"}


@app.get("/health", tags=["meta"])
def health():
    """Simple liveness/readiness probe - also pings the database backend."""
    from backend.deps import get_db
    try:
        get_db().ping()
        db_ok = True
    except CloudServiceError:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": "up" if db_ok else "down"}
