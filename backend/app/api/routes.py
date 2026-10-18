"""
Route Optimization API

POST /routes/optimize           – optimize route (TSP or VRP)
POST /routes/recalculate        – live recalculation for an active assignment
GET  /routes/history            – paginated route history
GET  /routes/history/{id}       – single route history detail
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.delivery_assignment import AssignmentStatus, DeliveryAssignment
from app.models.delivery_order import DeliveryOrder, OrderStatus
from app.models.route_history import RouteHistory
from app.models.user import User, UserRole
from app.optimization.route_optimizer import route_optimizer
from app.schemas.route_history import RouteHistoryResponse
from app.schemas.route_optimization import (
    OptimizeRouteRequest,
    OptimizeRouteResponse,
    RecalculateRouteRequest,
)
from app.utils.dependencies import (
    PaginationParams,
    get_current_user,
    require_delivery_partner,
)
from app.utils.exceptions import ForbiddenException, NotFoundException
from app.utils.helpers import (
    estimate_co2_kg,
    estimate_fuel_litres,
    estimate_travel_time_minutes,
    utcnow,
)
from app.utils.pagination import paginate
from app.utils.response import paginated_response, success_response

router = APIRouter(prefix="/routes", tags=["Route Optimization"])


@router.post("/optimize", summary="Optimize delivery route (TSP / VRP)")
async def optimize_route(
    request: OptimizeRouteRequest,
    current_user: User = Depends(require_delivery_partner),
):
    """
    Submit delivery coordinates and receive the optimised route sequence.
    - 1 vehicle config (or none) → TSP
    - 2+ vehicle configs → VRP multi-agent optimisation
    """
    result: OptimizeRouteResponse = route_optimizer.optimize(request)
    return success_response(
        data=result.model_dump(),
        message=f"Route optimised using {result.algorithm} — {result.solver_status}",
    )


@router.post("/recalculate", summary="Live route recalculation for active assignment")
async def recalculate_route(
    request: RecalculateRouteRequest,
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    Recalculate the optimised route for an ongoing delivery run.
    Supports adding newly assigned orders and removing cancelled ones.
    """
    # Fetch the assignment
    result = await db.execute(
        select(DeliveryAssignment).where(
            and_(
                DeliveryAssignment.id == request.assignment_id,
                DeliveryAssignment.status == AssignmentStatus.ACTIVE,
            )
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundException("Active Assignment")

    # Delivery partners may only recalculate their own
    if (
        current_user.role == UserRole.DELIVERY_PARTNER
        and assignment.delivery_partner_id != current_user.id
    ):
        raise ForbiddenException()

    # Build location list from remaining active orders
    orders_q = await db.execute(
        select(DeliveryOrder).where(
            and_(
                DeliveryOrder.id.in_(
                    select(DeliveryAssignment.order_id).where(
                        and_(
                            DeliveryAssignment.delivery_partner_id == assignment.delivery_partner_id,
                            DeliveryAssignment.status == AssignmentStatus.ACTIVE,
                        )
                    )
                ),
                DeliveryOrder.status.notin_([OrderStatus.DELIVERED, OrderStatus.CANCELLED]),
            )
        )
    )
    active_orders = orders_q.scalars().all()

    # Exclude cancelled order IDs if provided
    cancelled_ids = set(request.cancelled_order_ids or [])
    locations = []
    from app.schemas.route_optimization import DeliveryLocation

    for order in active_orders:
        if order.id in cancelled_ids:
            continue
        if order.delivery_latitude and order.delivery_longitude:
            locations.append(
                DeliveryLocation(
                    order_id=order.id,
                    latitude=order.delivery_latitude,
                    longitude=order.delivery_longitude,
                    label=order.order_number,
                )
            )

    if not locations:
        return success_response(
            data={"message": "No remaining stops – route complete"},
            message="No active stops remaining",
        )

    optimize_req = OptimizeRouteRequest(
        depot_latitude=request.current_latitude,
        depot_longitude=request.current_longitude,
        locations=locations,
        return_to_depot=False,  # driver is mid-route
    )
    recalculated = route_optimizer.optimize(optimize_req)
    return success_response(
        data=recalculated.model_dump(),
        message="Route recalculated",
    )


@router.get("/history", summary="Get route history (paginated)")
async def get_route_history(
    partner_id: Optional[UUID] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    query = select(RouteHistory).order_by(RouteHistory.route_date.desc())

    if current_user.role == UserRole.DELIVERY_PARTNER:
        query = query.where(RouteHistory.delivery_partner_id == current_user.id)
    elif partner_id:
        query = query.where(RouteHistory.delivery_partner_id == partner_id)

    items, total = await paginate(db, query, pagination.page, pagination.page_size)
    return paginated_response(
        data=[RouteHistoryResponse.model_validate(r).model_dump() for r in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/history/{history_id}", summary="Get single route history entry")
async def get_route_history_detail(
    history_id: UUID,
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    rh = await db.get(RouteHistory, history_id)
    if not rh:
        raise NotFoundException("Route History")
    if (
        current_user.role == UserRole.DELIVERY_PARTNER
        and rh.delivery_partner_id != current_user.id
    ):
        raise ForbiddenException()
    return success_response(data=RouteHistoryResponse.model_validate(rh).model_dump())
