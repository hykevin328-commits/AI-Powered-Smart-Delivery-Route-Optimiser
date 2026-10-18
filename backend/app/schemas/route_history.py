"""
Route History schemas.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.schemas.common import AppSchema, TimestampSchema


class RouteHistoryResponse(TimestampSchema):
    id: UUID
    delivery_partner_id: UUID
    assignment_id: Optional[UUID]
    route_date: date
    total_stops: int
    total_distance_km: float
    total_travel_time_minutes: int
    fuel_consumed_litres: float
    fuel_saved_litres: float
    co2_emitted_kg: float
    co2_saved_kg: float
    algorithm_used: Optional[str]
    optimisation_time_ms: Optional[int]
    route_efficiency_pct: Optional[float]
    waypoints: Optional[Dict]
    route_polyline: Optional[str]
    traffic_factor: Optional[float]
    weather_condition: Optional[str]
    deliveries_completed: int
    deliveries_failed: int
