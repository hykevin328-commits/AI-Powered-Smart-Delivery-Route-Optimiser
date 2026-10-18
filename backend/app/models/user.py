"""
User model – supports Admin and Delivery Partner roles.
"""
from __future__ import annotations

import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Enum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.delivery_assignment import DeliveryAssignment
    from app.models.route_history import RouteHistory


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DELIVERY_PARTNER = "delivery_partner"


class User(BaseModel):
    __tablename__ = "users"

    # ── Identity ──────────────────────────────────────────────────────────────
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # ── Auth ──────────────────────────────────────────────────────────────────
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), nullable=False, default=UserRole.DELIVERY_PARTNER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Profile ───────────────────────────────────────────────────────────────
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    licence_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # delivery partners

    # ── Token management ──────────────────────────────────────────────────────
    refresh_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_login_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    assignments: Mapped[List["DeliveryAssignment"]] = relationship(
        "DeliveryAssignment", back_populates="delivery_partner", lazy="select"
    )
    route_histories: Mapped[List["RouteHistory"]] = relationship(
        "RouteHistory", back_populates="delivery_partner", lazy="select"
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_users_role_active", "role", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
