"""
Delivery Orders API

GET    /orders                      – list / filter orders (paginated)
POST   /orders                      – create order (Admin)
GET    /orders/today                – today's orders for current partner
GET    /orders/{id}                 – get single order with full details
PUT    /orders/{id}                 – update order fields (Admin)
DELETE /orders/{id}                 – delete order (Admin, PENDING only)
POST   /orders/assign               – assign order(s) to a delivery partner (Admin)
PATCH  /orders/{id}/status          – update delivery status
POST   /orders/{id}/complete        – mark as delivered (Delivery Partner)
GET    /orders/{id}/status-history  – full status audit trail
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.delivery_order import OrderPriority, OrderStatus
from app.models.user import User
from app.schemas.delivery_order import (
    AssignOrderRequest,
    DeliveryOrderCreate,
    DeliveryOrderResponse,
    DeliveryOrderUpdate,
    OrderStatusUpdate,
)
from app.services.order_service import order_service
from app.utils.dependencies import (
    PaginationParams,
    get_current_user,
    require_admin,
    require_delivery_partner,
)
from app.utils.response import paginated_response, success_response

router = APIRouter(prefix="/orders", tags=["Delivery Orders"])


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", summary="List delivery orders (paginated + filterable)")
async def list_orders(
    status: Optional[OrderStatus] = Query(None),
    priority: Optional[OrderPriority] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    partner_id: Optional[UUID] = Query(None),
    scheduled_date: Optional[date] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    from app.models.user import UserRole

    # Delivery partners can only see their own assigned orders
    effective_partner_id = (
        current_user.id
        if current_user.role == UserRole.DELIVERY_PARTNER
        else partner_id
    )
    orders, total = await order_service.list_orders(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        status=status,
        priority=priority,
        customer_id=customer_id,
        partner_id=effective_partner_id,
        scheduled_date=scheduled_date,
    )
    return paginated_response(
        data=[DeliveryOrderResponse.model_validate(o).model_dump() for o in orders],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


# ── Today's Orders ────────────────────────────────────────────────────────────

@router.get("/today", summary="Get today's delivery orders")
async def get_todays_orders(
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    from app.models.user import UserRole

    partner_id = (
        current_user.id if current_user.role == UserRole.DELIVERY_PARTNER else None
    )
    orders = await order_service.get_todays_orders(db, partner_id=partner_id)
    return success_response(
        data=[DeliveryOrderResponse.model_validate(o).model_dump() for o in orders],
        message=f"{len(orders)} orders scheduled for today",
    )


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a new delivery order")
async def create_order(
    data: DeliveryOrderCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    order = await order_service.create_order(db, data)
    return success_response(
        data=DeliveryOrderResponse.model_validate(order).model_dump(),
        message="Order created",
        status_code=201,
    )


# ── Get Single ────────────────────────────────────────────────────────────────

@router.get("/{order_id}", summary="Get order details")
async def get_order(
    order_id: UUID,
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    order = await order_service.get_order(db, order_id)
    return success_response(data=DeliveryOrderResponse.model_validate(order).model_dump())


# ── Update ────────────────────────────────────────────────────────────────────

@router.put("/{order_id}", summary="Update order fields (Admin)")
async def update_order(
    order_id: UUID,
    data: DeliveryOrderUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    order = await order_service.update_order(db, order_id, data)
    return success_response(
        data=DeliveryOrderResponse.model_validate(order).model_dump(),
        message="Order updated",
    )


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete order (Admin)")
async def delete_order(
    order_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await order_service.delete_order(db, order_id)


# ── Assign ────────────────────────────────────────────────────────────────────

@router.post("/assign", status_code=status.HTTP_201_CREATED, summary="Assign orders to delivery partner (Admin)")
async def assign_orders(
    data: AssignOrderRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    assignments = await order_service.assign_orders(db, data, assigned_by=admin)
    return success_response(
        data={"assigned_count": len(assignments), "assignment_ids": [str(a.id) for a in assignments]},
        message=f"{len(assignments)} order(s) assigned successfully",
        status_code=201,
    )


# ── Status Update ─────────────────────────────────────────────────────────────

@router.patch("/{order_id}/status", summary="Update delivery status")
async def update_order_status(
    order_id: UUID,
    data: OrderStatusUpdate,
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    order = await order_service.update_status(db, order_id, data, changed_by=current_user)
    return success_response(
        data=DeliveryOrderResponse.model_validate(order).model_dump(),
        message=f"Order status updated to '{order.status}'",
    )


# ── Complete ──────────────────────────────────────────────────────────────────

@router.post("/{order_id}/complete", summary="Mark order as delivered")
async def complete_delivery(
    order_id: UUID,
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    order = await order_service.complete_delivery(db, order_id, partner=current_user)
    return success_response(
        data=DeliveryOrderResponse.model_validate(order).model_dump(),
        message="Delivery completed",
    )


# ── Status History ────────────────────────────────────────────────────────────

@router.get("/{order_id}/status-history", summary="Get full status audit trail")
async def get_status_history(
    order_id: UUID,
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    logs = await order_service.get_status_history(db, order_id)
    return success_response(
        data=[
            {
                "id": str(log.id),
                "from_status": log.from_status,
                "to_status": log.to_status,
                "changed_by": log.changed_by,
                "notes": log.notes,
                "latitude": log.latitude,
                "longitude": log.longitude,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in logs
        ]
    )
