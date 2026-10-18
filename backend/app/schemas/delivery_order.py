"""
Delivery Order schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, model_validator

from app.models.delivery_order import OrderPriority, OrderStatus
from app.schemas.common import AppSchema, TimestampSchema
from app.schemas.customer import CustomerSummary


# ── Create ────────────────────────────────────────────────────────────────────

class DeliveryOrderCreate(AppSchema):
    customer_id: UUID
    delivery_address: str = Field(..., min_length=5)
    delivery_city: Optional[str] = Field(None, max_length=100)
    delivery_postal_code: Optional[str] = Field(None, max_length=20)
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None

    pickup_address: Optional[str] = None
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None

    package_description: Optional[str] = Field(None, max_length=255)
    weight_kg: Optional[float] = Field(None, gt=0, le=10000)
    special_instructions: Optional[str] = None
    priority: OrderPriority = OrderPriority.NORMAL

    scheduled_date: Optional[datetime] = None
    delivery_window_start: Optional[datetime] = None
    delivery_window_end: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_delivery_window(self) -> "DeliveryOrderCreate":
        if self.delivery_window_start and self.delivery_window_end:
            if self.delivery_window_end <= self.delivery_window_start:
                raise ValueError("delivery_window_end must be after delivery_window_start")
        return self


# ── Update ────────────────────────────────────────────────────────────────────

class DeliveryOrderUpdate(AppSchema):
    delivery_address: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_postal_code: Optional[str] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    pickup_address: Optional[str] = None
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    package_description: Optional[str] = Field(None, max_length=255)
    weight_kg: Optional[float] = Field(None, gt=0, le=10000)
    special_instructions: Optional[str] = None
    priority: Optional[OrderPriority] = None
    scheduled_date: Optional[datetime] = None
    delivery_window_start: Optional[datetime] = None
    delivery_window_end: Optional[datetime] = None


# ── Status Update ─────────────────────────────────────────────────────────────

class OrderStatusUpdate(AppSchema):
    status: OrderStatus
    notes: Optional[str] = None
    latitude: Optional[float] = None   # current location at status change
    longitude: Optional[float] = None


# ── Assign ────────────────────────────────────────────────────────────────────

class AssignOrderRequest(AppSchema):
    order_ids: list[UUID] = Field(..., min_length=1, max_length=200)
    delivery_partner_id: UUID
    vehicle_id: Optional[UUID] = None


# ── Responses ─────────────────────────────────────────────────────────────────

class DeliveryOrderResponse(TimestampSchema):
    id: UUID
    order_number: str
    status: OrderStatus
    priority: OrderPriority
    customer_id: UUID
    customer: Optional[CustomerSummary] = None

    delivery_address: str
    delivery_city: Optional[str]
    delivery_postal_code: Optional[str]
    delivery_latitude: Optional[float]
    delivery_longitude: Optional[float]

    pickup_address: Optional[str]
    pickup_latitude: Optional[float]
    pickup_longitude: Optional[float]

    package_description: Optional[str]
    weight_kg: Optional[float]
    special_instructions: Optional[str]

    scheduled_date: Optional[datetime]
    delivery_window_start: Optional[datetime]
    delivery_window_end: Optional[datetime]
    delivered_at: Optional[datetime]

    predicted_delay_minutes: Optional[float]
    predicted_priority_score: Optional[float]
    estimated_delivery_time_minutes: Optional[int]


class DeliveryOrderSummary(AppSchema):
    """Lightweight order reference used in assignment / route responses."""
    id: UUID
    order_number: str
    status: OrderStatus
    priority: OrderPriority
    delivery_address: str
    delivery_latitude: Optional[float]
    delivery_longitude: Optional[float]
    customer: Optional[CustomerSummary] = None
