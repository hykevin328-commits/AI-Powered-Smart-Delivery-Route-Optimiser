"""
Vehicles API – Admin manages fleet, delivery partners can view.

GET    /vehicles            – list all vehicles
POST   /vehicles            – create vehicle (Admin)
GET    /vehicles/{id}       – get vehicle detail
PUT    /vehicles/{id}       – update vehicle (Admin)
DELETE /vehicles/{id}       – delete vehicle (Admin)
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.user import User
from app.models.vehicle import VehicleStatus
from app.schemas.vehicle import VehicleCreate, VehicleResponse, VehicleUpdate
from app.services.order_service import vehicle_service
from app.utils.dependencies import (
    PaginationParams,
    get_current_user,
    require_admin,
    require_delivery_partner,
)
from app.utils.response import paginated_response, success_response

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.get("", summary="List vehicles")
async def list_vehicles(
    status: Optional[VehicleStatus] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    vehicles, total = await vehicle_service.list_vehicles(
        db, pagination.page, pagination.page_size, status=status
    )
    return paginated_response(
        data=[VehicleResponse.model_validate(v).model_dump() for v in vehicles],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create vehicle (Admin)")
async def create_vehicle(
    data: VehicleCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await vehicle_service.create(db, data)
    return success_response(
        data=VehicleResponse.model_validate(vehicle).model_dump(),
        message="Vehicle added to fleet",
        status_code=201,
    )


@router.get("/{vehicle_id}", summary="Get vehicle detail")
async def get_vehicle(
    vehicle_id: UUID,
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await vehicle_service.get(db, vehicle_id)
    return success_response(data=VehicleResponse.model_validate(vehicle).model_dump())


@router.put("/{vehicle_id}", summary="Update vehicle (Admin)")
async def update_vehicle(
    vehicle_id: UUID,
    data: VehicleUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await vehicle_service.update(db, vehicle_id, data)
    return success_response(
        data=VehicleResponse.model_validate(vehicle).model_dump(),
        message="Vehicle updated",
    )


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete vehicle (Admin)")
async def delete_vehicle(
    vehicle_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await vehicle_service.delete(db, vehicle_id)
