"""
AI prediction module unit tests.
All tests run without DB or network access.
"""
from __future__ import annotations

import pytest
from app.ai.predictor import ai_predictor


def test_delay_prediction_clear_weather():
    result = ai_predictor.predict_delay(
        distance_km=20.0,
        num_stops=5,
        traffic_factor=1.0,
        congestion_level="low",
        weather_condition="clear",
        priority="normal",
    )
    assert result["predicted_delay_minutes"] >= 0
    assert 0 <= result["delay_probability"] <= 1
    assert result["adjusted_estimated_minutes"] >= result["base_estimated_minutes"]


def test_delay_prediction_storm_increases_delay():
    clear = ai_predictor.predict_delay(
        distance_km=20.0, num_stops=3,
        weather_condition="clear", traffic_factor=1.0,
    )
    storm = ai_predictor.predict_delay(
        distance_km=20.0, num_stops=3,
        weather_condition="thunderstorm", traffic_factor=1.0,
    )
    assert storm["adjusted_estimated_minutes"] > clear["adjusted_estimated_minutes"]


def test_delay_prediction_heavy_traffic():
    normal = ai_predictor.predict_delay(distance_km=15.0, num_stops=3, traffic_factor=1.0)
    heavy = ai_predictor.predict_delay(distance_km=15.0, num_stops=3, traffic_factor=2.0)
    assert heavy["predicted_delay_minutes"] >= normal["predicted_delay_minutes"]


def test_traffic_prediction_peak_hour():
    result = ai_predictor.predict_traffic(
        hour=8, day_of_week=0,  # Monday morning peak
        latitude=12.97, longitude=77.59, current_factor=1.0
    )
    assert result["congestion_level"] == "high"
    assert result["predicted_traffic_factor"] > 1.2


def test_traffic_prediction_midnight():
    result = ai_predictor.predict_traffic(
        hour=2, day_of_week=3,  # Wednesday midnight
        latitude=12.97, longitude=77.59, current_factor=1.0
    )
    assert result["congestion_level"] == "low"
    assert result["predicted_traffic_factor"] < 1.1


def test_priority_prediction_urgent_window():
    result = ai_predictor.predict_priority(
        distance_km=5.0,
        weight_kg=2.0,
        has_time_window=True,
        current_priority="urgent",
        delay_probability=0.8,
        hour=16,
    )
    assert result["priority_score"] >= 75
    assert result["recommended_priority"] == "urgent"


def test_priority_prediction_low():
    result = ai_predictor.predict_priority(
        distance_km=50.0,
        weight_kg=1.0,
        has_time_window=False,
        current_priority="low",
        delay_probability=0.1,
        hour=10,
    )
    assert result["recommended_priority"] in ("low", "normal")


def test_fuel_prediction_petrol():
    result = ai_predictor.predict_fuel(
        distance_km=30.0,
        vehicle_efficiency_l_per_100km=8.5,
        traffic_factor=1.0,
        load_kg=0.0,
        is_electric=False,
    )
    assert result["is_electric"] is False
    assert result["fuel_litres"] > 0
    assert result["co2_kg"] > 0
    # 30 km at 8.5 L/100 km = 2.55 L baseline
    assert abs(result["baseline_fuel_litres"] - 2.55) < 0.1


def test_fuel_prediction_electric():
    result = ai_predictor.predict_fuel(
        distance_km=30.0, is_electric=True
    )
    assert result["is_electric"] is True
    assert result["fuel_litres"] == 0.0
    assert result["co2_kg"] == 0.0
    assert result["energy_kwh"] > 0


def test_fuel_prediction_traffic_penalty():
    normal = ai_predictor.predict_fuel(distance_km=20.0, traffic_factor=1.0)
    heavy = ai_predictor.predict_fuel(distance_km=20.0, traffic_factor=1.8)
    assert heavy["fuel_litres"] > normal["fuel_litres"]


def test_carbon_estimate_petrol():
    result = ai_predictor.estimate_carbon(fuel_litres=5.0, is_electric=False)
    assert abs(result["co2_kg"] - 5.0 * 2.31) < 0.01
    assert result["emission_type"] == "direct (combustion)"
    assert result["trees_equivalent"] > 0


def test_carbon_estimate_electric():
    result = ai_predictor.estimate_carbon(
        fuel_litres=0.0, is_electric=True,
        energy_kwh=10.0, grid_co2_factor_kg_per_kwh=0.82
    )
    assert abs(result["co2_kg"] - 8.2) < 0.01
    assert result["emission_type"] == "indirect (grid)"


def test_weather_routing_storm():
    result = ai_predictor.weather_routing_advice("thunderstorm", 20.0, 5)
    assert result["impact_severity"] == "severe"
    assert result["delay_factor"] > 1.0
    assert result["adjusted_eta_minutes"] > 0


def test_weather_routing_clear():
    result = ai_predictor.weather_routing_advice("clear sky", 20.0, 5)
    assert result["impact_severity"] == "none"
    assert result["delay_factor"] == 1.0


def test_smart_recommendation_heavy_traffic():
    result = ai_predictor.smart_recommendation(
        distance_km=30.0, fuel_litres=3.0,
        traffic_factor=1.6, delay_minutes=25.0,
        num_stops=4, weather_condition="clear",
    )
    assert "traffic" in result.lower()


def test_smart_recommendation_optimal():
    result = ai_predictor.smart_recommendation(
        distance_km=10.0, fuel_litres=1.0,
        traffic_factor=1.0, delay_minutes=0.0,
        num_stops=3, weather_condition="clear",
    )
    assert "optimal" in result.lower()
