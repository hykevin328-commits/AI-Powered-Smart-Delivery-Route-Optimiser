"""
Analytics API

GET /analytics/summary          – KPI dashboard summary
GET /analytics/time-series      – daily/weekly/monthly trend data
GET /analytics/partners         – per-delivery-partner performance table
GET /analytics/aggregate        – trigger manual daily aggregation (Admin)
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.user import User, UserRole
from app.schemas.analytics import AnalyticsResponse
from app.services.analytics_service import analytics_service
from app.utils.dependencies import get_current_user, require_admin, require_delivery_partner
from app.utils.response import success_response

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _default_start() -> date:
    return date.today() - timedelta(days=30)


@router.get("/summary", summary="Dashboard KPI summary")
async def get_kpi_summary(
    start_date: date = Query(default_factory=_default_start),
    end_date: date = Query(default_factory=date.today),
    partner_id: Optional[UUID] = Query(None),
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    # Delivery partners can only view their own analytics
    effective_id = (
        current_user.id if current_user.role == UserRole.DELIVERY_PARTNER else partner_id
    )
    kpi = await analytics_service.get_kpi_summary(
        db, start_date, end_date, partner_id=effective_id
    )
    return success_response(data=kpi.model_dump())


@router.get("/time-series", summary="Trend data for charts")
async def get_time_series(
    start_date: date = Query(default_factory=_default_start),
    end_date: date = Query(default_factory=date.today),
    period_type: str = Query(default="daily", pattern="^(daily|weekly|monthly)$"),
    partner_id: Optional[UUID] = Query(None),
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    effective_id = (
        current_user.id if current_user.role == UserRole.DELIVERY_PARTNER else partner_id
    )
    data = await analytics_service.get_time_series(
        db, start_date, end_date, period_type=period_type, partner_id=effective_id
    )
    return success_response(data=[dp.model_dump() for dp in data])


@router.get("/partners", summary="Per-partner performance leaderboard (Admin)")
async def get_partner_performance(
    start_date: date = Query(default_factory=_default_start),
    end_date: date = Query(default_factory=date.today),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    partners = await analytics_service.get_partner_performance(db, start_date, end_date)
    return success_response(data=[p.model_dump() for p in partners])


@router.get("/dashboard", summary="Full dashboard response: KPI + time-series + partners")
async def get_full_dashboard(
    start_date: date = Query(default_factory=_default_start),
    end_date: date = Query(default_factory=date.today),
    period_type: str = Query(default="daily", pattern="^(daily|weekly|monthly)$"),
    partner_id: Optional[UUID] = Query(None),
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    is_admin = current_user.role == UserRole.ADMIN
    effective_id = current_user.id if not is_admin else partner_id

    kpi = await analytics_service.get_kpi_summary(db, start_date, end_date, effective_id)
    ts = await analytics_service.get_time_series(
        db, start_date, end_date, period_type, effective_id
    )
    partners = await analytics_service.get_partner_performance(db, start_date, end_date) if is_admin else None

    return success_response(
        data={
            "kpi": kpi.model_dump(),
            "time_series": [dp.model_dump() for dp in ts],
            "partner_performance": [p.model_dump() for p in partners] if partners else None,
        }
    )


@router.post("/aggregate", summary="Trigger daily analytics aggregation (Admin)")
async def trigger_aggregation(
    for_date: date = Query(default_factory=date.today),
    partner_id: Optional[UUID] = Query(None),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await analytics_service.aggregate_daily(db, for_date, partner_id)
    return success_response(
        message=f"Analytics aggregated for {for_date}"
        + (f" (partner {partner_id})" if partner_id else " (all partners)")
    )
