"""POST /generate-plan, GET /plans, GET /plans/{id}, DELETE /plans/{id}."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from backend.deps import get_current_user, get_db, get_settings_cached
from backend.models.schemas import GeneratePlanRequest
from backend.utils.validators import profile_is_complete
from cloud.database_service import DatabaseService
from cloud.errors import CloudServiceError
from ai_engine.planner import create_plan

router = APIRouter(tags=["plans"])
logger = logging.getLogger("diet_planner.plans")


@router.post("/generate-plan", status_code=status.HTTP_201_CREATED)
def generate_plan(body: GeneratePlanRequest, user: dict = Depends(get_current_user),
                  db: DatabaseService = Depends(get_db), settings=Depends(get_settings_cached)):
    if not profile_is_complete(user):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Complete your profile (age, height, weight, activity level, "
                            "dietary preference, goal) before generating a plan")
    plan = create_plan(user, settings.ai_settings)
    if not body.save:
        return plan
    try:
        return db.create_plan(user["user_id"], plan)
    except CloudServiceError:
        logger.exception("Database error saving plan")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Could not save plan - database temporarily unavailable")


@router.get("/plans")
def list_plans(user: dict = Depends(get_current_user), db: DatabaseService = Depends(get_db)):
    try:
        return db.list_plans(user["user_id"])
    except CloudServiceError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database temporarily unavailable")


@router.get("/plans/{plan_id}")
def get_plan(plan_id: str, user: dict = Depends(get_current_user), db: DatabaseService = Depends(get_db)):
    try:
        plan = db.get_plan(user["user_id"], plan_id)
    except CloudServiceError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database temporarily unavailable")
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")
    return plan


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan_id: str, user: dict = Depends(get_current_user), db: DatabaseService = Depends(get_db)):
    try:
        deleted = db.delete_plan(user["user_id"], plan_id)
    except CloudServiceError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database temporarily unavailable")
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")
