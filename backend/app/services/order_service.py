"""
Delivery Order service – all business logic for CRUD and status management.
"""
from __future__ import annotations

import random
import string
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.delivery_assignment import AssignmentStatus, DeliveryAssignment
from app.models.delivery_order import DeliveryOrder, OrderPriority, OrderStatus
from app.models.delivery_status import DeliveryStatusLog
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle, VehicleStatus
from app.schemas.delivery_order import (
    AssignOrderRequest,
    DeliveryOrderCreate,
    DeliveryOrderUpdate,
    OrderStatusUpdate,
)
from app.utils.exceptions import (
    ForbiddenException,
    NotFoundException,
    OrderAlreadyAssignedException,
    OrderAlreadyCompletedException,
    ValidationException,
)
from app.utils.helpers import utcnow


def _generate_order_number() -> str:
    """Generate a unique order number like ORD-A3X9F2."""
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD-{suffix}"


# ── Terminal statuses that cannot be updated ──────────────────────────────────
TERMINAL_STATUSES = {OrderStatus.DELIVERED, OrderStatus.CANCELLED}


class OrderService:

    # ── Create ────────────────────────────────────────────────────────────────

    async def create_order(
        self, db: AsyncSession, data: DeliveryOrderCreate
    ) -> DeliveryOrder:
        # Validate customer exists
        cust = await db.get(Customer, data.customer_id)
        if not cust:
            raise NotFoundException("Customer")

        order = DeliveryOrder(
            order_number=_generate_order_number(),
            status=OrderStatus.PENDING,
            **data.model_dump(),
        )
        db.add(order)
        await db.flush()

        # Log initial status
        await self._log_status(db, order, None, OrderStatus.PENDING, "Order created")
        return order

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_order(self, db: AsyncSession, order_id: UUID) -> DeliveryOrder:
        result = await db.execute(
            select(DeliveryOrder)
            .options(selectinload(DeliveryOrder.customer))
            .where(DeliveryOrder.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundException("Order")
        return order

    async def list_orders(
        self,
        db: AsyncSession,
        page: int,
        page_size: int,
        status: Optional[OrderStatus] = None,
        priority: Optional[OrderPriority] = None,
        customer_id: Optional[UUID] = None,
        partner_id: Optional[UUID] = None,
        scheduled_date: Optional[date] = None,
    ) -> Tuple[List[DeliveryOrder], int]:
        query = (
            select(DeliveryOrder)
            .options(selectinload(DeliveryOrder.customer))
            .order_by(DeliveryOrder.created_at.desc())
        )

        filters = []
        if status:
            filters.append(DeliveryOrder.status == status)
        if priority:
            filters.append(DeliveryOrder.priority == priority)
        if customer_id:
            filters.append(DeliveryOrder.customer_id == customer_id)
        if scheduled_date:
            filters.append(func.date(DeliveryOrder.scheduled_date) == scheduled_date)
        if partner_id:
            # Filter by assigned delivery partner
            sub = select(DeliveryAssignment.order_id).where(
                and_(
                    DeliveryAssignment.delivery_partner_id == partner_id,
                    DeliveryAssignment.status == AssignmentStatus.ACTIVE,
                )
            )
            filters.append(DeliveryOrder.id.in_(sub))

        if filters:
            query = query.where(and_(*filters))

        from app.utils.pagination import paginate
        return await paginate(db, query, page, page_size)

    async def get_todays_orders(
        self, db: AsyncSession, partner_id: Optional[UUID] = None
    ) -> List[DeliveryOrder]:
        today = datetime.now(timezone.utc).date()
        query = (
            select(DeliveryOrder)
            .options(selectinload(DeliveryOrder.customer))
            .where(
                or_(
                    func.date(DeliveryOrder.scheduled_date) == today,
                    and_(
                        DeliveryOrder.scheduled_date.is_(None),
                        DeliveryOrder.status == OrderStatus.PENDING,
                    ),
                )
            )
        )
        if partner_id:
            sub = select(DeliveryAssignment.order_id).where(
                and_(
                    DeliveryAssignment.delivery_partner_id == partner_id,
                    DeliveryAssignment.status == AssignmentStatus.ACTIVE,
                )
            )
            query = query.where(DeliveryOrder.id.in_(sub))

        result = await db.execute(query)
        return list(result.scalars().all())

    # ── Update ────────────────────────────────────────────────────────────────

    async def update_order(
        self, db: AsyncSession, order_id: UUID, data: DeliveryOrderUpdate
    ) -> DeliveryOrder:
        order = await self.get_order(db, order_id)
        if order.status in TERMINAL_STATUSES:
            raise OrderAlreadyCompletedException()

        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(order, field, value)
        await db.flush()
        return order

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete_order(self, db: AsyncSession, order_id: UUID) -> None:
        order = await self.get_order(db, order_id)
        if order.status not in {OrderStatus.PENDING, OrderStatus.CANCELLED}:
            raise ValidationException(
                "Only PENDING or CANCELLED orders can be deleted. Cancel the order first."
            )
        await db.delete(order)
        await db.flush()

    # ── Assign ────────────────────────────────────────────────────────────────

    async def assign_orders(
        self, db: AsyncSession, data: AssignOrderRequest, assigned_by: User
    ) -> List[DeliveryAssignment]:
        # Validate delivery partner
        partner_result = await db.execute(
            select(User).where(
                and_(
                    User.id == data.delivery_partner_id,
                    User.role == UserRole.DELIVERY_PARTNER,
                    User.is_active == True,
                )
            )
        )
        partner = partner_result.scalar_one_or_none()
        if not partner:
            raise NotFoundException("Delivery Partner")

        # Validate vehicle if provided
        if data.vehicle_id:
            vehicle = await db.get(Vehicle, data.vehicle_id)
            if not vehicle:
                raise NotFoundException("Vehicle")
            if vehicle.status == VehicleStatus.MAINTENANCE:
                raise ValidationException("Vehicle is under maintenance")

        assignments: List[DeliveryAssignment] = []
        now = utcnow()

        for seq, order_id in enumerate(data.order_ids, start=1):
            order = await self.get_order(db, order_id)

            # Check for existing active assignment
            existing = await db.execute(
                select(DeliveryAssignment).where(
                    and_(
                        DeliveryAssignment.order_id == order_id,
                        DeliveryAssignment.status == AssignmentStatus.ACTIVE,
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise OrderAlreadyAssignedException()

            if order.status in TERMINAL_STATUSES:
                raise OrderAlreadyCompletedException()

            # Create assignment
            assignment = DeliveryAssignment(
                order_id=order_id,
                delivery_partner_id=data.delivery_partner_id,
                vehicle_id=data.vehicle_id,
                status=AssignmentStatus.ACTIVE,
                assigned_at=now,
                sequence_number=seq,
            )
            db.add(assignment)

            # Update order status
            old_status = order.status
            order.status = OrderStatus.ASSIGNED
            await self._log_status(
                db, order, old_status, OrderStatus.ASSIGNED,
                f"Assigned to partner {partner.full_name}",
                changed_by=assigned_by.full_name,
            )
            assignments.append(assignment)

        # Mark vehicle in-use
        if data.vehicle_id:
            vehicle = await db.get(Vehicle, data.vehicle_id)
            if vehicle:
                vehicle.status = VehicleStatus.IN_USE

        await db.flush()
        return assignments

    # ── Status Update ─────────────────────────────────────────────────────────

    async def update_status(
        self,
        db: AsyncSession,
        order_id: UUID,
        data: OrderStatusUpdate,
        changed_by: User,
    ) -> DeliveryOrder:
        order = await self.get_order(db, order_id)

        if order.status in TERMINAL_STATUSES and data.status != OrderStatus.CANCELLED:
            raise OrderAlreadyCompletedException()

        old_status = order.status

        # Validate allowed transitions
        if not self._is_valid_transition(old_status, data.status):
            raise ValidationException(
                f"Cannot transition from '{old_status}' to '{data.status}'"
            )

        order.status = data.status
        if data.status == OrderStatus.DELIVERED:
            order.delivered_at = utcnow()

        await self._log_status(
            db, order, old_status, data.status,
            notes=data.notes,
            changed_by=changed_by.full_name,
            latitude=data.latitude,
            longitude=data.longitude,
        )
        await db.flush()
        return order

    # ── Complete Delivery ─────────────────────────────────────────────────────

    async def complete_delivery(
        self, db: AsyncSession, order_id: UUID, partner: User
    ) -> DeliveryOrder:
        return await self.update_status(
            db,
            order_id,
            OrderStatusUpdate(status=OrderStatus.DELIVERED),
            changed_by=partner,
        )

    # ── Status history ────────────────────────────────────────────────────────

    async def get_status_history(
        self, db: AsyncSession, order_id: UUID
    ) -> List[DeliveryStatusLog]:
        result = await db.execute(
            select(DeliveryStatusLog)
            .where(DeliveryStatusLog.order_id == order_id)
            .order_by(DeliveryStatusLog.timestamp)
        )
        return list(result.scalars().all())

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _is_valid_transition(from_status: OrderStatus, to_status: OrderStatus) -> bool:
        TRANSITIONS = {
            OrderStatus.PENDING:    {OrderStatus.ASSIGNED, OrderStatus.CANCELLED},
            OrderStatus.ASSIGNED:   {OrderStatus.PICKED_UP, OrderStatus.CANCELLED},
            OrderStatus.PICKED_UP:  {OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED},
            OrderStatus.IN_TRANSIT: {OrderStatus.DELIVERED, OrderStatus.FAILED, OrderStatus.CANCELLED},
            OrderStatus.FAILED:     {OrderStatus.PENDING, OrderStatus.CANCELLED},
            OrderStatus.DELIVERED:  set(),
            OrderStatus.CANCELLED:  set(),
        }
        return to_status in TRANSITIONS.get(from_status, set())

    @staticmethod
    async def _log_status(
        db: AsyncSession,
        order: DeliveryOrder,
        from_status: Optional[OrderStatus],
        to_status: OrderStatus,
        notes: Optional[str] = None,
        changed_by: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> None:
        log = DeliveryStatusLog(
            order_id=order.id,
            from_status=from_status,
            to_status=to_status,
            notes=notes,
            changed_by=changed_by,
            latitude=latitude,
            longitude=longitude,
            timestamp=utcnow(),
        )
        db.add(log)


# ── Vehicle service ───────────────────────────────────────────────────────────

class VehicleService:

    async def create(self, db: AsyncSession, data) -> Vehicle:
        existing = await db.execute(
            select(Vehicle).where(Vehicle.registration_number == data.registration_number.upper())
        )
        if existing.scalar_one_or_none():
            raise ValidationException(
                f"Vehicle with registration '{data.registration_number}' already exists"
            )
        vehicle = Vehicle(**data.model_dump(), registration_number=data.registration_number.upper())
        db.add(vehicle)
        await db.flush()
        return vehicle

    async def get(self, db: AsyncSession, vehicle_id: UUID) -> Vehicle:
        v = await db.get(Vehicle, vehicle_id)
        if not v:
            raise NotFoundException("Vehicle")
        return v

    async def list_vehicles(
        self, db: AsyncSession, page: int, page_size: int,
        status: Optional[VehicleStatus] = None
    ) -> Tuple[List[Vehicle], int]:
        from app.utils.pagination import paginate
        query = select(Vehicle).order_by(Vehicle.created_at.desc())
        if status:
            query = query.where(Vehicle.status == status)
        return await paginate(db, query, page, page_size)

    async def update(self, db: AsyncSession, vehicle_id: UUID, data) -> Vehicle:
        v = await self.get(db, vehicle_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(v, field, value)
        await db.flush()
        return v

    async def delete(self, db: AsyncSession, vehicle_id: UUID) -> None:
        v = await self.get(db, vehicle_id)
        if v.status == VehicleStatus.IN_USE:
            raise ValidationException("Cannot delete a vehicle that is currently in use")
        await db.delete(v)
        await db.flush()


order_service = OrderService()
vehicle_service = VehicleService()
