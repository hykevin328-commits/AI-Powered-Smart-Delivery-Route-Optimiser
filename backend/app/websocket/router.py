"""
WebSocket routes for live delivery tracking and route updates.

Endpoints:
  WS  /ws/partner/{partner_id}  – delivery partner live channel
  WS  /ws/admin                 – admin broadcast channel
  WS  /ws/order/{order_id}      – per-order tracking (for customers)

  GET /ws/stats                 – connection statistics (Admin REST endpoint)

Authentication:
  Clients send their JWT access token as a query parameter:
  ws://host/ws/partner/{id}?token=<access_token>

Message protocol (JSON):
  Client → Server:
    {"event": "ping"}
    {"event": "location_update", "payload": {"lat": 12.9, "lon": 77.6, ...}}
    {"event": "subscribe_order", "payload": {"order_id": "..."}}

  Server → Client:
    {"event": "pong"}
    {"event": "route_update", "payload": {...}}
    {"event": "order_status_changed", "payload": {...}}
    {"event": "error", "payload": {"message": "..."}}
"""
from __future__ import annotations

import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import decode_token
from app.config.database import get_db
from app.config.logging import get_logger
from app.models.user import UserRole
from app.schemas.websocket import WSEventType
from app.utils.dependencies import require_admin
from app.utils.exceptions import InvalidTokenException, UnauthorizedException
from app.websocket.connection_manager import ws_manager

logger = get_logger(__name__)

router = APIRouter(tags=["WebSocket"])


# ── JWT helper for WebSocket (query param auth) ────────────────────────────────

def _authenticate_ws(token: Optional[str]) -> dict:
    """Validate JWT token from WebSocket query param. Returns decoded payload."""
    if not token:
        raise UnauthorizedException("WebSocket authentication token required")
    return decode_token(token)


# ── Delivery Partner Channel ──────────────────────────────────────────────────

@router.websocket("/ws/partner/{partner_id}")
async def partner_websocket(
    websocket: WebSocket,
    partner_id: UUID,
    token: Optional[str] = Query(None),
):
    """
    Live channel for a delivery partner.
    - Receives location updates pushed from the client.
    - Receives route recalculation events from the server.
    - Receives new order assignment events.
    """
    try:
        payload = _authenticate_ws(token)
        token_user_id = payload.get("sub")
        token_role = payload.get("role")

        # Partners can only connect to their own channel; admins can observe any
        if token_role != UserRole.ADMIN.value and token_user_id != str(partner_id):
            await websocket.close(code=4003, reason="Forbidden")
            return
    except (UnauthorizedException, InvalidTokenException) as exc:
        await websocket.close(code=4001, reason=str(exc.detail))
        return

    room = f"partner:{partner_id}"
    await ws_manager.connect(websocket, room)
    logger.info("partner_ws_open", partner_id=str(partner_id))

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "event": WSEventType.ERROR,
                    "payload": {"message": "Invalid JSON"},
                }))
                continue

            event = msg.get("event")

            if event == WSEventType.PING:
                await websocket.send_text(json.dumps({"event": WSEventType.PONG}))

            elif event == "location_update":
                # Broadcast partner location to admin channel
                await ws_manager.send_to_admins(
                    WSEventType.PARTNER_LOCATION,
                    {"delivery_partner_id": str(partner_id), **msg.get("payload", {})},
                )

            elif event == "subscribe_order":
                # Join order-specific room for tracking
                order_id = msg.get("payload", {}).get("order_id")
                if order_id:
                    await ws_manager.connect(websocket, f"order:{order_id}")
                    await websocket.send_text(json.dumps({
                        "event": "subscribed",
                        "payload": {"order_id": order_id},
                    }))
            else:
                await websocket.send_text(json.dumps({
                    "event": WSEventType.ERROR,
                    "payload": {"message": f"Unknown event: {event}"},
                }))

    except WebSocketDisconnect:
        logger.info("partner_ws_close", partner_id=str(partner_id))
    finally:
        await ws_manager.disconnect(websocket, room)


# ── Admin Broadcast Channel ───────────────────────────────────────────────────

@router.websocket("/ws/admin")
async def admin_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    Admin-only channel. Receives all partner location updates and system events.
    """
    try:
        payload = _authenticate_ws(token)
        if payload.get("role") != UserRole.ADMIN.value:
            await websocket.close(code=4003, reason="Admin access required")
            return
    except (UnauthorizedException, InvalidTokenException) as exc:
        await websocket.close(code=4001, reason=str(exc.detail))
        return

    room = "admin"
    await ws_manager.connect(websocket, room)
    logger.info("admin_ws_open")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if msg.get("event") == WSEventType.PING:
                await websocket.send_text(json.dumps({"event": WSEventType.PONG}))

    except WebSocketDisconnect:
        logger.info("admin_ws_close")
    finally:
        await ws_manager.disconnect(websocket, room)


# ── Order Tracking Channel ─────────────────────────────────────────────────────

@router.websocket("/ws/order/{order_id}")
async def order_websocket(
    websocket: WebSocket,
    order_id: UUID,
    token: Optional[str] = Query(None),
):
    """
    Public order-tracking channel.
    Clients (e.g. customers) subscribe to receive status change events for an order.
    Requires a valid JWT but no role restriction.
    """
    try:
        _authenticate_ws(token)
    except (UnauthorizedException, InvalidTokenException) as exc:
        await websocket.close(code=4001, reason=str(exc.detail))
        return

    room = f"order:{order_id}"
    await ws_manager.connect(websocket, room)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if msg.get("event") == WSEventType.PING:
                await websocket.send_text(json.dumps({"event": WSEventType.PONG}))

    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket, room)


# ── REST: Connection stats (Admin) ────────────────────────────────────────────

@router.get("/ws/stats", summary="WebSocket connection statistics (Admin)")
async def ws_stats(admin=Depends(require_admin)):
    from app.utils.response import success_response
    return success_response(data={
        "total_connections": ws_manager.total_connections,
        "admin_connections": ws_manager.room_count("admin"),
    })
