"""
Backs the two WebSocket routes (see app/routers/streams.py):

  - /api/cameras/{id}/stream        -> run_camera_stream()
  - /api/notifications/stream       -> run_notification_stream()

Wire contract matches what the frontend already assumes (documented in
streamService.js / notificationStreamService.js): JSON text frames, image
as a base64 data URL, detections as normalized [x, y, w, h] boxes.
"""
import asyncio
import base64
import logging
import time
from pathlib import Path
from typing import Optional

import cv2
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app import crud, schemas
from app.services.connection_manager import camera_stream_manager, notification_manager
from app.services.detection_service import DetectionService

logger = logging.getLogger("sitesafe.websocket_service")

TARGET_FPS = 8
FRAME_INTERVAL_S = 1 / TARGET_FPS
# Don't create a duplicate incident for the same camera+type more often
# than this — a violation that persists across many frames would
# otherwise flood the incidents table.
INCIDENT_COOLDOWN_S = 30


def _resolve_frame_source(feed_url: Optional[str]) -> str:
    """
    Picks what cv2.VideoCapture should open: the camera's configured
    feed_url if set, otherwise a bundled test clip if one exists,
    otherwise the local webcam (index 0) as a last resort for local dev.
    """
    if feed_url:
        return feed_url

    backend_root = Path(__file__).resolve().parents[2]
    for candidate in (
        backend_root / "test_videos" / "ppe.mp4",
        backend_root / "test_videos" / "demo.mp4",
    ):
        if candidate.exists():
            return str(candidate)

    return "0"  # cv2.VideoCapture accepts "0" as a stringified device index


def _encode_frame(frame) -> str:
    ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
    if not ok:
        raise RuntimeError("Failed to JPEG-encode frame")
    b64 = base64.b64encode(buffer).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


async def run_camera_stream(websocket: WebSocket, camera_id: int, db: Session):
    """
    One coroutine per connected viewer. Each viewer runs its own capture +
    detection loop — fine for the small number of concurrent viewers a
    site-safety dashboard actually has; if you need many simultaneous
    viewers of the same camera, share one capture/detection loop across
    viewers via camera_stream_manager instead of duplicating inference.
    """
    camera = crud.get_camera(db, camera_id)
    if camera is None:
        await websocket.close(code=4404)
        return

    await camera_stream_manager.add_viewer(camera_id, websocket)

    source = _resolve_frame_source(camera.feed_url)
    cap = cv2.VideoCapture(int(source) if source.isdigit() else source)
    if not cap.isOpened():
        try:
            await websocket.send_json(
                {"type": "error", "message": f"Could not open video source: {source}"}
            )
        finally:
            await camera_stream_manager.remove_viewer(camera_id, websocket)
            await websocket.close(code=4500)
        return

    detection_service = DetectionService(camera_id)
    last_incident_at: dict[str, float] = {}

    try:
        while True:
            loop_start = time.monotonic()

            ok, frame = await asyncio.to_thread(cap.read)
            if not ok:
                # Loop test clips instead of ending the stream.
                await asyncio.to_thread(cap.set, cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = await asyncio.to_thread(cap.read)
                if not ok:
                    break

            result = await asyncio.to_thread(detection_service.process_frame, frame)

            await websocket.send_json(
                {
                    "type": "frame",
                    "image": await asyncio.to_thread(_encode_frame, result["annotated_frame"]),
                    "detections": result["detections"],
                }
            )

            payloads = detection_service.build_incident_payloads(frame, result)
            for payload in payloads:
                now = time.monotonic()
                key = payload["type"]
                if now - last_incident_at.get(key, 0) < INCIDENT_COOLDOWN_S:
                    continue
                last_incident_at[key] = now
                await _create_incident_and_notify(db, payload)

            elapsed = time.monotonic() - loop_start
            await asyncio.sleep(max(0.0, FRAME_INTERVAL_S - elapsed))

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Camera stream loop crashed for camera %s", camera_id)
    finally:
        cap.release()
        await camera_stream_manager.remove_viewer(camera_id, websocket)


async def _create_incident_and_notify(db: Session, payload: dict):
    """Writes the Incident row, a matching Notification, and broadcasts both."""
    incident = crud.create_incident(db, schemas.IncidentCreate(**payload))

    notification = crud.create_notification(
        db,
        schemas.NotificationCreate(
            incident_id=incident.id,
            title=incident.title or incident.type,
            message=f"Detected on camera #{incident.camera_id}"
            if incident.camera_id
            else "Detected",
            severity=incident.severity,
        ),
    )

    await notification_manager.broadcast(
        {
            "type": "notification",
            "notification": schemas.NotificationOut.model_validate(notification).model_dump(
                mode="json"
            ),
        }
    )


async def run_notification_stream(websocket: WebSocket):
    """
    Receive-only from the client's point of view — just registers this
    connection so _create_incident_and_notify()'s broadcasts reach it,
    and keeps the socket alive with a periodic ping until it disconnects.
    """
    await notification_manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Notification stream connection dropped unexpectedly")
    finally:
        await notification_manager.disconnect(websocket)
