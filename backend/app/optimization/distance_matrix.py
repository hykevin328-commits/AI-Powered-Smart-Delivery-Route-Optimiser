"""
Distance matrix builder.

Builds an integer distance matrix (metres, scaled) suitable for OR-Tools.
Falls back to Haversine if no traffic data is available; otherwise blends
traffic-adjusted durations.
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from app.utils.helpers import haversine_distance

# OR-Tools works with integers; we scale km → metres × 10 for sub-km precision
_SCALE = 1000  # 1 km → 1000 units


def _km_to_units(km: float) -> int:
    return int(km * _SCALE)


def build_haversine_matrix(
    coordinates: List[Tuple[float, float]]  # (lat, lon)
) -> List[List[int]]:
    """Return an N×N integer distance matrix using Haversine distances."""
    n = len(coordinates)
    matrix: List[List[int]] = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                km = haversine_distance(
                    coordinates[i][0], coordinates[i][1],
                    coordinates[j][0], coordinates[j][1],
                )
                matrix[i][j] = _km_to_units(km)
    return matrix


def build_traffic_matrix(
    coordinates: List[Tuple[float, float]],
    traffic_durations: Optional[List[List[float]]],   # minutes
    avg_speed_kmh: float = 40.0,
) -> List[List[int]]:
    """
    Build a distance matrix adjusted for live traffic.
    If traffic_durations is provided, convert travel time → effective distance.
    Otherwise fall back to Haversine.
    """
    if traffic_durations is None:
        return build_haversine_matrix(coordinates)

    n = len(coordinates)
    matrix: List[List[int]] = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                # Convert traffic-adjusted minutes to km equivalent
                mins = traffic_durations[i][j]
                km = (mins / 60.0) * avg_speed_kmh
                matrix[i][j] = _km_to_units(km)
    return matrix


def units_to_km(units: int) -> float:
    return round(units / _SCALE, 3)
