"""
Traffic Cache model – short-lived storage of traffic segment data
fetched from Google Maps Routes API or OpenRouteService.
Rows are soft-expired by checking expires_at; a background job can hard-delete.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TrafficCache(BaseModel):
    __tablename__ = "traffic_cache"

    # ── Cache Key ─────────────────────────────────────────────────────────────
    # Composite key: "lat1,lon1->lat2,lon2" or a road segment ID
    cache_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # ── Source ────────────────────────────────────────────────────────────────
    provider: Mapped[str] = mapped_column(String(50), default="google", nullable=False)

    # ── Coordinates ───────────────────────────────────────────────────────────
    origin_lat: Mapped[float] = mapped_column(Float, nullable=False)
    origin_lon: Mapped[float] = mapped_column(Float, nullable=False)
    dest_lat: Mapped[float] = mapped_column(Float, nullable=False)
    dest_lon: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Traffic Data ──────────────────────────────────────────────────────────
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    duration_minutes: Mapped[float] = mapped_column(Float, nullable=False)
    duration_in_traffic_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    congestion_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # low|medium|high
    traffic_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # ── Raw response snapshot ─────────────────────────────────────────────────
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ── TTL ───────────────────────────────────────────────────────────────────
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index("ix_traffic_cache_coords", "origin_lat", "origin_lon", "dest_lat", "dest_lon"),
    )

    def __repr__(self) -> str:
        return f"<TrafficCache key={self.cache_key} factor={self.traffic_factor}>"
