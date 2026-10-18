"""
Analytics Service – aggregates route_histories and route_analytics
into dashboard KPIs, time-series data, and per-partner performance.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery_order import DeliveryOrder, OrderStatus
from app.models.route_analytics import RouteAnalytics
from app.models.route_history import RouteHistory
from app.models.user import User, UserRole
from app.schemas.analytics import (
    AnalyticsFilter,
    AnalyticsResponse,
    DailyDataPoint,
    KPISummary,
    PartnerPerformance,
)


class AnalyticsService:

    # ── KPI Summary ───────────────────────────────────────────────────────────

    async def get_kpi_summary(
        self,
        db: AsyncSession,
        start_date: date,
        end_date: date,
        partner_id: Optional[UUID] = None,
    ) -> KPISummary:
        query = select(
            func.sum(RouteAnalytics.total_deliveries).label("total"),
            func.sum(RouteAnalytics.completed_deliveries).label("completed"),
            func.sum(RouteAnalytics.failed_deliveries).label("failed"),
            func.sum(RouteAnalytics.total_distance_km).label("distance"),
            func.sum(RouteAnalytics.fuel_consumed_litres).label("fuel"),
            func.sum(RouteAnalytics.fuel_saved_litres).label("fuel_saved"),
            func.sum(RouteAnalytics.co2_emitted_kg).label("co2"),
            func.sum(RouteAnalytics.co2_saved_kg).label("co2_saved"),
            func.avg(RouteAnalytics.avg_delivery_time_minutes).label("avg_time"),
            func.avg(RouteAnalytics.route_efficiency_pct).label("avg_efficiency"),
            func.sum(RouteAnalytics.routes_optimised).label("routes_opt"),
        ).where(
            and_(
                RouteAnalytics.analytics_date >= start_date,
                RouteAnalytics.analytics_date <= end_date,
                RouteAnalytics.period_type == "daily",
            )
        )
        if partner_id:
            query = query.where(RouteAnalytics.delivery_partner_id == partner_id)

        result = await db.execute(query)
        row = result.one()

        total = row.total or 0
        completed = row.completed or 0
        return KPISummary(
            total_deliveries=total,
            completed_deliveries=completed,
            failed_deliveries=row.failed or 0,
            completion_rate_pct=round(completed / total * 100, 1) if total else 0.0,
            total_distance_km=round(row.distance or 0, 2),
            total_fuel_consumed_litres=round(row.fuel or 0, 2),
            total_fuel_saved_litres=round(row.fuel_saved or 0, 2),
            total_co2_emitted_kg=round(row.co2 or 0, 2),
            total_co2_saved_kg=round(row.co2_saved or 0, 2),
            avg_delivery_time_minutes=round(row.avg_time or 0, 1),
            avg_route_efficiency_pct=round(row.avg_efficiency or 0, 1),
            routes_optimised=row.routes_opt or 0,
        )

    # ── Time Series ───────────────────────────────────────────────────────────

    async def get_time_series(
        self,
        db: AsyncSession,
        start_date: date,
        end_date: date,
        period_type: str = "daily",
        partner_id: Optional[UUID] = None,
    ) -> List[DailyDataPoint]:
        query = (
            select(
                RouteAnalytics.analytics_date,
                func.sum(RouteAnalytics.total_deliveries).label("total"),
                func.sum(RouteAnalytics.completed_deliveries).label("completed"),
                func.sum(RouteAnalytics.total_distance_km).label("distance"),
                func.sum(RouteAnalytics.fuel_consumed_litres).label("fuel"),
                func.sum(RouteAnalytics.fuel_saved_litres).label("fuel_saved"),
                func.sum(RouteAnalytics.co2_emitted_kg).label("co2"),
                func.sum(RouteAnalytics.co2_saved_kg).label("co2_saved"),
                func.avg(RouteAnalytics.avg_delivery_time_minutes).label("avg_time"),
                func.avg(RouteAnalytics.route_efficiency_pct).label("efficiency"),
            )
            .where(
                and_(
                    RouteAnalytics.analytics_date >= start_date,
                    RouteAnalytics.analytics_date <= end_date,
                    RouteAnalytics.period_type == period_type,
                )
            )
            .group_by(RouteAnalytics.analytics_date)
            .order_by(RouteAnalytics.analytics_date)
        )
        if partner_id:
            query = query.where(RouteAnalytics.delivery_partner_id == partner_id)

        result = await db.execute(query)
        rows = result.all()

        return [
            DailyDataPoint(
                date=r.analytics_date,
                total_deliveries=r.total or 0,
                completed_deliveries=r.completed or 0,
                total_distance_km=round(r.distance or 0, 2),
                fuel_consumed_litres=round(r.fuel or 0, 2),
                fuel_saved_litres=round(r.fuel_saved or 0, 2),
                co2_emitted_kg=round(r.co2 or 0, 2),
                co2_saved_kg=round(r.co2_saved or 0, 2),
                avg_delivery_time_minutes=round(r.avg_time, 1) if r.avg_time else None,
                route_efficiency_pct=round(r.efficiency, 1) if r.efficiency else None,
            )
            for r in rows
        ]

    # ── Partner Performance ────────────────────────────────────────────────────

    async def get_partner_performance(
        self,
        db: AsyncSession,
        start_date: date,
        end_date: date,
    ) -> List[PartnerPerformance]:
        query = (
            select(
                RouteAnalytics.delivery_partner_id,
                User.full_name,
                func.sum(RouteAnalytics.total_deliveries).label("total"),
                func.sum(RouteAnalytics.completed_deliveries).label("completed"),
                func.sum(RouteAnalytics.total_distance_km).label("distance"),
                func.avg(RouteAnalytics.avg_delivery_time_minutes).label("avg_time"),
                func.sum(RouteAnalytics.fuel_consumed_litres).label("fuel"),
                func.sum(RouteAnalytics.co2_emitted_kg).label("co2"),
            )
            .join(User, User.id == RouteAnalytics.delivery_partner_id)
            .where(
                and_(
                    RouteAnalytics.analytics_date >= start_date,
                    RouteAnalytics.analytics_date <= end_date,
                    RouteAnalytics.period_type == "daily",
                    RouteAnalytics.delivery_partner_id.isnot(None),
                )
            )
            .group_by(RouteAnalytics.delivery_partner_id, User.full_name)
            .order_by(func.sum(RouteAnalytics.completed_deliveries).desc())
        )
        result = await db.execute(query)
        rows = result.all()

        partners: List[PartnerPerformance] = []
        for r in rows:
            total = r.total or 0
            completed = r.completed or 0
            partners.append(
                PartnerPerformance(
                    delivery_partner_id=r.delivery_partner_id,
                    partner_name=r.full_name,
                    total_deliveries=total,
                    completed_deliveries=completed,
                    completion_rate_pct=round(completed / total * 100, 1) if total else 0.0,
                    total_distance_km=round(r.distance or 0, 2),
                    avg_delivery_time_minutes=round(r.avg_time, 1) if r.avg_time else None,
                    fuel_consumed_litres=round(r.fuel or 0, 2),
                    co2_emitted_kg=round(r.co2 or 0, 2),
                )
            )
        return partners

    # ── Aggregate (called after each route completion) ─────────────────────────

    async def aggregate_daily(
        self, db: AsyncSession, for_date: date, partner_id: Optional[UUID] = None
    ) -> None:
        """
        Compute and upsert daily RouteAnalytics row for the given date/partner.
        Called by background task after each assignment completes.
        """
        query = select(
            func.count(RouteHistory.id).label("routes"),
            func.sum(RouteHistory.total_distance_km).label("distance"),
            func.sum(RouteHistory.total_travel_time_minutes).label("travel_time"),
            func.sum(RouteHistory.fuel_consumed_litres).label("fuel"),
            func.sum(RouteHistory.fuel_saved_litres).label("fuel_saved"),
            func.sum(RouteHistory.co2_emitted_kg).label("co2"),
            func.sum(RouteHistory.co2_saved_kg).label("co2_saved"),
            func.sum(RouteHistory.deliveries_completed).label("completed"),
            func.sum(RouteHistory.deliveries_failed).label("failed"),
            func.avg(RouteHistory.route_efficiency_pct).label("efficiency"),
        ).where(RouteHistory.route_date == for_date)

        if partner_id:
            query = query.where(RouteHistory.delivery_partner_id == partner_id)

        result = await db.execute(query)
        row = result.one()

        total = (row.completed or 0) + (row.failed or 0)
        avg_time = (
            round((row.travel_time or 0) / max(row.routes, 1), 1)
            if row.routes else None
        )
        completion_rate = round((row.completed or 0) / total * 100, 1) if total else 0.0

        # Upsert
        existing = await db.execute(
            select(RouteAnalytics).where(
                and_(
                    RouteAnalytics.analytics_date == for_date,
                    RouteAnalytics.delivery_partner_id == partner_id,
                    RouteAnalytics.period_type == "daily",
                )
            )
        )
        analytic = existing.scalar_one_or_none()
        if not analytic:
            analytic = RouteAnalytics(
                analytics_date=for_date,
                delivery_partner_id=partner_id,
                period_type="daily",
            )
            db.add(analytic)

        analytic.total_deliveries = total
        analytic.completed_deliveries = row.completed or 0
        analytic.failed_deliveries = row.failed or 0
        analytic.completion_rate_pct = completion_rate
        analytic.total_distance_km = round(row.distance or 0, 3)
        analytic.fuel_consumed_litres = round(row.fuel or 0, 3)
        analytic.fuel_saved_litres = round(row.fuel_saved or 0, 3)
        analytic.co2_emitted_kg = round(row.co2 or 0, 3)
        analytic.co2_saved_kg = round(row.co2_saved or 0, 3)
        analytic.total_travel_time_minutes = row.travel_time or 0
        analytic.avg_delivery_time_minutes = avg_time
        analytic.route_efficiency_pct = (
            round(row.efficiency, 1) if row.efficiency else None
        )
        analytic.routes_optimised = row.routes or 0
        await db.flush()


analytics_service = AnalyticsService()
