"""
Geocoding schemas.
"""
from __future__ import annotations

from typing import List, Optional

from app.schemas.common import AppSchema


class GeocodeRequest(AppSchema):
    address: str
    city: Optional[str] = None
    country: Optional[str] = "India"


class GeocodeResponse(AppSchema):
    address: str
    formatted_address: str
    latitude: float
    longitude: float
    confidence: float       # 0.0 – 1.0
    provider: str


class ReverseGeocodeRequest(AppSchema):
    latitude: float
    longitude: float


class ReverseGeocodeResponse(AppSchema):
    formatted_address: str
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]
    latitude: float
    longitude: float
