"""
Shared FastAPI dependencies: DB session (re-exported from app.database)
and current-user resolution.

Two flavors of "get current user" because browsers can't set custom
headers on a WebSocket handshake — REST routes authenticate via the
Authorization header, WebSocket routes via a `?token=` query param (see
streamService.js / notificationStreamService.js on the frontend, which
both document this same constraint).
"""
from fastapi import Depends, HTTPException, Query, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db  # noqa: F401 - re-exported for router imports
from app.models import User
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    user = crud.get_user(db, int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    return user


async def get_current_user_ws(
    websocket: WebSocket,
    db: Session = Depends(get_db),
    token: str = Query(default=None),
) -> User:
    """
    Same validation as get_current_user, but for WebSocket routes:
    reads the JWT from ?token= instead of an Authorization header, and
    closes the socket with code 4401 (matches the contract documented in
    streamService.js / notificationStreamService.js) on failure instead
    of raising an HTTPException.
    """
    user_id = decode_access_token(token) if token else None
    user = crud.get_user(db, int(user_id)) if user_id else None
    if user is None or not user.is_active:
        await websocket.close(code=4401)
        raise HTTPException(status_code=401, detail="Not authorized for this stream")
    return user
