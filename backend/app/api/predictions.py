"""
AI Prediction API

POST /ai/predict/delay          – delivery delay prediction
POST /ai/predict/traffic        – traffic congestion prediction
POST /ai/predict/priority       – delivery priority recommendation
POST /ai/predict/fuel           – fuel consumption prediction
POST /ai/predict/carbon         – carbon emission estimation
POST /ai/predict/weather-route  – weather-aware routing advice
GET  /ai/predict/order/{id}     – full AI analysis for a single order
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.predictor import ai_predictor
from app.config.database import get_db
from app.models.user import User
from app.schemas.common import AppSchema
from app.schemas.analytics import DeliveryPredictionResponse
from app.utils.dependencies import require_delivery_partner
from app.utils.exceptions import NotFoundException
from app.utils.response import success_response

router = APIRouter(prefix="/ai", tags=["AI Predictions"])


# ── Request bodies ────────────────────────────────────────────────────────────

class DelayPredictRequest(AppSchema):
    distance_km: float = Field(..., gt=0)
    num_stops: int = Field(..., ge=1)
    traffic_factor: float = Field(default=1.0, ge=0.5, le=5.0)
    congestion_level: str = Field(default="low", pattern="^(low|medium|high|severe)$")
    weather_condition: str = "clear"
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    scheduled_at: Optional[datetime] = None


class TrafficPredictRequest(AppSchema):
    hour: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    latitude: float
    longitude: float
    current_factor: float = Field(default=1.0, ge=0.5, le=5.0)


class PriorityPredictRequest(AppSchema):
    distance_km: float = Field(..., gt=0)
    weight_kg: float = Field(default=5.0, ge=0)
    has_time_window: bool = False
    current_priority: str = Field(default="normal")
    delay_probability: float = Field(default=0.3, ge=0, le=1)
    hour: int = Field(default=10, ge=0, le=23)


class FuelPredictRequest(AppSchema):
    distance_km: float = Field(..., gt=0)
    vehicle_efficiency_l_per_100km: float = Field(default=8.5, gt=0)
    traffic_factor: float = Field(default=1.0, ge=0.5, le=5.0)
    load_kg: float = Field(default=0.0, ge=0)
    is_electric: bool = False


class CarbonEstimateRequest(AppSchema):
    fuel_litres: float = Field(default=0.0, ge=0)
    is_electric: bool = False
    energy_kwh: float = Field(default=0.0, ge=0)
    grid_co2_factor_kg_per_kwh: float = Field(default=0.82, gt=0)


class WeatherRouteRequest(AppSchema):
    weather_condition: str
    distance_km: float = Field(..., gt=0)
    num_stops: int = Field(..., ge=1)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/predict/delay", summary="Predict delivery delay")
async def predict_delay(
    body: DelayPredictRequest,
    current_user: User = Depends(require_delivery_partner),
):
    result = ai_predictor.predict_delay(
        distance_km=body.distance_km,
        num_stops=body.num_stops,
        traffic_factor=body.traffic_factor,
        congestion_level=body.congestion_level,
        weather_condition=body.weather_condition,
        priority=body.priority,
        scheduled_dt=body.scheduled_at,
    )
    return success_response(data=result, message="Delay prediction computed")


@router.post("/predict/traffic", summary="Predict traffic congestion for a future time")
async def predict_traffic(
    body: TrafficPredictRequest,
    current_user: User = Depends(require_delivery_partner),
):
    result = ai_predictor.predict_traffic(
        hour=body.hour,
        day_of_week=body.day_of_week,
        latitude=body.latitude,
        longitude=body.longitude,
        current_factor=body.current_factor,
    )
    return success_response(data=result, message="Traffic prediction computed")


@router.post("/predict/priority", summary="Predict optimal delivery priority")
async def predict_priority(
    body: PriorityPredictRequest,
    current_user: User = Depends(require_delivery_partner),
):
    result = ai_predictor.predict_priority(
        distance_km=body.distance_km,
        weight_kg=body.weight_kg,
        has_time_window=body.has_time_window,
        current_priority=body.current_priority,
        delay_probability=body.delay_probability,
        hour=body.hour,
    )
    return success_response(data=result, message="Priority recommendation computed")


@router.post("/predict/fuel", summary="Predict fuel consumption")
async def predict_fuel(
    body: FuelPredictRequest,
    current_user: User = Depends(require_delivery_partner),
):
    result = ai_predictor.predict_fuel(
        distance_km=body.distance_km,
        vehicle_efficiency_l_per_100km=body.vehicle_efficiency_l_per_100km,
        traffic_factor=body.traffic_factor,
        load_kg=body.load_kg,
        is_electric=body.is_electric,
    )
    return success_response(data=result, message="Fuel prediction computed")


@router.post("/predict/carbon", summary="Estimate carbon emissions")
async def estimate_carbon(
    body: CarbonEstimateRequest,
    current_user: User = Depends(require_delivery_partner),
):
    result = ai_predictor.estimate_carbon(
        fuel_litres=body.fuel_litres,
        is_electric=body.is_electric,
        grid_co2_factor_kg_per_kwh=body.grid_co2_factor_kg_per_kwh,
        energy_kwh=body.energy_kwh,
    )
    return success_response(data=result, message="Carbon emission estimate computed")


@router.post("/predict/weather-route", summary="Weather-aware routing advice")
async def weather_route_advice(
    body: WeatherRouteRequest,
    current_user: User = Depends(require_delivery_partner),
):
    result = ai_predictor.weather_routing_advice(
        weather_condition=body.weather_condition,
        distance_km=body.distance_km,
        num_stops=body.num_stops,
    )
    return success_response(data=result)


@router.get("/predict/order/{order_id}", summary="Full AI analysis for a delivery order")
async def predict_for_order(
    order_id: UUID,
    weather_condition: str = Query(default="clear"),
    traffic_factor: float = Query(default=1.0, ge=0.5, le=5.0),
    congestion_level: str = Query(default="low"),
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    from app.models.delivery_order import DeliveryOrder
    from sqlalchemy import select

    result = await db.execute(select(DeliveryOrder).where(DeliveryOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException("Order")

    # Calculate distance from pickup → delivery (fallback: 10 km estimate)
    distance_km = 10.0
    if (order.pickup_latitude and order.pickup_longitude
            and order.delivery_latitude and order.delivery_longitude):
        from app.utils.helpers import haversine_distance
        distance_km = haversine_distance(
            order.pickup_latitude, order.pickup_longitude,
            order.delivery_latitude, order.delivery_longitude,
        )

    now = datetime.now(timezone.utc)
    delay_result = ai_predictor.predict_delay(
        distance_km=distance_km,
        num_stops=1,
        traffic_factor=traffic_factor,
        congestion_level=congestion_level,
        weather_condition=weather_condition,
        priority=order.priority.value,
        scheduled_dt=order.scheduled_date or now,
    )
    fuel_result = ai_predictor.predict_fuel(
        distance_km=distance_km,
        traffic_factor=traffic_factor,
        load_kg=order.weight_kg or 5.0,
    )
    carbon_result = ai_predictor.estimate_carbon(
        fuel_litres=fuel_result["fuel_litres"]
    )
    priority_result = ai_predictor.predict_priority(
        distance_km=distance_km,
        weight_kg=order.weight_kg or 5.0,
        has_time_window=bool(order.delivery_window_start),
        current_priority=order.priority.value,
        delay_probability=delay_result["delay_probability"],
        hour=now.hour,
    )
    recommendation = ai_predictor.smart_recommendation(
        distance_km=distance_km,
        fuel_litres=fuel_result["fuel_litres"],
        traffic_factor=traffic_factor,
        delay_minutes=delay_result["predicted_delay_minutes"],
        num_stops=1,
        weather_condition=weather_condition,
    )

    response = DeliveryPredictionResponse(
        order_id=order_id,
        predicted_delay_minutes=delay_result["predicted_delay_minutes"],
        delay_probability=delay_result["delay_probability"],
        predicted_priority_score=priority_result["priority_score"],
        estimated_delivery_time_minutes=int(delay_result["adjusted_estimated_minutes"]),
        predicted_fuel_litres=fuel_result["fuel_litres"],
        predicted_co2_kg=carbon_result["co2_kg"],
        traffic_congestion_level=congestion_level,
        weather_impact=ai_predictor.weather_routing_advice(weather_condition, distance_km, 1)["impact_severity"],
        recommendation=recommendation,
    )

    # Persist AI predictions back to the order
    order.predicted_delay_minutes = response.predicted_delay_minutes
    order.predicted_priority_score = response.predicted_priority_score
    order.estimated_delivery_time_minutes = response.estimated_delivery_time_minutes
    await db.flush()

    return success_response(data=response.model_dump(), message="AI analysis complete")
