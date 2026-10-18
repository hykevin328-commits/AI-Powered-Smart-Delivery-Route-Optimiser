"""
Vehicle model – tracks the fleet available for delivery assignments.
"""
from __future__ import annotations

import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Enum, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.delivery_assignment import DeliveryAssignment


class VehicleType(str, enum.Enum):
    BIKE = "bike"
    SCOOTER = "scooter"
    CAR = "car"
    VAN = "van"
    TRUCK = "truck"


class VehicleStatus(str, enum.Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class Vehicle(BaseModel):
    __tablename__ = "vehicles"

    # ── Identity ──────────────────────────────────────────────────────────────
    registration_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    make: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # ── Type & Status ─────────────────────────────────────────────────────────
    vehicle_type: Mapped[VehicleType] = mapped_column(
        Enum(VehicleType, name="vehicle_type"), nullable=False, default=VehicleType.VAN
    )
    status: Mapped[VehicleStatus] = mapped_column(
        Enum(VehicleStatus, name="vehicle_status"), nullable=False, default=VehicleStatus.AVAILABLE
    )

    # ── Capacity & Efficiency ─────────────────────────────────────────────────
    max_capacity_kg: Mapped[float] = mapped_column(Float, default=500.0, nullable=False)
    fuel_efficiency_l_per_100km: Mapped[float] = mapped_column(Float, default=8.5, nullable=False)
    is_electric: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Odometer ──────────────────────────────────────────────────────────────
    odometer_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    assignments: Mapped[List["DeliveryAssignment"]] = relationship(
        "DeliveryAssignment", back_populates="vehicle", lazy="select"
    )

    __table_args__ = (
        Index("ix_vehicles_status", "status"),
        Index("ix_vehicles_type_status", "vehicle_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<Vehicle id={self.id} reg={self.registration_number} type={self.vehicle_type}>"
