"""
Customer schemas.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.common import AppSchema, TimestampSchema


# ── Create / Update ───────────────────────────────────────────────────────────

class CustomerCreate(AppSchema):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: Optional[EmailStr] = None
    phone: str = Field(..., min_length=7, max_length=20)
    address: str = Field(..., min_length=5)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="India", max_length=80)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


class CustomerUpdate(AppSchema):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=7, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=80)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


# ── Responses ─────────────────────────────────────────────────────────────────

class CustomerResponse(TimestampSchema):
    id: UUID
    full_name: str
    email: Optional[str]
    phone: str
    address: str
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: str
    latitude: Optional[float]
    longitude: Optional[float]
    is_active: bool
    notes: Optional[str]


class CustomerSummary(AppSchema):
    """Lightweight customer reference embedded in order responses."""
    id: UUID
    full_name: str
    phone: str
    email: Optional[str]
