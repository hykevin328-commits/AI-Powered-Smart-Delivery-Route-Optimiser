"""
Delivery Assignment schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from app.models.delivery_assignment import AssignmentStatus
from app.schemas.common import AppSchema, TimestampSchema
from app.schemas.delivery_order import DeliveryOrderSummary
from app.schemas.vehicle import VehicleSummary


class AssignmentResponse(TimestampSchema):
    id: UUID
    order_id: UUID
    delivery_partner_id: UUID
    vehicle_id: Optional[UUID]
    status: AssignmentStatus
    assigned_at: datetime
    completed_at: Optional[datetime]
    sequence_number: int
    actual_distance_km: Optional[float]
    actual_fuel_litres: Optional[float]
    actual_travel_time_minutes: Optional[int]
    notes: Optional[str]

    # Nested detail
    order: Optional[DeliveryOrderSummary] = None
    vehicle: Optional[VehicleSummary] = None


class AssignmentUpdate(AppSchema):
    vehicle_id: Optional[UUID] = None
    sequence_number: Optional[int] = None
    notes: Optional[str] = None


class CompleteAssignmentRequest(AppSchema):
    actual_distance_km: Optional[float] = None
    actual_fuel_litres: Optional[float] = None
    actual_travel_time_minutes: Optional[int] = None
    notes: Optional[str] = None
