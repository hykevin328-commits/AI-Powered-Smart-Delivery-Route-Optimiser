"""
Vehicle schemas.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import Field

from app.models.vehicle import VehicleStatus, VehicleType
from app.schemas.common import AppSchema, TimestampSchema


class VehicleCreate(AppSchema):
    registration_number: str = Field(..., min_length=2, max_length=30)
    make: Optional[str] = Field(None, max_length=60)
    model: Optional[str] = Field(None, max_length=60)
    year: Optional[int] = Field(None, ge=1990, le=2100)
    color: Optional[str] = Field(None, max_length=30)
    vehicle_type: VehicleType = VehicleType.VAN
    max_capacity_kg: float = Field(default=500.0, gt=0)
    fuel_efficiency_l_per_100km: float = Field(default=8.5, gt=0)
    is_electric: bool = False


class VehicleUpdate(AppSchema):
    make: Optional[str] = Field(None, max_length=60)
    model: Optional[str] = Field(None, max_length=60)
    year: Optional[int] = Field(None, ge=1990, le=2100)
    color: Optional[str] = Field(None, max_length=30)
    vehicle_type: Optional[VehicleType] = None
    status: Optional[VehicleStatus] = None
    max_capacity_kg: Optional[float] = Field(None, gt=0)
    fuel_efficiency_l_per_100km: Optional[float] = Field(None, gt=0)
    is_electric: Optional[bool] = None
    odometer_km: Optional[float] = Field(None, ge=0)


class VehicleResponse(TimestampSchema):
    id: UUID
    registration_number: str
    make: Optional[str]
    model: Optional[str]
    year: Optional[int]
    color: Optional[str]
    vehicle_type: VehicleType
    status: VehicleStatus
    max_capacity_kg: float
    fuel_efficiency_l_per_100km: float
    is_electric: bool
    odometer_km: float


class VehicleSummary(AppSchema):
    id: UUID
    registration_number: str
    vehicle_type: VehicleType
    status: VehicleStatus
