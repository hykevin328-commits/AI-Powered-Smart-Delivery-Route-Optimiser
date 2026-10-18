"""
Traffic API

POST /traffic/segment    – get live traffic for an origin → destination pair
POST /traffic/matrix     – build a full traffic-aware N×N distance matrix
GET  /traffic/cache      – view cached traffic entries (Admin)
DELETE /traffic/cache    – purge expired cache entries (Admin)
"""
from __future__ import annotations

from typing import List, Tuple

from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.traffic_cache import TrafficCache
from app.models.user import User
from app.schemas.common import CoordinateSchema
from app.schemas.traffic import (
    TrafficAwareDistanceMatrix,
    TrafficRequest,
    TrafficResponse,
)
from app.services.traffic_service import traffic_service
from app.utils.dependencies import require_admin, require_delivery_partner
from app.utils.helpers import utcnow
from app.utils.response import success_response

router = APIRouter(prefix="/traffic", tags=["Traffic Integration"])


@router.post("/segment", summary="Get live traffic data for a route segment")
async def get_traffic_segment(
    request: TrafficRequest,
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    result = await traffic_service.get_traffic(db, request)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/matrix", summary="Build traffic-aware distance matrix for multiple locations")
async def get_traffic_matrix(
    locations: List[CoordinateSchema],
    current_user: User = Depends(require_delivery_partner),
    db: AsyncSession = Depends(get_db),
):
    if len(locations) < 2:
        from app.utils.exceptions import ValidationException
        raise ValidationException("At least 2 locations are required")
    if len(locations) > 20:
        from app.utils.exceptions import ValidationException
        raise ValidationException("Maximum 20 locations per matrix request")

    coords = [(loc.latitude, loc.longitude) for loc in locations]
    dist_matrix, dur_matrix, avg_factor = await traffic_service.build_traffic_matrix(
        db, coords
    )

    result = TrafficAwareDistanceMatrix(
        locations=locations,
        distance_matrix_km=dist_matrix,
        duration_matrix_minutes=dur_matrix,
        traffic_duration_matrix_minutes=dur_matrix,
        overall_traffic_factor=avg_factor,
    )
    return success_response(data=result.model_dump())


@router.get("/cache", summary="View traffic cache entries (Admin)")
async def get_traffic_cache(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    result = await db.execute(
        select(TrafficCache)
        .where(TrafficCache.expires_at > utcnow())
        .order_by(TrafficCache.created_at.desc())
        .limit(100)
    )
    rows = result.scalars().all()
    return success_response(
        data=[
            {
                "key": r.cache_key,
                "provider": r.provider,
                "traffic_factor": r.traffic_factor,
                "congestion_level": r.congestion_level,
                "expires_at": r.expires_at.isoformat(),
            }
            for r in rows
        ],
        message=f"{len(rows)} active cache entries",
    )


@router.delete("/cache", summary="Purge expired traffic cache entries (Admin)")
async def purge_traffic_cache(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        delete(TrafficCache).where(TrafficCache.expires_at <= utcnow())
    )
    await db.flush()
    return success_response(message=f"Purged {result.rowcount} expired cache entries")
