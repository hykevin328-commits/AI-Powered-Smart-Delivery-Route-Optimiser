"""
Traffic Integration Service

Fetches live traffic data from Google Maps Routes API or OpenRouteService,
caches results in PostgreSQL (TrafficCache table) and Redis with a TTL,
and returns traffic-adjusted distance/duration matrices.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.redis_client import cache_get, cache_set
from app.config.settings import settings
from app.models.traffic_cache import TrafficCache
from app.schemas.traffic import TrafficRequest, TrafficResponse, TrafficSegment
from app.schemas.common import CoordinateSchema
from app.utils.exceptions import ExternalAPIException
from app.utils.helpers import haversine_distance, utcnow

_HTTP_TIMEOUT = 10


def _cache_key(olat: float, olon: float, dlat: float, dlon: float) -> str:
    return f"traffic:{olat:.4f},{olon:.4f}->{dlat:.4f},{dlon:.4f}"


class TrafficService:

    # ── Public: fetch segment ─────────────────────────────────────────────────

    async def get_traffic(
        self, db: AsyncSession, request: TrafficRequest
    ) -> TrafficResponse:
        key = _cache_key(
            request.origin_latitude, request.origin_longitude,
            request.destination_latitude, request.destination_longitude,
        )

        # 1. Redis cache
        cached = await cache_get(key)
        if cached:
            return TrafficResponse(**cached, cached=True)

        # 2. DB cache
        db_cache = await self._get_db_cache(db, key)
        if db_cache:
            result = self._db_to_response(db_cache, cached=True)
            await cache_set(key, result.model_dump(mode="json"), ttl=settings.TRAFFIC_CACHE_TTL)
            return result

        # 3. Fetch live
        if settings.GOOGLE_MAPS_API_KEY:
            segment = await self._fetch_google(request)
            provider = "google"
        elif settings.OPENROUTESERVICE_API_KEY:
            segment = await self._fetch_ors(request)
            provider = "openrouteservice"
        else:
            segment = self._haversine_fallback(request)
            provider = "haversine"

        response = TrafficResponse(
            origin=CoordinateSchema(
                latitude=request.origin_latitude, longitude=request.origin_longitude
            ),
            destination=CoordinateSchema(
                latitude=request.destination_latitude, longitude=request.destination_longitude
            ),
            segment=segment,
            provider=provider,
            cached=False,
            fetched_at=utcnow(),
        )

        # Persist to DB + Redis
        await self._save_db_cache(db, key, request, segment, provider)
        await cache_set(key, response.model_dump(mode="json"), ttl=settings.TRAFFIC_CACHE_TTL)
        return response

    # ── Public: build traffic-aware distance matrix ───────────────────────────

    async def build_traffic_matrix(
        self,
        db: AsyncSession,
        coordinates: List[Tuple[float, float]],
    ) -> Tuple[List[List[float]], List[List[float]], float]:
        """
        Return (distance_km_matrix, traffic_duration_matrix, avg_traffic_factor).
        Falls back to Haversine if no API keys are configured.
        """
        n = len(coordinates)
        dist_matrix = [[0.0] * n for _ in range(n)]
        dur_matrix = [[0.0] * n for _ in range(n)]
        factors: List[float] = []

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                req = TrafficRequest(
                    origin_latitude=coordinates[i][0],
                    origin_longitude=coordinates[i][1],
                    destination_latitude=coordinates[j][0],
                    destination_longitude=coordinates[j][1],
                )
                seg = (await self.get_traffic(db, req)).segment
                dist_matrix[i][j] = seg.distance_km
                dur_matrix[i][j] = seg.duration_in_traffic_minutes
                factors.append(seg.traffic_factor)

        avg_factor = sum(factors) / len(factors) if factors else 1.0
        return dist_matrix, dur_matrix, round(avg_factor, 3)

    # ── Google Maps Routes API ─────────────────────────────────────────────────

    async def _fetch_google(self, req: TrafficRequest) -> TrafficSegment:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": f"{req.origin_latitude},{req.origin_longitude}",
            "destinations": f"{req.destination_latitude},{req.destination_longitude}",
            "departure_time": "now",
            "traffic_model": "best_guess",
            "key": settings.GOOGLE_MAPS_API_KEY,
        }
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.get(url, params=params)

        data = resp.json()
        if data.get("status") != "OK":
            raise ExternalAPIException("Google Maps", f"Status: {data.get('status')}")

        element = data["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            return self._haversine_fallback(req)

        dist_km = element["distance"]["value"] / 1000
        free_flow_min = element["duration"]["value"] / 60
        traffic_min = element.get("duration_in_traffic", {}).get("value", element["duration"]["value"]) / 60
        factor = round(traffic_min / free_flow_min, 3) if free_flow_min > 0 else 1.0

        congestion = "low"
        if factor > 1.5:
            congestion = "severe"
        elif factor > 1.3:
            congestion = "high"
        elif factor > 1.15:
            congestion = "medium"

        return TrafficSegment(
            distance_km=round(dist_km, 3),
            duration_minutes=round(free_flow_min, 1),
            duration_in_traffic_minutes=round(traffic_min, 1),
            congestion_level=congestion,
            traffic_factor=factor,
        )

    # ── OpenRouteService ──────────────────────────────────────────────────────

    async def _fetch_ors(self, req: TrafficRequest) -> TrafficSegment:
        url = "https://api.openrouteservice.org/v2/directions/driving-car"
        body = {
            "coordinates": [
                [req.origin_longitude, req.origin_latitude],
                [req.destination_longitude, req.destination_latitude],
            ]
        }
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(
                url,
                json=body,
                headers={
                    "Authorization": settings.OPENROUTESERVICE_API_KEY,
                    "Content-Type": "application/json",
                },
            )

        if resp.status_code != 200:
            return self._haversine_fallback(req)

        data = resp.json()
        summary = data["routes"][0]["summary"]
        dist_km = summary["distance"] / 1000
        duration_min = summary["duration"] / 60

        return TrafficSegment(
            distance_km=round(dist_km, 3),
            duration_minutes=round(duration_min, 1),
            duration_in_traffic_minutes=round(duration_min, 1),
            congestion_level="low",
            traffic_factor=1.0,
        )

    # ── Haversine fallback ─────────────────────────────────────────────────────

    @staticmethod
    def _haversine_fallback(req: TrafficRequest) -> TrafficSegment:
        dist = haversine_distance(
            req.origin_latitude, req.origin_longitude,
            req.destination_latitude, req.destination_longitude,
        )
        duration = (dist / 40.0) * 60  # 40 km/h avg
        return TrafficSegment(
            distance_km=round(dist, 3),
            duration_minutes=round(duration, 1),
            duration_in_traffic_minutes=round(duration, 1),
            congestion_level="low",
            traffic_factor=1.0,
        )

    # ── DB cache helpers ───────────────────────────────────────────────────────

    async def _get_db_cache(
        self, db: AsyncSession, key: str
    ) -> Optional[TrafficCache]:
        result = await db.execute(
            select(TrafficCache).where(
                TrafficCache.cache_key == key,
                TrafficCache.expires_at > utcnow(),
            )
        )
        return result.scalar_one_or_none()

    async def _save_db_cache(
        self,
        db: AsyncSession,
        key: str,
        req: TrafficRequest,
        seg: TrafficSegment,
        provider: str,
    ) -> None:
        # Upsert: delete old, insert fresh
        old = await db.execute(
            select(TrafficCache).where(TrafficCache.cache_key == key)
        )
        old_row = old.scalar_one_or_none()
        if old_row:
            await db.delete(old_row)

        entry = TrafficCache(
            cache_key=key,
            provider=provider,
            origin_lat=req.origin_latitude,
            origin_lon=req.origin_longitude,
            dest_lat=req.destination_latitude,
            dest_lon=req.destination_longitude,
            distance_km=seg.distance_km,
            duration_minutes=seg.duration_minutes,
            duration_in_traffic_minutes=seg.duration_in_traffic_minutes,
            congestion_level=seg.congestion_level,
            traffic_factor=seg.traffic_factor,
            expires_at=utcnow() + timedelta(seconds=settings.TRAFFIC_CACHE_TTL),
        )
        db.add(entry)
        await db.flush()

    @staticmethod
    def _db_to_response(row: TrafficCache, cached: bool) -> TrafficResponse:
        return TrafficResponse(
            origin=CoordinateSchema(latitude=row.origin_lat, longitude=row.origin_lon),
            destination=CoordinateSchema(latitude=row.dest_lat, longitude=row.dest_lon),
            segment=TrafficSegment(
                distance_km=row.distance_km,
                duration_minutes=row.duration_minutes,
                duration_in_traffic_minutes=row.duration_in_traffic_minutes or row.duration_minutes,
                congestion_level=row.congestion_level or "low",
                traffic_factor=row.traffic_factor,
            ),
            provider=row.provider,
            cached=cached,
            fetched_at=row.created_at,
        )


traffic_service = TrafficService()
