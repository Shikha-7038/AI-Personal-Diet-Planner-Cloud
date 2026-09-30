"""Pydantic request/response models for the REST API."""
from typing import Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    sex: Optional[str] = None
    age: Optional[float] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    activity_level: Optional[str] = None
    dietary_preference: Optional[str] = None
    goal: Optional[str] = None
    allergies: Optional[list] = None
    preferences: Optional[str] = None


class GeneratePlanRequest(BaseModel):
    save: bool = Field(default=True, description="Persist the generated plan to the database")
