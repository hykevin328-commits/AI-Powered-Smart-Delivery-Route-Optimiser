"""
Customer service – CRUD + delivery history.
"""
from __future__ import annotations

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.delivery_order import DeliveryOrder, OrderStatus
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.utils.exceptions import AlreadyExistsException, NotFoundException
from app.utils.pagination import paginate


class CustomerService:

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(self, db: AsyncSession, data: CustomerCreate) -> Customer:
        if data.email:
            existing = await db.execute(
                select(Customer).where(Customer.email == data.email.lower())
            )
            if existing.scalar_one_or_none():
                raise AlreadyExistsException("Customer email")

        customer = Customer(**data.model_dump())
        if customer.email:
            customer.email = customer.email.lower()
        db.add(customer)
        await db.flush()
        return customer

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get(self, db: AsyncSession, customer_id: UUID) -> Customer:
        customer = await db.get(Customer, customer_id)
        if not customer:
            raise NotFoundException("Customer")
        return customer

    async def list_customers(
        self,
        db: AsyncSession,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Customer], int]:
        query = select(Customer).order_by(Customer.full_name)

        filters = []
        if search:
            term = f"%{search.lower()}%"
            filters.append(
                func.lower(Customer.full_name).like(term)
                | func.lower(Customer.phone).like(term)
                | func.lower(Customer.email).like(term)
            )
        if is_active is not None:
            filters.append(Customer.is_active == is_active)

        if filters:
            query = query.where(and_(*filters))

        return await paginate(db, query, page, page_size)

    # ── Update ────────────────────────────────────────────────────────────────

    async def update(
        self, db: AsyncSession, customer_id: UUID, data: CustomerUpdate
    ) -> Customer:
        customer = await self.get(db, customer_id)
        update_data = data.model_dump(exclude_none=True)

        # Normalise email if being updated
        if "email" in update_data and update_data["email"]:
            update_data["email"] = update_data["email"].lower()
            # Check uniqueness
            existing = await db.execute(
                select(Customer).where(
                    and_(
                        Customer.email == update_data["email"],
                        Customer.id != customer_id,
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise AlreadyExistsException("Customer email")

        for field, value in update_data.items():
            setattr(customer, field, value)
        await db.flush()
        return customer

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, db: AsyncSession, customer_id: UUID) -> None:
        customer = await self.get(db, customer_id)
        # Soft-delete: mark inactive rather than hard-delete
        customer.is_active = False
        await db.flush()

    async def hard_delete(self, db: AsyncSession, customer_id: UUID) -> None:
        """Permanent delete – fails if customer has any orders."""
        customer = await self.get(db, customer_id)
        count_result = await db.execute(
            select(func.count()).select_from(DeliveryOrder).where(
                DeliveryOrder.customer_id == customer_id
            )
        )
        if count_result.scalar_one() > 0:
            from app.utils.exceptions import ValidationException
            raise ValidationException(
                "Cannot delete a customer that has existing orders. Deactivate instead."
            )
        await db.delete(customer)
        await db.flush()

    # ── Delivery History ──────────────────────────────────────────────────────

    async def get_delivery_history(
        self,
        db: AsyncSession,
        customer_id: UUID,
        page: int,
        page_size: int,
        status: Optional[OrderStatus] = None,
    ) -> Tuple[List[DeliveryOrder], int]:
        await self.get(db, customer_id)  # validates existence

        query = (
            select(DeliveryOrder)
            .where(DeliveryOrder.customer_id == customer_id)
            .order_by(DeliveryOrder.created_at.desc())
        )
        if status:
            query = query.where(DeliveryOrder.status == status)

        return await paginate(db, query, page, page_size)

    # ── Statistics ────────────────────────────────────────────────────────────

    async def get_stats(self, db: AsyncSession, customer_id: UUID) -> dict:
        await self.get(db, customer_id)

        result = await db.execute(
            select(
                func.count(DeliveryOrder.id).label("total"),
                func.count(DeliveryOrder.id).filter(
                    DeliveryOrder.status == OrderStatus.DELIVERED
                ).label("delivered"),
                func.count(DeliveryOrder.id).filter(
                    DeliveryOrder.status == OrderStatus.CANCELLED
                ).label("cancelled"),
                func.count(DeliveryOrder.id).filter(
                    DeliveryOrder.status == OrderStatus.FAILED
                ).label("failed"),
            ).where(DeliveryOrder.customer_id == customer_id)
        )
        row = result.one()
        return {
            "total_orders": row.total,
            "delivered": row.delivered,
            "cancelled": row.cancelled,
            "failed": row.failed,
            "completion_rate": round(row.delivered / row.total * 100, 1) if row.total else 0,
        }


customer_service = CustomerService()
