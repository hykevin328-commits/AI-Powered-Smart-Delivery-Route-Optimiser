"""
General-purpose utility functions used across the application.
"""
from __future__ import annotations

import math
import re
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID


# ── Date / Time ───────────────────────────────────────────────────────────────

def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def start_of_day(d: Optional[date] = None) -> datetime:
    d = d or utcnow().date()
    return datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=timezone.utc)


def end_of_day(d: Optional[date] = None) -> datetime:
    d = d or utcnow().date()
    return datetime(d.year, d.month, d.day, 23, 59, 59, 999999, tzinfo=timezone.utc)


# ── Geospatial ────────────────────────────────────────────────────────────────

EARTH_RADIUS_KM = 6371.0


def haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate great-circle distance between two coordinates in kilometres
    using the Haversine formula.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def build_distance_matrix(
    coordinates: List[Tuple[float, float]]
) -> List[List[float]]:
    """
    Build an N×N symmetric distance matrix (km) from a list of (lat, lon) pairs.
    """
    n = len(coordinates)
    matrix: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dist = haversine_distance(
                coordinates[i][0], coordinates[i][1],
                coordinates[j][0], coordinates[j][1],
            )
            matrix[i][j] = dist
            matrix[j][i] = dist
    return matrix


# ── Fuel & Carbon Estimates ───────────────────────────────────────────────────

AVG_FUEL_CONSUMPTION_L_PER_100KM = 8.5     # litres per 100 km (typical van)
CO2_PER_LITRE_PETROL_KG = 2.31             # kg CO₂ per litre burned


def estimate_fuel_litres(distance_km: float) -> float:
    return round((distance_km / 100) * AVG_FUEL_CONSUMPTION_L_PER_100KM, 3)


def estimate_co2_kg(distance_km: float) -> float:
    return round(estimate_fuel_litres(distance_km) * CO2_PER_LITRE_PETROL_KG, 3)


def estimate_travel_time_minutes(distance_km: float, avg_speed_kmh: float = 40.0) -> float:
    """Estimate travel time assuming a constant average speed."""
    if avg_speed_kmh <= 0:
        return 0.0
    return round((distance_km / avg_speed_kmh) * 60, 1)


# ── Text helpers ──────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text


def mask_email(email: str) -> str:
    """Return a privacy-masked version: us**@domain.com"""
    local, _, domain = email.partition("@")
    return f"{local[:2]}**@{domain}"


# ── Serialisation ─────────────────────────────────────────────────────────────

def uuid_to_str(value: Any) -> Any:
    """Recursively convert UUID objects in a dict/list to strings."""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {k: uuid_to_str(v) for k, v in value.items()}
    if isinstance(value, list):
        return [uuid_to_str(v) for v in value]
    return value
