"""
Database access layer. All routers go through these functions instead of
touching SQLAlchemy models/queries directly - keeps business logic out of
the HTTP layer and easy to unit test. Same convention as the old
Workers/Alerts/Reports schema's crud.py.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.security import hash_password


# ---------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------
def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserRegister) -> models.User:
    db_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hash_password(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ---------------------------------------------------------------------
# Cameras
# ---------------------------------------------------------------------
def get_camera(db: Session, camera_id: int) -> Optional[models.Camera]:
    return db.query(models.Camera).filter(models.Camera.id == camera_id).first()


def get_cameras(db: Session, skip: int = 0, limit: int = 100) -> List[models.Camera]:
    return (
        db.query(models.Camera)
        .order_by(models.Camera.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_camera(db: Session, camera: schemas.CameraCreate) -> models.Camera:
    db_camera = models.Camera(**camera.model_dump())
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    return db_camera


def update_camera(
    db: Session, camera_id: int, camera: schemas.CameraUpdate
) -> Optional[models.Camera]:
    db_camera = get_camera(db, camera_id)
    if not db_camera:
        return None
    for field, value in camera.model_dump(exclude_unset=True).items():
        setattr(db_camera, field, value)
    db.commit()
    db.refresh(db_camera)
    return db_camera


def delete_camera(db: Session, camera_id: int) -> bool:
    db_camera = get_camera(db, camera_id)
    if not db_camera:
        return False
    db.delete(db_camera)
    db.commit()
    return True


# ---------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------
def _incident_out(db_incident: models.Incident) -> models.Incident:
    """Attaches camera_name for IncidentOut without a separate join in every caller."""
    db_incident.camera_name = db_incident.camera.name if db_incident.camera else None
    return db_incident


def get_incident(db: Session, incident_id: int) -> Optional[models.Incident]:
    incident = (
        db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    )
    return _incident_out(incident) if incident else None


def get_incidents(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    camera_id: Optional[int] = None,
) -> List[models.Incident]:
    query = db.query(models.Incident)
    if status:
        query = query.filter(models.Incident.status == status)
    if severity:
        query = query.filter(models.Incident.severity == severity)
    if camera_id:
        query = query.filter(models.Incident.camera_id == camera_id)
    incidents = (
        query.order_by(models.Incident.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_incident_out(i) for i in incidents]


def create_incident(db: Session, incident: schemas.IncidentCreate) -> models.Incident:
    db_incident = models.Incident(**incident.model_dump())
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return _incident_out(db_incident)


def update_incident(
    db: Session, incident_id: int, incident: schemas.IncidentUpdate
) -> Optional[models.Incident]:
    db_incident = (
        db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    )
    if not db_incident:
        return None
    updates = incident.model_dump(exclude_unset=True)
    if updates.get("status") == "resolved" and db_incident.status != "resolved":
        db_incident.resolved_at = datetime.now(timezone.utc)
    for field, value in updates.items():
        setattr(db_incident, field, value)
    db.commit()
    db.refresh(db_incident)
    return _incident_out(db_incident)


def delete_incident(db: Session, incident_id: int) -> bool:
    db_incident = (
        db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    )
    if not db_incident:
        return False
    db.delete(db_incident)
    db.commit()
    return True


# ---------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------
def get_notifications(
    db: Session, skip: int = 0, limit: int = 50, unread_only: bool = False
) -> List[models.Notification]:
    query = db.query(models.Notification)
    if unread_only:
        query = query.filter(models.Notification.read.is_(False))
    return (
        query.order_by(models.Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_unread_notification_count(db: Session) -> int:
    return (
        db.query(func.count(models.Notification.id))
        .filter(models.Notification.read.is_(False))
        .scalar()
        or 0
    )


def create_notification(
    db: Session, notification: schemas.NotificationCreate
) -> models.Notification:
    db_notification = models.Notification(**notification.model_dump())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def mark_notification_read(
    db: Session, notification_id: int
) -> Optional[models.Notification]:
    db_notification = (
        db.query(models.Notification)
        .filter(models.Notification.id == notification_id)
        .first()
    )
    if not db_notification:
        return None
    db_notification.read = True
    db.commit()
    db.refresh(db_notification)
    return db_notification


def mark_all_notifications_read(db: Session) -> int:
    updated = (
        db.query(models.Notification)
        .filter(models.Notification.read.is_(False))
        .update({"read": True})
    )
    db.commit()
    return updated


def delete_notification(db: Session, notification_id: int) -> bool:
    db_notification = (
        db.query(models.Notification)
        .filter(models.Notification.id == notification_id)
        .first()
    )
    if not db_notification:
        return False
    db.delete(db_notification)
    db.commit()
    return True


# ---------------------------------------------------------------------
# Dashboard / Analytics — always computed live, never cached
# ---------------------------------------------------------------------
def get_dashboard_stats(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    return {
        "active_cameras": db.query(func.count(models.Camera.id))
        .filter(models.Camera.is_active.is_(True))
        .scalar()
        or 0,
        "total_cameras": db.query(func.count(models.Camera.id)).scalar() or 0,
        "open_incidents": db.query(func.count(models.Incident.id))
        .filter(models.Incident.status != "resolved")
        .scalar()
        or 0,
        "incidents_today": db.query(func.count(models.Incident.id))
        .filter(models.Incident.created_at >= today_start)
        .scalar()
        or 0,
        "unread_notifications": get_unread_notification_count(db),
    }


def get_analytics(
    db: Session, from_date: Optional[str] = None, to_date: Optional[str] = None
) -> dict:
    query = db.query(models.Incident)

    parsed_from = None
    parsed_to = None
    if from_date:
        parsed_from = datetime.fromisoformat(from_date)
        query = query.filter(models.Incident.created_at >= parsed_from)
    if to_date:
        parsed_to = datetime.fromisoformat(to_date) + timedelta(days=1)
        query = query.filter(models.Incident.created_at < parsed_to)

    incidents = query.all()

    by_severity: dict[str, int] = {}
    by_camera: dict[Optional[int], dict] = {}
    by_day: dict[str, int] = {}

    for inc in incidents:
        by_severity[inc.severity] = by_severity.get(inc.severity, 0) + 1

        cam_key = inc.camera_id
        cam_name = inc.camera.name if inc.camera else "Unassigned"
        if cam_key not in by_camera:
            by_camera[cam_key] = {"camera_id": cam_key, "camera_name": cam_name, "count": 0}
        by_camera[cam_key]["count"] += 1

        day_key = inc.created_at.date().isoformat() if inc.created_at else "unknown"
        by_day[day_key] = by_day.get(day_key, 0) + 1

    return {
        "from_date": from_date,
        "to_date": to_date,
        "total_incidents": len(incidents),
        "by_severity": [
            {"severity": sev, "count": count} for sev, count in sorted(by_severity.items())
        ],
        "by_camera": sorted(by_camera.values(), key=lambda x: -x["count"]),
        "trend": [
            {"date": day, "count": count} for day, count in sorted(by_day.items())
        ],
    }
