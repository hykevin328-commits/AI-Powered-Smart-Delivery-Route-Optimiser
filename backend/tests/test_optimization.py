"""
Route optimization unit tests — no DB or HTTP required.
Tests the OR-Tools solvers directly.
"""
from __future__ import annotations

import pytest

from app.optimization.distance_matrix import build_haversine_matrix, units_to_km
from app.optimization.tsp_solver import solve_tsp
from app.optimization.vrp_solver import solve_vrp
from app.optimization.route_optimizer import route_optimizer
from app.schemas.route_optimization import DeliveryLocation, OptimizeRouteRequest


# ── Distance matrix tests ────────────────────────────────────────────────────

def test_haversine_matrix_shape():
    coords = [(12.97, 77.59), (12.93, 77.62), (13.02, 77.60)]
    matrix = build_haversine_matrix(coords)
    assert len(matrix) == 3
    assert all(len(row) == 3 for row in matrix)


def test_haversine_matrix_diagonal_zero():
    coords = [(12.97, 77.59), (12.93, 77.62)]
    matrix = build_haversine_matrix(coords)
    assert matrix[0][0] == 0
    assert matrix[1][1] == 0


def test_haversine_matrix_symmetric():
    coords = [(12.97, 77.59), (12.93, 77.62), (13.02, 77.60)]
    matrix = build_haversine_matrix(coords)
    assert matrix[0][1] == matrix[1][0]
    assert matrix[0][2] == matrix[2][0]


def test_units_to_km():
    assert units_to_km(5000) == 5.0
    assert units_to_km(0) == 0.0


# ── TSP solver tests ──────────────────────────────────────────────────────────

def test_tsp_basic():
    coords = [(12.97, 77.59), (12.93, 77.62), (13.02, 77.60), (12.95, 77.65)]
    matrix = build_haversine_matrix(coords)
    result = solve_tsp(matrix, depot_index=0, time_limit_seconds=5)

    assert result["solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert result["route"][0] == 0        # starts at depot
    assert result["route"][-1] == 0       # returns to depot
    assert len(result["route"]) == len(coords) + 1
    assert result["total_distance_km"] > 0


def test_tsp_two_nodes():
    coords = [(12.97, 77.59), (12.93, 77.62)]
    matrix = build_haversine_matrix(coords)
    result = solve_tsp(matrix, depot_index=0, time_limit_seconds=5)
    assert result["solver_status"] in ("OPTIMAL", "FEASIBLE")


def test_tsp_single_location_raises():
    from app.utils.exceptions import OptimizationException
    matrix = [[0]]
    with pytest.raises(OptimizationException):
        solve_tsp(matrix)


# ── VRP solver tests ──────────────────────────────────────────────────────────

def test_vrp_two_vehicles():
    coords = [(12.97, 77.59), (12.93, 77.62), (13.02, 77.60), (12.95, 77.65), (12.98, 77.58)]
    matrix = build_haversine_matrix(coords)
    result = solve_vrp(matrix, num_vehicles=2, depot_index=0, time_limit_seconds=5)

    assert result["solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert result["total_distance_km"] > 0
    assert len(result["vehicle_routes"]) >= 1   # at least one vehicle used


def test_vrp_all_stops_served():
    coords = [(12.97, 77.59), (12.93, 77.62), (13.02, 77.60)]
    matrix = build_haversine_matrix(coords)
    result = solve_vrp(matrix, num_vehicles=2, depot_index=0, time_limit_seconds=5)

    # Collect all visited nodes (excluding depot)
    visited = set()
    for vr in result["vehicle_routes"]:
        visited.update(n for n in vr["route"] if n != 0)
    assert 1 in visited
    assert 2 in visited


# ── High-level optimizer tests ────────────────────────────────────────────────

def test_optimizer_tsp_mode():
    request = OptimizeRouteRequest(
        depot_latitude=12.9716,
        depot_longitude=77.5946,
        locations=[
            DeliveryLocation(latitude=12.9352, longitude=77.6245, label="A"),
            DeliveryLocation(latitude=12.9698, longitude=77.7500, label="B"),
            DeliveryLocation(latitude=13.0195, longitude=77.5989, label="C"),
        ],
        time_limit_seconds=5,
    )
    result = route_optimizer.optimize(request)
    assert result.algorithm == "TSP"
    assert result.solver_status in ("OPTIMAL", "FEASIBLE")
    assert result.total_distance_km > 0
    assert result.total_fuel_litres > 0
    assert result.total_co2_kg > 0
    assert len(result.vehicle_routes) == 1
    assert len(result.vehicle_routes[0].waypoints) == 5   # depot + 3 stops + return


def test_optimizer_efficiency_metric():
    request = OptimizeRouteRequest(
        depot_latitude=12.9716,
        depot_longitude=77.5946,
        locations=[
            DeliveryLocation(latitude=12.9352, longitude=77.6245),
            DeliveryLocation(latitude=12.9698, longitude=77.7500),
        ],
        time_limit_seconds=5,
    )
    result = route_optimizer.optimize(request)
    # Efficiency can be negative (optimised is longer for small graphs), but must be a number
    assert result.route_efficiency_pct is not None
