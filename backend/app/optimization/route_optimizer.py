"""
High-level route optimization orchestrator.

Accepts the OptimizeRouteRequest schema, decides TSP vs VRP,
calls the appropriate solver, and returns OptimizeRouteResponse.
"""
from __future__ import annotations

import time
from typing import List, Optional, Tuple

from app.optimization.distance_matrix import (
    build_haversine_matrix,
    build_traffic_matrix,
    units_to_km,
)
from app.optimization.tsp_solver import solve_tsp
from app.optimization.vrp_solver import solve_vrp
from app.schemas.route_optimization import (
    DeliveryLocation,
    OptimizeRouteRequest,
    OptimizeRouteResponse,
    VehicleConfig,
    VehicleRouteResult,
    WaypointResult,
)
from app.utils.helpers import (
    estimate_co2_kg,
    estimate_fuel_litres,
    estimate_travel_time_minutes,
)


def _make_waypoints(
    route_indices: List[int],
    all_locations: List[Tuple[float, float, Optional[object], Optional[str]]],
    distance_matrix_km: List[List[float]],
    avg_speed_kmh: float = 40.0,
) -> Tuple[List[WaypointResult], float]:
    """
    Convert solver node indices → WaypointResult list.
    Returns (waypoints, cumulative_travel_minutes).
    """
    waypoints: List[WaypointResult] = []
    cumulative_minutes = 0.0

    for seq, node_idx in enumerate(route_indices):
        lat, lon, order_id, label = all_locations[node_idx]
        dist_from_prev = 0.0

        if seq > 0:
            prev_node = route_indices[seq - 1]
            dist_from_prev = distance_matrix_km[prev_node][node_idx]
            cumulative_minutes += estimate_travel_time_minutes(dist_from_prev, avg_speed_kmh)

        waypoints.append(
            WaypointResult(
                sequence=seq,
                order_id=order_id,
                label=label or f"Stop {seq}",
                latitude=lat,
                longitude=lon,
                estimated_arrival_minutes=round(cumulative_minutes, 1),
                distance_from_prev_km=round(dist_from_prev, 3),
            )
        )

    return waypoints, cumulative_minutes


