"""
Authentication schemas – request bodies and token responses.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.models.user import UserRole
from app.schemas.common import AppSchema


# ── Register ──────────────────────────────────────────────────────────────────

class RegisterRequest(AppSchema):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = Field(None, max_length=20)
    role: UserRole = UserRole.DELIVERY_PARTNER

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginRequest(AppSchema):
    email: EmailStr
    password: str = Field(..., min_length=1)


# ── Token responses ───────────────────────────────────────────────────────────

class TokenResponse(AppSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(AppSchema):
    refresh_token: str


# ── Password management ───────────────────────────────────────────────────────

class ChangePasswordRequest(AppSchema):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ── User Profile ──────────────────────────────────────────────────────────────

class UserProfileResponse(AppSchema):
    id: UUID
    full_name: str
    email: str
    phone: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str]
    address: Optional[str]
    licence_number: Optional[str]
    last_login_at: Optional[str]
    created_at: str

    model_config = AppSchema.model_config


class UpdateProfileRequest(AppSchema):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    licence_number: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=500)
