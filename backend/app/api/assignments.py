"""
Delivery Assignments API

GET  /assignments                    – list assignments (Admin sees all, partner sees own)
GET  /assignments/{id}               – get single assignment detail
PUT  /assignments/{id}               – update assignment (vehicle, sequence, notes)
POST /assignments/{id}/complete      – mark assignment complete with actual metrics
GET  /assignments/partner/{partner_id}/active – get active assignments for a partner
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.database import get_db
from app.models.delivery_assignment import AssignmentStatus, DeliveryAssignment
from app.models.user import User, UserRole
from app.models.vehicle import VehicleStatus
from app.schemas.delivery_assignment import (
    AssignmentResponse,
    AssignmentUpdate,
    CompleteAssignmentRequest,
)
from app.utils.dependencies import (
    PaginationParams,
    get_current_user,
    require_admin,
    require_delivery_partner,
)
from app.utils.exceptions import ForbiddenException, NotFoundException
from app.utils.helpers import utcnow
from app.utils.pagination import paginate
from app.utils.response import paginated_response, success_response

router = APIRouter(prefix="/assignments", tags=["Delivery Assignments"])


def _assignment_to_dict(a: DeliveryAssignment) -> dict:
    return AssignmentResponse.model_validate(a).model_dump()


@router.get("", summary="List assignments")
async def list_assignments(
    status: Optional[AssignmentStatus] = Query(None),
    partner_id: Optional[UUID] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(DeliveryAssignment)
        .options(
            selectinload(DeliveryAssignment.order),
            selectinload(DeliveryAssignment.vehicle),
        )
        .order_by(DeliveryAssignment.assigned_at.desc())
    )

    # Partners can only see their own
    if current_user.role == UserRole.DELIVERY_PARTNER:
        query = query.where(DeliveryAssignment.delivery_partner_id == current_user.id)
    elif partner_id:
        query = query.where(DeliveryAssignment.delivery_partner_id == partner_id)

    if status:
        query = query.where(DeliveryAssignment.status == status)

    items, total = await paginate(db, query, pagination.page, pagination.page_size)
    return paginated_response(
        data=[_assignment_to_dict(a) for a in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/partner/{partner_id}/active", summary="Get active assignments for a delivery partner")
async def get_active_assignments(
    partner_id: UUID,
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    # Delivery partners can only query their own active assignments
    if current_user.role == UserRole.DELIVERY_PARTNER and current_user.id != partner_id:
        raise ForbiddenException()

    result = await db.execute(
        select(DeliveryAssignment)
        .options(
            selectinload(DeliveryAssignment.order),
            selectinload(DeliveryAssignment.vehicle),
        )
        .where(
            and_(
                DeliveryAssignment.delivery_partner_id == partner_id,
                DeliveryAssignment.status == AssignmentStatus.ACTIVE,
            )
        )
        .order_by(DeliveryAssignment.sequence_number)
    )
    assignments = result.scalars().all()
    return success_response(data=[_assignment_to_dict(a) for a in assignments])


@router.get("/{assignment_id}", summary="Get assignment detail")
async def get_assignment(
    assignment_id: UUID,
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DeliveryAssignment)
        .options(
            selectinload(DeliveryAssignment.order),
            selectinload(DeliveryAssignment.vehicle),
        )
        .where(DeliveryAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundException("Assignment")

    # Delivery partners cannot view others' assignments
    if (
        current_user.role == UserRole.DELIVERY_PARTNER
        and assignment.delivery_partner_id != current_user.id
    ):
        raise ForbiddenException()

    return success_response(data=_assignment_to_dict(assignment))


@router.put("/{assignment_id}", summary="Update assignment metadata (Admin)")
async def update_assignment(
    assignment_id: UUID,
    data: AssignmentUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DeliveryAssignment).where(DeliveryAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundException("Assignment")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(assignment, field, value)
    await db.flush()
    return success_response(data=_assignment_to_dict(assignment), message="Assignment updated")


@router.post("/{assignment_id}/complete", summary="Complete an assignment with actual metrics")
async def complete_assignment(
    assignment_id: UUID,
    data: CompleteAssignmentRequest,
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DeliveryAssignment).where(DeliveryAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundException("Assignment")

    if (
        current_user.role == UserRole.DELIVERY_PARTNER
        and assignment.delivery_partner_id != current_user.id
    ):
        raise ForbiddenException()

    assignment.status = AssignmentStatus.COMPLETED
    assignment.completed_at = utcnow()

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(assignment, field, value)

    # Free up vehicle
    if assignment.vehicle_id:
        vehicle = await db.get(__import__("app.models.vehicle", fromlist=["Vehicle"]).Vehicle, assignment.vehicle_id)
        if vehicle:
            vehicle.status = VehicleStatus.AVAILABLE

    await db.flush()
    return success_response(data=_assignment_to_dict(assignment), message="Assignment completed")
