"""
Analytics schemas – request filters and aggregated response bodies.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.common import AppSchema


# ── Query filters ─────────────────────────────────────────────────────────────

class AnalyticsFilter(AppSchema):
    start_date: date
    end_date: date
    delivery_partner_id: Optional[UUID] = None
    period_type: str = Field(default="daily", pattern="^(daily|weekly|monthly)$")


# ── Summary responses ─────────────────────────────────────────────────────────

class KPISummary(AppSchema):
    """Top-level KPI cards for the dashboard."""
    total_deliveries: int
    completed_deliveries: int
    failed_deliveries: int
    completion_rate_pct: float

    total_distance_km: float
    total_fuel_consumed_litres: float
    total_fuel_saved_litres: float

    total_co2_emitted_kg: float
    total_co2_saved_kg: float

    avg_delivery_time_minutes: float
    avg_route_efficiency_pct: float
    routes_optimised: int


class DailyDataPoint(AppSchema):
    """Single data point for time-series charts."""
    date: date
    total_deliveries: int
    completed_deliveries: int
    total_distance_km: float
    fuel_consumed_litres: float
    fuel_saved_litres: float
    co2_emitted_kg: float
    co2_saved_kg: float
    avg_delivery_time_minutes: Optional[float]
    route_efficiency_pct: Optional[float]


class PartnerPerformance(AppSchema):
    """Per-delivery-partner performance summary."""
    delivery_partner_id: UUID
    partner_name: str
    total_deliveries: int
    completed_deliveries: int
    completion_rate_pct: float
    total_distance_km: float
    avg_delivery_time_minutes: Optional[float]
    fuel_consumed_litres: float
    co2_emitted_kg: float


class AnalyticsResponse(AppSchema):
    kpi: KPISummary
    time_series: List[DailyDataPoint]
    partner_performance: Optional[List[PartnerPerformance]] = None


# ── AI prediction response ────────────────────────────────────────────────────

class DeliveryPredictionResponse(AppSchema):
    order_id: UUID
    predicted_delay_minutes: float
    delay_probability: float           # 0.0 – 1.0
    predicted_priority_score: float
    estimated_delivery_time_minutes: int
    predicted_fuel_litres: float
    predicted_co2_kg: float
    traffic_congestion_level: str      # low | medium | high
    weather_impact: str                # none | light | moderate | severe
    recommendation: str                # human-readable summary