class RouteOptimizer:

    def optimize(self, request: OptimizeRouteRequest) -> OptimizeRouteResponse:
        """
        Main entry point.  Chooses TSP (1 vehicle) or VRP (multi-vehicle)
        automatically based on the number of vehicle configs supplied.
        """
        start_ts = time.time()

        # ── Build coordinate list: depot first, then delivery stops ───────────
        # Each entry: (lat, lon, order_id, label)
        all_coords: List[Tuple[float, float, Optional[object], Optional[str]]] = [
            (request.depot_latitude, request.depot_longitude, None, "Depot")
        ]
        for loc in request.locations:
            all_coords.append((loc.latitude, loc.longitude, loc.order_id, loc.label))

        coord_pairs = [(c[0], c[1]) for c in all_coords]

        # ── Distance matrix ───────────────────────────────────────────────────
        int_matrix = build_haversine_matrix(coord_pairs)

        # Float km matrix for waypoint distance labelling
        n = len(coord_pairs)
        from app.utils.helpers import haversine_distance
        km_matrix = [
            [
                haversine_distance(coord_pairs[i][0], coord_pairs[i][1],
                                   coord_pairs[j][0], coord_pairs[j][1])
                for j in range(n)
            ]
            for i in range(n)
        ]

        # ── Naive (unoptimised) distance for efficiency calculation ───────────
        naive_km = sum(km_matrix[i][i + 1] for i in range(n - 1)) + km_matrix[n - 1][0]

        num_vehicles = len(request.vehicles)
        use_vrp = num_vehicles > 1

        # ── Solve ─────────────────────────────────────────────────────────────
        if use_vrp:
            raw = solve_vrp(
                distance_matrix=int_matrix,
                num_vehicles=num_vehicles,
                depot_index=0,
                time_limit_seconds=request.time_limit_seconds,
                return_to_depot=request.return_to_depot,
            )
            algorithm = "VRP"
            solver_status = raw["solver_status"]
            total_km = raw["total_distance_km"]
            solve_ms = raw["solve_time_ms"]

            vehicle_results: List[VehicleRouteResult] = []
            for vr in raw["vehicle_routes"]:
                waypoints, total_mins = _make_waypoints(
                    vr["route"], all_coords, km_matrix
                )
                fuel = estimate_fuel_litres(vr["distance_km"])
                co2 = estimate_co2_kg(vr["distance_km"])
                v_cfg: Optional[VehicleConfig] = (
                    request.vehicles[vr["vehicle_index"]]
                    if vr["vehicle_index"] < len(request.vehicles) else None
                )
                vehicle_results.append(
                    VehicleRouteResult(
                        vehicle_index=vr["vehicle_index"],
                        vehicle_id=v_cfg.vehicle_id if v_cfg else None,
                        delivery_partner_id=v_cfg.delivery_partner_id if v_cfg else None,
                        waypoints=waypoints,
                        total_distance_km=vr["distance_km"],
                        total_travel_time_minutes=total_mins,
                        estimated_fuel_litres=fuel,
                        estimated_co2_kg=co2,
                        stop_count=vr["stop_count"],
                    )
                )

        else:
            # TSP – single vehicle
            raw = solve_tsp(
                distance_matrix=int_matrix,
                depot_index=0,
                time_limit_seconds=request.time_limit_seconds,
            )
            algorithm = "TSP"
            solver_status = raw["solver_status"]
            total_km = raw["total_distance_km"]
            solve_ms = raw["solve_time_ms"]

            waypoints, total_mins = _make_waypoints(raw["route"], all_coords, km_matrix)
            fuel = estimate_fuel_litres(total_km)
            co2 = estimate_co2_kg(total_km)
            v_cfg = request.vehicles[0] if request.vehicles else None
            vehicle_results = [
                VehicleRouteResult(
                    vehicle_index=0,
                    vehicle_id=v_cfg.vehicle_id if v_cfg else None,
                    delivery_partner_id=v_cfg.delivery_partner_id if v_cfg else None,
                    waypoints=waypoints,
                    total_distance_km=total_km,
                    total_travel_time_minutes=total_mins,
                    estimated_fuel_litres=fuel,
                    estimated_co2_kg=co2,
                    stop_count=len(request.locations),
                )
            ]

        # ── Aggregate totals ──────────────────────────────────────────────────
        total_fuel = sum(v.estimated_fuel_litres for v in vehicle_results)
        total_co2 = sum(v.estimated_co2_kg for v in vehicle_results)
        total_time = sum(v.total_travel_time_minutes for v in vehicle_results)

        naive_fuel = estimate_fuel_litres(naive_km)
        fuel_saved = max(0.0, round(naive_fuel - total_fuel, 3))
        co2_saved = max(0.0, round(estimate_co2_kg(naive_km) - total_co2, 3))
        efficiency = round((1 - total_km / naive_km) * 100, 1) if naive_km > 0 else 0.0

        # ── Map coordinates (flat array of [lat, lon]) ────────────────────────
        route_coords = [[c[0], c[1]] for c in coord_pairs]

        return OptimizeRouteResponse(
            algorithm=algorithm,
            solver_status=solver_status,
            optimization_time_ms=solve_ms,
            total_distance_km=round(total_km, 3),
            total_travel_time_minutes=round(total_time, 1),
            total_fuel_litres=round(total_fuel, 3),
            total_co2_kg=round(total_co2, 3),
            fuel_saved_litres=fuel_saved,
            co2_saved_kg=co2_saved,
            route_efficiency_pct=efficiency,
            vehicle_routes=vehicle_results,
            route_coordinates=route_coords,
        )


route_optimizer = RouteOptimizer()
