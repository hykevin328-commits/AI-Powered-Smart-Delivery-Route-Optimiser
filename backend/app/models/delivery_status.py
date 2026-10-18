"""
DeliveryStatusLog – immutable audit trail for every status change on an order.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.delivery_order import OrderStatus

if TYPE_CHECKING:
    from app.models.delivery_order import DeliveryOrder


class DeliveryStatusLog(BaseModel):
    __tablename__ = "delivery_status_logs"

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("delivery_orders.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # ── Status Transition ─────────────────────────────────────────────────────
    from_status: Mapped[Optional[OrderStatus]] = mapped_column(
        Enum(OrderStatus, name="order_status"), nullable=True
    )
    to_status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"), nullable=False
    )
    changed_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    # ── Location at Status Change ─────────────────────────────────────────────
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Context ───────────────────────────────────────────────────────────────
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    order: Mapped["DeliveryOrder"] = relationship("DeliveryOrder", back_populates="status_logs")

    __table_args__ = (
        Index("ix_status_logs_order_timestamp", "order_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryStatusLog order={self.order_id} {self.from_status}→{self.to_status}>"
