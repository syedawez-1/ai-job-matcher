import uuid
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, EmailStr


# --- Auth ---
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# --- Resumes ---
class ResumeOut(BaseModel):
    id: uuid.UUID
    storage_path: str
    parsed_data: Optional[Any] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


# --- Jobs ---
class JobCreate(BaseModel):
    title: str
    company: Optional[str] = None
    description: Optional[str] = None
    required_skills: list[str] = []
    source_url: Optional[str] = None


class JobOut(BaseModel):
    id: uuid.UUID
    title: str
    company: Optional[str]
    description: Optional[str]
    required_skills: Optional[list[str]]
    source_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Applications ---
class ApplicationCreate(BaseModel):
    job_id: uuid.UUID
    status: str = "applied"
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class ApplicationOut(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    status: str
    applied_at: datetime
    notes: Optional[str]

    class Config:
        from_attributes = True
