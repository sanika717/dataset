"""
WebSocket routes — thin wrappers around app/services/websocket_service.py.
Auth uses get_current_user_ws (token via ?token= query param, see
app/deps.py) since browsers can't set an Authorization header on a
WebSocket handshake.
"""
from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user_ws
from app.services.websocket_service import run_camera_stream, run_notification_stream

router = APIRouter(tags=["Streams"])


@router.websocket("/api/cameras/{camera_id}/stream")
async def camera_stream(
    websocket: WebSocket,
    camera_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_ws),
):
    await run_camera_stream(websocket, camera_id, db)


@router.websocket("/api/notifications/stream")
async def notification_stream(
    websocket: WebSocket,
    current_user=Depends(get_current_user_ws),
):
    await run_notification_stream(websocket)
