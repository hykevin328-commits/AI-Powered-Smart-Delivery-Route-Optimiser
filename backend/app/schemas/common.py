"""
Shared schema primitives reused across multiple domain schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

T = TypeVar("T")


# ── Config shared across all schemas ─────────────────────────────────────────

class AppSchema(BaseModel):
    """Base schema with ORM mode enabled and strict alias handling."""
    model_config = ConfigDict(
        from_attributes=True,   # replaces orm_mode=True (Pydantic v2)
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# ── Generic paginated response envelope ──────────────────────────────────────

class PaginationMeta(AppSchema):
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedResponse(AppSchema, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: List[T]
    meta: PaginationMeta


# ── Standard API response envelope ───────────────────────────────────────────

class APIResponse(AppSchema, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None


# ── Coordinate pair ───────────────────────────────────────────────────────────

class CoordinateSchema(AppSchema):
    latitude: float
    longitude: float

    @field_validator("latitude")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_lon(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v


# ── Timestamp mixin ───────────────────────────────────────────────────────────

class TimestampSchema(AppSchema):
    created_at: datetime
    updated_at: datetime
