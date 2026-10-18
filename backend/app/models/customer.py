"""
Customer model – stores customer contact info and default delivery location.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.delivery_order import DeliveryOrder


class Customer(BaseModel):
    __tablename__ = "customers"

    # ── Contact ───────────────────────────────────────────────────────────────
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    # ── Default Delivery Location ─────────────────────────────────────────────
    address: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(80), default="India", nullable=False)

    # ── Geocoordinates ────────────────────────────────────────────────────────
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Meta ──────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    orders: Mapped[List["DeliveryOrder"]] = relationship(
        "DeliveryOrder", back_populates="customer", lazy="select"
    )

    __table_args__ = (
        Index("ix_customers_phone", "phone"),
        Index("ix_customers_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} name={self.full_name}>"
