"""
In-memory WebSocket connection tracking.

Single-process only — fine for one uvicorn worker (the default for this
project); if you scale to multiple workers/processes you'd need to move
this to a shared pub/sub (Redis, etc.) instead, since each process would
otherwise only see its own connections.
"""
import asyncio
import json
import logging
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger("sitesafe.websocket")


class NotificationConnectionManager:
    """Broadcasts new/updated/deleted notifications to every connected client."""

    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, payload: dict):
        message = json.dumps(payload, default=str)
        dead = []
        async with self._lock:
            connections = list(self._connections)
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)


class CameraStreamManager:
    """
    Tracks which cameras currently have at least one viewer, so
    detection_service.py can skip running inference on cameras nobody is
    watching. Each viewer gets its own outgoing queue; frames are pushed
    to every viewer of a given camera_id.
    """

    def __init__(self):
        self._viewers: Dict[int, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def add_viewer(self, camera_id: int, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._viewers.setdefault(camera_id, set()).add(websocket)

    async def remove_viewer(self, camera_id: int, websocket: WebSocket):
        async with self._lock:
            viewers = self._viewers.get(camera_id)
            if viewers:
                viewers.discard(websocket)
                if not viewers:
                    self._viewers.pop(camera_id, None)

    def has_viewers(self, camera_id: int) -> bool:
        return bool(self._viewers.get(camera_id))

    async def send_frame(self, camera_id: int, payload: dict):
        async with self._lock:
            viewers = list(self._viewers.get(camera_id, []))
        if not viewers:
            return
        message = json.dumps(payload, default=str)
        dead = []
        for ws in viewers:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._viewers.get(camera_id, set()).discard(ws)


# Module-level singletons — imported by both the WebSocket routes and
# detection_service.py, so a detected incident can push straight out to
# whoever's connected without going through HTTP.
notification_manager = NotificationConnectionManager()
camera_stream_manager = CameraStreamManager()
