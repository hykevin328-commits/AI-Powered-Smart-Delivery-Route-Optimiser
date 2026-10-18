"""
Delivery Order model – a single parcel/shipment to be delivered.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.delivery_assignment import DeliveryAssignment
    from app.models.delivery_status import DeliveryStatusLog


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrderPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class DeliveryOrder(BaseModel):
    __tablename__ = "delivery_orders"

    # ── Order Details ─────────────────────────────────────────────────────────
    order_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
    )
    priority: Mapped[OrderPriority] = mapped_column(
        Enum(OrderPriority, name="order_priority"),
        nullable=False,
        default=OrderPriority.NORMAL,
    )

    # ── Customer FK ───────────────────────────────────────────────────────────
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")

    # ── Delivery Location ─────────────────────────────────────────────────────
    delivery_address: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    delivery_postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    delivery_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delivery_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Pickup Location ───────────────────────────────────────────────────────
    pickup_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pickup_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pickup_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Package ───────────────────────────────────────────────────────────────
    package_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    special_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Scheduling ────────────────────────────────────────────────────────────
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_window_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_window_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── AI Predictions ────────────────────────────────────────────────────────
    predicted_delay_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    predicted_priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_delivery_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    assignments: Mapped[List["DeliveryAssignment"]] = relationship(
        "DeliveryAssignment", back_populates="order", lazy="select"
    )
    status_logs: Mapped[List["DeliveryStatusLog"]] = relationship(
        "DeliveryStatusLog", back_populates="order", lazy="select", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_orders_status_scheduled", "status", "scheduled_date"),
        Index("ix_orders_customer_status", "customer_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryOrder id={self.id} number={self.order_number} status={self.status}>"
