"""
Delivery Assignment model – links an Order to a Delivery Partner and Vehicle.
One order can have at most one active assignment at a time.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.delivery_order import DeliveryOrder
    from app.models.user import User
    from app.models.vehicle import Vehicle
    from app.models.route_history import RouteHistory


class AssignmentStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REASSIGNED = "reassigned"


class DeliveryAssignment(BaseModel):
    __tablename__ = "delivery_assignments"

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("delivery_orders.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    delivery_partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False, index=True
    )
    vehicle_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True
    )

    # ── Status & Timing ───────────────────────────────────────────────────────
    status: Mapped[AssignmentStatus] = mapped_column(
        Enum(AssignmentStatus, name="assignment_status"),
        nullable=False,
        default=AssignmentStatus.ACTIVE,
        index=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Route Sequence ────────────────────────────────────────────────────────
    sequence_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # ── Distance & Fuel Actuals ────────────────────────────────────────────────
    actual_distance_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_fuel_litres: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_travel_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ── Notes ─────────────────────────────────────────────────────────────────
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    order: Mapped["DeliveryOrder"] = relationship("DeliveryOrder", back_populates="assignments")
    delivery_partner: Mapped["User"] = relationship("User", back_populates="assignments")
    vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle", back_populates="assignments")
    route_history: Mapped[Optional["RouteHistory"]] = relationship(
        "RouteHistory", back_populates="assignment", uselist=False, lazy="select"
    )

    __table_args__ = (
        Index("ix_assignments_partner_status", "delivery_partner_id", "status"),
        Index("ix_assignments_order_active", "order_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<DeliveryAssignment id={self.id} "
            f"order={self.order_id} partner={self.delivery_partner_id} "
            f"status={self.status}>"
        )
