"""
Route optimization request / response schemas.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import AppSchema, CoordinateSchema


# ── Input ─────────────────────────────────────────────────────────────────────

class DeliveryLocation(AppSchema):
    """A single stop to include in the optimization."""
    order_id: Optional[UUID] = None
    label: Optional[str] = None       # e.g. "Warehouse", "Customer A"
    latitude: float
    longitude: float
    service_time_minutes: int = Field(default=5, ge=0)    # time spent at stop
    time_window_start: Optional[int] = None  # minutes from midnight
    time_window_end: Optional[int] = None

    @field_validator("latitude")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_lon(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v


class VehicleConfig(AppSchema):
    """Per-vehicle capacity constraints for VRP."""
    vehicle_id: Optional[UUID] = None
    delivery_partner_id: Optional[UUID] = None
    max_capacity_kg: float = Field(default=500.0, gt=0)
    max_stops: Optional[int] = Field(None, ge=1)
    start_latitude: Optional[float] = None    # depot / starting point
    start_longitude: Optional[float] = None
    end_latitude: Optional[float] = None      # return-to-depot
    end_longitude: Optional[float] = None


class OptimizeRouteRequest(AppSchema):
    """
    Unified request body for both TSP (single vehicle) and VRP (multi-vehicle).
    If vehicles is empty or has 1 entry → TSP mode.
    If vehicles has 2+ entries → VRP mode.
    """
    depot_latitude: float
    depot_longitude: float
    locations: List[DeliveryLocation] = Field(..., min_length=1, max_length=500)
    vehicles: List[VehicleConfig] = Field(default_factory=list)

    consider_traffic: bool = True
    consider_time_windows: bool = False
    return_to_depot: bool = True
    time_limit_seconds: int = Field(default=30, ge=5, le=120)


# ── Output ────────────────────────────────────────────────────────────────────

class WaypointResult(AppSchema):
    sequence: int
    order_id: Optional[UUID]
    label: Optional[str]
    latitude: float
    longitude: float
    estimated_arrival_minutes: Optional[float]   # from depot start
    distance_from_prev_km: Optional[float]


class VehicleRouteResult(AppSchema):
    vehicle_index: int
    vehicle_id: Optional[UUID]
    delivery_partner_id: Optional[UUID]
    waypoints: List[WaypointResult]
    total_distance_km: float
    total_travel_time_minutes: float
    estimated_fuel_litres: float
    estimated_co2_kg: float
    stop_count: int


class OptimizeRouteResponse(AppSchema):
    algorithm: str                        # "TSP" | "VRP"
    solver_status: str                    # "OPTIMAL" | "FEASIBLE" | "INFEASIBLE"
    optimization_time_ms: int
    total_distance_km: float
    total_travel_time_minutes: float
    total_fuel_litres: float
    total_co2_kg: float
    fuel_saved_litres: Optional[float]    # vs. naive ordering
    co2_saved_kg: Optional[float]
    route_efficiency_pct: Optional[float]
    vehicle_routes: List[VehicleRouteResult]
    # GeoJSON-compatible coordinate array for map rendering
    route_coordinates: Optional[List[List[float]]] = None


# ── Live recalculation ────────────────────────────────────────────────────────

class RecalculateRouteRequest(AppSchema):
    assignment_id: UUID
    current_latitude: float
    current_longitude: float
    cancelled_order_ids: Optional[List[UUID]] = None
    added_order_ids: Optional[List[UUID]] = None
