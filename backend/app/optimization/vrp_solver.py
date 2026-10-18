"""
VRP (Vehicle Routing Problem) solver using Google OR-Tools.

Supports:
- Multiple delivery partners / vehicles
- Per-vehicle capacity constraints
- Optional time-window constraints
- Optional return-to-depot
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from app.optimization.distance_matrix import units_to_km
from app.utils.exceptions import OptimizationException


def solve_vrp(
    distance_matrix: List[List[int]],
    num_vehicles: int,
    depot_index: int = 0,
    demands: Optional[List[int]] = None,          # weight in grams (scaled)
    vehicle_capacities: Optional[List[int]] = None,
    time_windows: Optional[List[Tuple[int, int]]] = None,  # (start_min, end_min)
    service_times: Optional[List[int]] = None,    # minutes per stop
    time_limit_seconds: int = 30,
    return_to_depot: bool = True,
) -> Dict:
    """
    Solve VRP and return per-vehicle routes.

    Returns:
        {
            "vehicle_routes": [
                {"vehicle_index": 0, "route": [0,3,1,0], "distance_km": float},
                ...
            ],
            "total_distance_km": float,
            "solver_status": str,
            "solve_time_ms": int,
            "dropped_nodes": [int],   # unserviced stops (if capacity exceeded)
        }
    """
    n = len(distance_matrix)
    if n < 2:
        raise OptimizationException("At least 2 locations required")
    if num_vehicles < 1:
        raise OptimizationException("At least 1 vehicle required")

    start_ms = time.time()

    # Depot end nodes – either same as depot (return) or distinct dummy ends
    ends = [depot_index] * num_vehicles if return_to_depot else None

    manager = pywrapcp.RoutingIndexManager(
        n,
        num_vehicles,
        [depot_index] * num_vehicles,
        ends if ends else [depot_index] * num_vehicles,
    )
    routing = pywrapcp.RoutingModel(manager)

    # ── Distance / cost ───────────────────────────────────────────────────────
    def distance_callback(from_idx: int, to_idx: int) -> int:
        return distance_matrix[manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)]

    transit_cb_idx = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb_idx)

    # ── Capacity constraint ───────────────────────────────────────────────────
    if demands and vehicle_capacities:
        def demand_callback(idx: int) -> int:
            node = manager.IndexToNode(idx)
            return demands[node] if node < len(demands) else 0

        demand_cb_idx = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_cb_idx,
            0,                  # null capacity slack
            vehicle_capacities,
            True,               # start cumul to zero
            "Capacity",
        )

    # ── Time-window constraint ────────────────────────────────────────────────
    if time_windows and service_times:
        def time_callback(from_idx: int, to_idx: int) -> int:
            from_node = manager.IndexToNode(from_idx)
            to_node = manager.IndexToNode(to_idx)
            travel = distance_matrix[from_node][to_node] // 1000  # units → minutes proxy
            svc = service_times[from_node] if from_node < len(service_times) else 0
            return travel + svc

        time_cb_idx = routing.RegisterTransitCallback(time_callback)
        routing.AddDimension(
            time_cb_idx,
            30,     # allowed waiting time (minutes)
            480,    # max route duration (8 hours)
            False,
            "Time",
        )
        time_dim = routing.GetDimensionOrDie("Time")
        for node_idx, (tw_start, tw_end) in enumerate(time_windows):
            if node_idx == depot_index:
                continue
            idx = manager.NodeToIndex(node_idx)
            time_dim.CumulVar(idx).SetRange(tw_start, tw_end)

    # ── Allow dropping nodes if infeasible (with penalty) ─────────────────────
    penalty = 100_000_000
    for node in range(1, n):
        routing.AddDisjunction([manager.NodeToIndex(node)], penalty)

    # ── Search parameters ─────────────────────────────────────────────────────
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_params.time_limit.seconds = time_limit_seconds

    solution = routing.SolveWithParameters(search_params)
    solve_time_ms = int((time.time() - start_ms) * 1000)

    if not solution:
        raise OptimizationException("VRP solver could not find a feasible solution")

    # ── Extract routes ────────────────────────────────────────────────────────
    status_map = {
        routing.ROUTING_NOT_SOLVED: "NOT_SOLVED",
        routing.ROUTING_SUCCESS: "OPTIMAL",
        routing.ROUTING_PARTIAL_SUCCESS_LOCAL_OPTIMUM_NOT_REACHED: "FEASIBLE",
        routing.ROUTING_FAIL: "INFEASIBLE",
        routing.ROUTING_FAIL_TIMEOUT: "FEASIBLE",
        routing.ROUTING_INVALID: "INFEASIBLE",
    }
    solver_status = status_map.get(routing.status(), "UNKNOWN")

    vehicle_routes: List[Dict] = []
    total_units = 0

    for v in range(num_vehicles):
        route_nodes: List[int] = []
        route_units = 0
        index = routing.Start(v)
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route_nodes.append(node)
            prev_index = index
            index = solution.Value(routing.NextVar(index))
            route_units += routing.GetArcCostForVehicle(prev_index, index, v)
        route_nodes.append(manager.IndexToNode(index))  # end depot

        # Skip empty routes (vehicle not used)
        unique_stops = [n for n in route_nodes if n != depot_index]
        if unique_stops:
            total_units += route_units
            vehicle_routes.append({
                "vehicle_index": v,
                "route": route_nodes,
                "route_units": route_units,
                "distance_km": units_to_km(route_units),
                "stop_count": len(unique_stops),
            })

    # Collect dropped nodes
    dropped: List[int] = []
    for node in range(1, n):
        idx = manager.NodeToIndex(node)
        if solution.Value(routing.NextVar(idx)) == idx:
            dropped.append(node)

    return {
        "vehicle_routes": vehicle_routes,
        "total_distance_km": units_to_km(total_units),
        "solver_status": solver_status,
        "solve_time_ms": solve_time_ms,
        "dropped_nodes": dropped,
    }
