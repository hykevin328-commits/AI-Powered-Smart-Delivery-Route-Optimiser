"""
Geocoding service – forward and reverse geocoding.

Provider priority (configured via GEOCODING_PROVIDER env var):
  google           → Google Maps Geocoding API
  openrouteservice → ORS Geocoding (Pelias)
  nominatim        → OpenStreetMap Nominatim (free, no key required)

Falls back to Nominatim if the configured provider is unavailable.
"""
from __future__ import annotations

import asyncio
from typing import Optional, Tuple

import httpx
from geopy.geocoders import GoogleV3, Nominatim
from geopy.adapters import AioHTTPAdapter

from app.config.settings import settings
from app.schemas.geocoding import (
    GeocodeRequest,
    GeocodeResponse,
    ReverseGeocodeRequest,
    ReverseGeocodeResponse,
)
from app.utils.exceptions import GeocodingException

_USER_AGENT = "SmartDeliveryRouteOptimizer/1.0"
_TIMEOUT = 10  # seconds


class GeocodingService:

    # ── Forward geocoding ─────────────────────────────────────────────────────

    async def geocode(self, request: GeocodeRequest) -> GeocodeResponse:
        """Convert an address string to lat/lon coordinates."""
        full_address = request.address
        if request.city:
            full_address += f", {request.city}"
        if request.country:
            full_address += f", {request.country}"

        provider = settings.GEOCODING_PROVIDER
        try:
            if provider == "google" and settings.GOOGLE_MAPS_API_KEY:
                return await self._geocode_google(full_address, request.address)
            elif provider == "openrouteservice" and settings.OPENROUTESERVICE_API_KEY:
                return await self._geocode_ors(full_address, request.address)
            else:
                return await self._geocode_nominatim(full_address, request.address)
        except GeocodingException:
            raise
        except Exception as exc:
            raise GeocodingException(f"Geocoding failed: {exc}") from exc

    # ── Reverse geocoding ─────────────────────────────────────────────────────

    async def reverse_geocode(self, request: ReverseGeocodeRequest) -> ReverseGeocodeResponse:
        """Convert lat/lon to a human-readable address."""
        provider = settings.GEOCODING_PROVIDER
        try:
            if provider == "google" and settings.GOOGLE_MAPS_API_KEY:
                return await self._reverse_google(request.latitude, request.longitude)
            else:
                return await self._reverse_nominatim(request.latitude, request.longitude)
        except GeocodingException:
            raise
        except Exception as exc:
            raise GeocodingException(f"Reverse geocoding failed: {exc}") from exc

    # ── Google Maps ───────────────────────────────────────────────────────────

    async def _geocode_google(self, full_address: str, raw_address: str) -> GeocodeResponse:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, params={
                "address": full_address,
                "key": settings.GOOGLE_MAPS_API_KEY,
            })
            data = resp.json()

        if data.get("status") != "OK" or not data.get("results"):
            raise GeocodingException(f"Google Geocoding returned status: {data.get('status')}")

        result = data["results"][0]
        loc = result["geometry"]["location"]
        return GeocodeResponse(
            address=raw_address,
            formatted_address=result["formatted_address"],
            latitude=loc["lat"],
            longitude=loc["lng"],
            confidence=1.0 if result["geometry"]["location_type"] == "ROOFTOP" else 0.8,
            provider="google",
        )

    async def _reverse_google(self, lat: float, lon: float) -> ReverseGeocodeResponse:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, params={
                "latlng": f"{lat},{lon}",
                "key": settings.GOOGLE_MAPS_API_KEY,
            })
            data = resp.json()

        if data.get("status") != "OK" or not data.get("results"):
            raise GeocodingException("Google reverse geocoding failed")

        result = data["results"][0]
        components = {c["types"][0]: c["long_name"] for c in result.get("address_components", [])}
        return ReverseGeocodeResponse(
            formatted_address=result["formatted_address"],
            city=components.get("locality") or components.get("administrative_area_level_2"),
            state=components.get("administrative_area_level_1"),
            postal_code=components.get("postal_code"),
            country=components.get("country"),
            latitude=lat,
            longitude=lon,
        )

    # ── OpenRouteService ──────────────────────────────────────────────────────

    async def _geocode_ors(self, full_address: str, raw_address: str) -> GeocodeResponse:
        url = "https://api.openrouteservice.org/geocode/search"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, params={
                "api_key": settings.OPENROUTESERVICE_API_KEY,
                "text": full_address,
                "size": 1,
            })
            data = resp.json()

        features = data.get("features", [])
        if not features:
            raise GeocodingException("OpenRouteService geocoding returned no results")

        feat = features[0]
        coords = feat["geometry"]["coordinates"]
        props = feat.get("properties", {})
        return GeocodeResponse(
            address=raw_address,
            formatted_address=props.get("label", full_address),
            latitude=coords[1],
            longitude=coords[0],
            confidence=props.get("confidence", 0.7),
            provider="openrouteservice",
        )

    # ── Nominatim (free fallback) ─────────────────────────────────────────────

    async def _geocode_nominatim(self, full_address: str, raw_address: str) -> GeocodeResponse:
        url = "https://nominatim.openstreetmap.org/search"
        async with httpx.AsyncClient(
            timeout=_TIMEOUT,
            headers={"User-Agent": _USER_AGENT},
        ) as client:
            resp = await client.get(url, params={
                "q": full_address,
                "format": "json",
                "limit": 1,
                "addressdetails": 1,
            })
            data = resp.json()

        if not data:
            raise GeocodingException(f"Address not found: {full_address}")

        item = data[0]
        return GeocodeResponse(
            address=raw_address,
            formatted_address=item.get("display_name", full_address),
            latitude=float(item["lat"]),
            longitude=float(item["lon"]),
            confidence=float(item.get("importance", 0.5)),
            provider="nominatim",
        )

    async def _reverse_nominatim(self, lat: float, lon: float) -> ReverseGeocodeResponse:
        url = "https://nominatim.openstreetmap.org/reverse"
        async with httpx.AsyncClient(
            timeout=_TIMEOUT,
            headers={"User-Agent": _USER_AGENT},
        ) as client:
            resp = await client.get(url, params={
                "lat": lat,
                "lon": lon,
                "format": "json",
                "addressdetails": 1,
            })
            data = resp.json()

        if "error" in data:
            raise GeocodingException(f"Reverse geocoding failed: {data['error']}")

        addr = data.get("address", {})
        return ReverseGeocodeResponse(
            formatted_address=data.get("display_name", ""),
            city=addr.get("city") or addr.get("town") or addr.get("village"),
            state=addr.get("state"),
            postal_code=addr.get("postcode"),
            country=addr.get("country"),
            latitude=lat,
            longitude=lon,
        )

    # ── Bulk geocode ──────────────────────────────────────────────────────────

    async def bulk_geocode(
        self, addresses: list[str]
    ) -> list[Optional[Tuple[float, float]]]:
        """
        Geocode multiple addresses concurrently.
        Returns a list of (lat, lon) tuples; None for failures.
        """
        async def _safe(addr: str) -> Optional[Tuple[float, float]]:
            try:
                r = await self.geocode(GeocodeRequest(address=addr))
                return (r.latitude, r.longitude)
            except Exception:
                return None

        return await asyncio.gather(*[_safe(a) for a in addresses])


geocoding_service = GeocodingService()
