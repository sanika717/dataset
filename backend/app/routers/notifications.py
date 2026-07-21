from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("", response_model=list[schemas.NotificationOut])
def list_notifications(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return crud.get_notifications(db, skip=skip, limit=limit, unread_only=unread_only)


# Static path — must come before /{notification_id}/read so it can't be
# shadowed by a parameterized match.
@router.get("/unread-count", response_model=schemas.UnreadCountOut)
def unread_count(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return {"count": crud.get_unread_notification_count(db)}


@router.put("/read-all", response_model=schemas.MarkAllReadOut)
def mark_all_read(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return {"updated": crud.mark_all_notifications_read(db)}


@router.put("/{notification_id}/read", response_model=schemas.NotificationOut)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notification = crud.mark_notification_read(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.delete("/{notification_id}", status_code=204)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not crud.delete_notification(db, notification_id):
        raise HTTPException(status_code=404, detail="Notification not found")
