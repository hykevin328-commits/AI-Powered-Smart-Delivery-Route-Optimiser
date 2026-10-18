"""
Maps & Geocoding API

POST /maps/geocode          – address → lat/lon
POST /maps/reverse          – lat/lon → address
POST /maps/bulk-geocode     – batch address geocoding
PUT  /maps/geocode-order/{id}   – geocode an order's delivery address and store it
PUT  /maps/geocode-customer/{id} – geocode a customer's default address and store it
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.user import User
from app.schemas.geocoding import (
    GeocodeRequest,
    GeocodeResponse,
    ReverseGeocodeRequest,
    ReverseGeocodeResponse,
)
from app.services.geocoding_service import geocoding_service
from app.utils.dependencies import require_admin, require_delivery_partner
from app.utils.exceptions import NotFoundException
from app.utils.response import success_response

router = APIRouter(prefix="/maps", tags=["Maps & Geocoding"])


@router.post("/geocode", summary="Convert address to coordinates")
async def geocode_address(
    request: GeocodeRequest,
    current_user: User = Depends(require_delivery_partner),
):
    result = await geocoding_service.geocode(request)
    return success_response(data=result.model_dump())


@router.post("/reverse", summary="Convert coordinates to address")
async def reverse_geocode(
    request: ReverseGeocodeRequest,
    current_user: User = Depends(require_delivery_partner),
):
    result = await geocoding_service.reverse_geocode(request)
    return success_response(data=result.model_dump())


@router.post("/bulk-geocode", summary="Batch geocode multiple addresses")
async def bulk_geocode(
    addresses: List[str],
    admin: User = Depends(require_admin),
):
    results = await geocoding_service.bulk_geocode(addresses)
    return success_response(
        data=[
            {"address": addr, "coordinates": coords}
            for addr, coords in zip(addresses, results)
        ],
        message=f"Geocoded {len(addresses)} addresses",
    )


@router.put("/geocode-order/{order_id}", summary="Geocode and store coordinates for a delivery order")
async def geocode_order(
    order_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models.delivery_order import DeliveryOrder
    from sqlalchemy import select

    result = await db.execute(select(DeliveryOrder).where(DeliveryOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException("Order")

    geo = await geocoding_service.geocode(
        GeocodeRequest(address=order.delivery_address, city=order.delivery_city)
    )
    order.delivery_latitude = geo.latitude
    order.delivery_longitude = geo.longitude
    await db.flush()

    return success_response(
        data={
            "order_id": str(order_id),
            "latitude": geo.latitude,
            "longitude": geo.longitude,
            "formatted_address": geo.formatted_address,
        },
        message="Order coordinates updated",
    )


@router.put("/geocode-customer/{customer_id}", summary="Geocode and store coordinates for a customer")
async def geocode_customer(
    customer_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models.customer import Customer
    from sqlalchemy import select

    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundException("Customer")

    geo = await geocoding_service.geocode(
        GeocodeRequest(address=customer.address, city=customer.city, country=customer.country)
    )
    customer.latitude = geo.latitude
    customer.longitude = geo.longitude
    await db.flush()

    return success_response(
        data={
            "customer_id": str(customer_id),
            "latitude": geo.latitude,
            "longitude": geo.longitude,
            "formatted_address": geo.formatted_address,
        },
        message="Customer coordinates updated",
    )
