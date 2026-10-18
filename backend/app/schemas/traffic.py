"""
Traffic integration schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.schemas.common import AppSchema, CoordinateSchema


class TrafficRequest(AppSchema):
    """Request current traffic between two points."""
    origin_latitude: float
    origin_longitude: float
    destination_latitude: float
    destination_longitude: float
    departure_time: Optional[datetime] = None   # None = now


class TrafficSegment(AppSchema):
    distance_km: float
    duration_minutes: float
    duration_in_traffic_minutes: float
    congestion_level: str           # low | medium | high | severe
    traffic_factor: float           # ratio: actual_time / free_flow_time


class TrafficResponse(AppSchema):
    origin: CoordinateSchema
    destination: CoordinateSchema
    segment: TrafficSegment
    provider: str
    cached: bool
    fetched_at: datetime


class TrafficAwareDistanceMatrix(AppSchema):
    """Distance matrix with traffic-adjusted durations."""
    locations: List[CoordinateSchema]
    distance_matrix_km: List[List[float]]
    duration_matrix_minutes: List[List[float]]    # free-flow
    traffic_duration_matrix_minutes: List[List[float]]  # with traffic
    overall_traffic_factor: float
