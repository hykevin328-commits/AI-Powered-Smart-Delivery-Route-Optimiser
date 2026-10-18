"""
TSP (Traveling Salesman Problem) solver using Google OR-Tools.

Solves the single-vehicle shortest-route problem given an integer
distance matrix and returns the ordered list of node indices.
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from app.config.settings import settings
from app.optimization.distance_matrix import units_to_km
from app.utils.exceptions import OptimizationException


def solve_tsp(
    distance_matrix: List[List[int]],
    depot_index: int = 0,
    time_limit_seconds: int = 30,
) -> Dict:
    """
    Solve the TSP and return:
        {
            "route": [0, 3, 1, 2, 0],   # node indices including depot start/end
            "total_distance_units": int,
            "total_distance_km": float,
            "solver_status": "OPTIMAL" | "FEASIBLE" | "INFEASIBLE",
            "solve_time_ms": int,
        }
    """
    n = len(distance_matrix)
    if n < 2:
        raise OptimizationException("At least 2 locations (depot + 1 stop) are required")

    start_ms = time.time()

    # ── OR-Tools setup ────────────────────────────────────────────────────────
    manager = pywrapcp.RoutingIndexManager(n, 1, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_idx: int, to_idx: int) -> int:
        from_node = manager.IndexToNode(from_idx)
        to_node = manager.IndexToNode(to_idx)
        return distance_matrix[from_node][to_node]

    transit_cb_idx = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb_idx)

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
        raise OptimizationException("TSP solver could not find a feasible solution")

    # ── Extract route ─────────────────────────────────────────────────────────
    status_map = {
        routing.ROUTING_NOT_SOLVED: "NOT_SOLVED",
        routing.ROUTING_SUCCESS: "OPTIMAL",
        routing.ROUTING_PARTIAL_SUCCESS_LOCAL_OPTIMUM_NOT_REACHED: "FEASIBLE",
        routing.ROUTING_FAIL: "INFEASIBLE",
        routing.ROUTING_FAIL_TIMEOUT: "FEASIBLE",  # timed out with a solution
        routing.ROUTING_INVALID: "INFEASIBLE",
    }
    solver_status = status_map.get(routing.status(), "UNKNOWN")

    route: List[int] = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        route.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    route.append(manager.IndexToNode(index))  # return to depot

    total_units = solution.ObjectiveValue()

    return {
        "route": route,
        "total_distance_units": total_units,
        "total_distance_km": units_to_km(total_units),
        "solver_status": solver_status,
        "solve_time_ms": solve_time_ms,
    }
