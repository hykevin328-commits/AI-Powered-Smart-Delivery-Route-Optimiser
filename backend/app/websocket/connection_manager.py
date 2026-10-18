"""
WebSocket Connection Manager

Maintains a registry of active WebSocket connections, grouped by:
  - room: a string key such as "partner:{uuid}" or "admin"
  - global broadcast

Thread-safe for a single-process deployment.
For multi-process/multi-worker deployments, replace the in-memory dict
with a Redis pub/sub backend (stub included at bottom).
"""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Optional, Set
from uuid import UUID

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from app.config.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages WebSocket lifecycle and message routing.

    Rooms:
      - "admin"               – all admin subscribers
      - "partner:{uuid}"      – per-delivery-partner channel
      - "order:{uuid}"        – order tracking subscribers (customers)
    """

    def __init__(self) -> None:
        # room → set of WebSocket connections
        self._rooms: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    # ── Connection lifecycle ──────────────────────────────────────────────────

    async def connect(self, websocket: WebSocket, room: str) -> None:
        await websocket.accept()
        async with self._lock:
            self._rooms[room].add(websocket)
        logger.info("ws_connected", room=room, total=len(self._rooms[room]))

    async def disconnect(self, websocket: WebSocket, room: str) -> None:
        async with self._lock:
            self._rooms[room].discard(websocket)
            if not self._rooms[room]:
                del self._rooms[room]
        logger.info("ws_disconnected", room=room)

    # ── Messaging ─────────────────────────────────────────────────────────────

    async def send_to_room(self, room: str, event: str, payload: Any = None) -> int:
        """Broadcast a JSON message to all connections in a room. Returns delivery count."""
        message = json.dumps({
            "event": event,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        })
        connections = list(self._rooms.get(room, set()))
        delivered = 0
        dead: list[WebSocket] = []

        for ws in connections:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_text(message)
                    delivered += 1
                else:
                    dead.append(ws)
            except Exception as exc:
                logger.warning("ws_send_error", room=room, error=str(exc))
                dead.append(ws)

        # Clean up stale connections
        if dead:
            async with self._lock:
                for ws in dead:
                    self._rooms[room].discard(ws)

        return delivered

    async def send_to_partner(self, partner_id: UUID, event: str, payload: Any = None) -> int:
        return await self.send_to_room(f"partner:{partner_id}", event, payload)

    async def send_to_admins(self, event: str, payload: Any = None) -> int:
        return await self.send_to_room("admin", event, payload)

    async def broadcast(self, event: str, payload: Any = None) -> int:
        """Send to every connected client across all rooms."""
        rooms = list(self._rooms.keys())
        total = 0
        for room in rooms:
            total += await self.send_to_room(room, event, payload)
        return total

    # ── Stats ─────────────────────────────────────────────────────────────────

    @property
    def total_connections(self) -> int:
        return sum(len(v) for v in self._rooms.values())

    def room_count(self, room: str) -> int:
        return len(self._rooms.get(room, set()))


# Module-level singleton
ws_manager = ConnectionManager()
