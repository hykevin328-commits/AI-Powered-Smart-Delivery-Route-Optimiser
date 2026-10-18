"""
WebSocket message schemas for live route update events.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.common import AppSchema


class WSEventType:
    ROUTE_UPDATE = "route_update"
    ORDER_STATUS_CHANGED = "order_status_changed"
    ORDER_ASSIGNED = "order_assigned"
    ORDER_CANCELLED = "order_cancelled"
    ROUTE_RECALCULATED = "route_recalculated"
    PARTNER_LOCATION = "partner_location"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


class WSMessage(AppSchema):
    """Envelope for all WebSocket messages."""
    event: str
    payload: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PartnerLocationUpdate(AppSchema):
    delivery_partner_id: UUID
    latitude: float
    longitude: float
    speed_kmh: Optional[float] = None
    heading: Optional[float] = None    # degrees 0-360
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RouteUpdatePayload(AppSchema):
    assignment_id: UUID
    delivery_partner_id: UUID
    updated_waypoints: List[Dict[str, Any]]
    total_distance_km: float
    estimated_completion_minutes: float
