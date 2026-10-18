"""
Route History model – stores a completed optimised route for analytics
and AI model training.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.delivery_assignment import DeliveryAssignment


class RouteHistory(BaseModel):
    __tablename__ = "route_histories"

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    delivery_partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False, index=True
    )
    assignment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("delivery_assignments.id", ondelete="SET NULL"),
        nullable=True, unique=True
    )

    # ── Route Summary ─────────────────────────────────────────────────────────
    route_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_stops: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_distance_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_travel_time_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Fuel & Emissions ──────────────────────────────────────────────────────
    fuel_consumed_litres: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fuel_saved_litres: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    co2_emitted_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    co2_saved_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # ── Optimisation Metadata ─────────────────────────────────────────────────
    algorithm_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # "TSP" | "VRP"
    optimisation_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    route_efficiency_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Ordered waypoints stored as JSONB array ────────────────────────────────
    # [{"order_id": "...", "lat": 12.34, "lon": 56.78, "sequence": 1}]
    waypoints: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ── Polyline / map coordinates ────────────────────────────────────────────
    # GeoJSON LineString or encoded polyline string
    route_polyline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Traffic & Weather at the time ─────────────────────────────────────────
    traffic_factor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weather_condition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Delivery Outcome ──────────────────────────────────────────────────────
    deliveries_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deliveries_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    delivery_partner: Mapped["User"] = relationship("User", back_populates="route_histories")
    assignment: Mapped[Optional["DeliveryAssignment"]] = relationship(
        "DeliveryAssignment", back_populates="route_history"
    )

    __table_args__ = (
        Index("ix_route_histories_partner_date", "delivery_partner_id", "route_date"),
        Index("ix_route_histories_date", "route_date"),
    )

    def __repr__(self) -> str:
        return f"<RouteHistory id={self.id} date={self.route_date} partner={self.delivery_partner_id}>"
