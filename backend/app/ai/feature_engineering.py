"""
Feature engineering helpers shared across all AI prediction models.
Converts raw order / route / context data into model-ready numeric feature vectors.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def time_features(dt: Optional[datetime] = None) -> Dict[str, float]:
    """Extract cyclic time features from a datetime."""
    if dt is None:
        dt = datetime.now(timezone.utc)

    hour = dt.hour
    day_of_week = dt.weekday()   # 0=Mon … 6=Sun
    day_of_month = dt.day
    month = dt.month

    # Encode cyclically so midnight and 23:00 are close
    return {
        "hour_sin": math.sin(2 * math.pi * hour / 24),
        "hour_cos": math.cos(2 * math.pi * hour / 24),
        "dow_sin": math.sin(2 * math.pi * day_of_week / 7),
        "dow_cos": math.cos(2 * math.pi * day_of_week / 7),
        "month_sin": math.sin(2 * math.pi * month / 12),
        "month_cos": math.cos(2 * math.pi * month / 12),
        "is_weekend": float(day_of_week >= 5),
        "is_morning_peak": float(7 <= hour <= 9),
        "is_evening_peak": float(17 <= hour <= 19),
    }


def order_features(
    weight_kg: Optional[float],
    distance_km: float,
    priority: str,
    num_stops: int,
    has_time_window: bool = False,
) -> Dict[str, float]:
    """Numeric features derived from the delivery order."""
    priority_map = {"low": 0.0, "normal": 1.0, "high": 2.0, "urgent": 3.0}
    return {
        "weight_kg": weight_kg or 5.0,
        "distance_km": distance_km,
        "priority_score": priority_map.get(priority, 1.0),
        "num_stops": float(num_stops),
        "has_time_window": float(has_time_window),
        "distance_per_stop": distance_km / max(num_stops, 1),
    }


def weather_features(condition: str) -> Dict[str, float]:
    """
    Convert a weather condition string to numeric impact features.
    Weather data can come from an external API; here we map known categories.
    """
    condition = condition.lower()
    features: Dict[str, float] = {
        "is_rain": float("rain" in condition or "drizzle" in condition),
        "is_fog": float("fog" in condition or "mist" in condition),
        "is_storm": float("storm" in condition or "thunder" in condition or "snow" in condition),
        "is_clear": float("clear" in condition or "sunny" in condition),
    }
    # Composite delay multiplier: 1.0 = no impact
    if features["is_storm"]:
        features["weather_delay_factor"] = 1.5
    elif features["is_rain"]:
        features["weather_delay_factor"] = 1.2
    elif features["is_fog"]:
        features["weather_delay_factor"] = 1.15
    else:
        features["weather_delay_factor"] = 1.0
    return features


def traffic_features(
    traffic_factor: float,
    congestion_level: str,
) -> Dict[str, float]:
    congestion_map = {"low": 0.0, "medium": 1.0, "high": 2.0, "severe": 3.0}
    return {
        "traffic_factor": traffic_factor,
        "congestion_level_num": congestion_map.get(congestion_level, 1.0),
        "is_high_congestion": float(traffic_factor > 1.4),
    }


def build_feature_vector(features: Dict[str, float]) -> List[float]:
    """Flatten a features dict into a sorted, reproducible list for model inference."""
    return [features[k] for k in sorted(features.keys())]
