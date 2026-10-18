"""
Customer Management API

GET    /customers                           – list customers (paginated, searchable)
POST   /customers                           – create customer (Admin)
GET    /customers/{id}                      – get customer detail
PUT    /customers/{id}                      – update customer (Admin)
DELETE /customers/{id}                      – soft-delete customer (Admin)
DELETE /customers/{id}/permanent            – hard-delete customer (Admin, no orders)
GET    /customers/{id}/orders               – customer delivery history
GET    /customers/{id}/stats                – customer delivery statistics
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.delivery_order import OrderStatus
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.schemas.delivery_order import DeliveryOrderResponse
from app.services.customer_service import customer_service
from app.utils.dependencies import (
    PaginationParams,
    require_admin,
    require_delivery_partner,
)
from app.utils.response import paginated_response, success_response

router = APIRouter(prefix="/customers", tags=["Customer Management"])


@router.get("", summary="List customers (paginated + searchable)")
async def list_customers(
    search: Optional[str] = Query(None, description="Search by name, phone, or email"),
    is_active: Optional[bool] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    customers, total = await customer_service.list_customers(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        search=search,
        is_active=is_active,
    )
    return paginated_response(
        data=[CustomerResponse.model_validate(c).model_dump() for c in customers],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create customer (Admin)")
async def create_customer(
    data: CustomerCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    customer = await customer_service.create(db, data)
    return success_response(
        data=CustomerResponse.model_validate(customer).model_dump(),
        message="Customer created",
        status_code=201,
    )


@router.get("/{customer_id}", summary="Get customer detail")
async def get_customer(
    customer_id: UUID,
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    customer = await customer_service.get(db, customer_id)
    return success_response(data=CustomerResponse.model_validate(customer).model_dump())


@router.put("/{customer_id}", summary="Update customer (Admin)")
async def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    customer = await customer_service.update(db, customer_id, data)
    return success_response(
        data=CustomerResponse.model_validate(customer).model_dump(),
        message="Customer updated",
    )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Soft-delete customer (Admin)")
async def deactivate_customer(
    customer_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await customer_service.delete(db, customer_id)


@router.delete(
    "/{customer_id}/permanent",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete customer – fails if orders exist (Admin)",
)
async def hard_delete_customer(
    customer_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await customer_service.hard_delete(db, customer_id)


@router.get("/{customer_id}/orders", summary="Customer delivery history")
async def customer_delivery_history(
    customer_id: UUID,
    order_status: Optional[OrderStatus] = Query(None, alias="status"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    orders, total = await customer_service.get_delivery_history(
        db,
        customer_id,
        page=pagination.page,
        page_size=pagination.page_size,
        status=order_status,
    )
    return paginated_response(
        data=[DeliveryOrderResponse.model_validate(o).model_dump() for o in orders],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{customer_id}/stats", summary="Customer delivery statistics")
async def customer_stats(
    customer_id: UUID,
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    stats = await customer_service.get_stats(db, customer_id)
    return success_response(data=stats)
