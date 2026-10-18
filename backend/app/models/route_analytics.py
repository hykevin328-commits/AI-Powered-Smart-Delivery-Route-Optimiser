"""
Route Analytics model – daily pre-aggregated metrics per delivery partner.
Populated by a background job after each route completion.
Enables fast daily / weekly / monthly dashboard queries.
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class RouteAnalytics(BaseModel):
    __tablename__ = "route_analytics"

    # ── Dimensions ────────────────────────────────────────────────────────────
    analytics_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    delivery_partner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    # "daily" | "weekly" | "monthly"
    period_type: Mapped[str] = mapped_column(String(10), nullable=False, default="daily")

    # ── Distance ──────────────────────────────────────────────────────────────
    total_distance_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_distance_per_delivery_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Fuel ──────────────────────────────────────────────────────────────────
    fuel_consumed_litres: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fuel_saved_litres: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # ── Carbon Emissions ──────────────────────────────────────────────────────
    co2_emitted_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    co2_saved_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # ── Delivery Performance ──────────────────────────────────────────────────
    total_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    on_time_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_rate_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Time ──────────────────────────────────────────────────────────────────
    avg_delivery_time_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_travel_time_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Route Efficiency ──────────────────────────────────────────────────────
    route_efficiency_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    routes_optimised: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "analytics_date", "delivery_partner_id", "period_type",
            name="uq_analytics_date_partner_period"
        ),
        Index("ix_analytics_date_period", "analytics_date", "period_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<RouteAnalytics date={self.analytics_date} "
            f"partner={self.delivery_partner_id} period={self.period_type}>"
        )
