"""
Pydantic schemas (request/response models) for the REST API.
Kept separate from the SQLAlchemy models (app/models.py) so the API
contract can evolve independently of the DB schema.

Field names here are matched deliberately to what the frontend's
services/*.js files already send and expect (see fe_phase2 + Phase 6).
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# ---------------------------------------------------------------------
# Auth / Users
# ---------------------------------------------------------------------
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------------------------------------------------------------------
# Cameras
# ---------------------------------------------------------------------
class CameraBase(BaseModel):
    name: str
    location: Optional[str] = None
    feed_url: Optional[str] = None
    is_active: bool = True


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    feed_url: Optional[str] = None
    is_active: Optional[bool] = None


class CameraOut(CameraBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------
class IncidentBase(BaseModel):
    camera_id: Optional[int] = None
    type: str
    title: Optional[str] = None
    severity: str = "medium"
    status: str = "open"
    confidence: Optional[float] = None
    screenshot_path: Optional[str] = None
    detection_meta: Optional[Any] = None


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    camera_id: Optional[int] = None
    type: Optional[str] = None
    title: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    confidence: Optional[float] = None
    screenshot_path: Optional[str] = None
    detection_meta: Optional[Any] = None


class IncidentOut(IncidentBase):
    id: int
    camera_name: Optional[str] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------
class NotificationBase(BaseModel):
    incident_id: Optional[int] = None
    title: str
    message: Optional[str] = None
    severity: str = "medium"


class NotificationCreate(NotificationBase):
    pass


class NotificationOut(NotificationBase):
    id: int
    read: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UnreadCountOut(BaseModel):
    count: int


class MarkAllReadOut(BaseModel):
    updated: int


# ---------------------------------------------------------------------
# Dashboard / Analytics
# ---------------------------------------------------------------------
class DashboardStatsOut(BaseModel):
    active_cameras: int
    total_cameras: int
    open_incidents: int
    incidents_today: int
    unread_notifications: int


class SeverityBreakdown(BaseModel):
    severity: str
    count: int


class CameraBreakdown(BaseModel):
    camera_id: Optional[int] = None
    camera_name: str
    count: int


class DailyCount(BaseModel):
    date: str
    count: int


class AnalyticsOut(BaseModel):
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    total_incidents: int
    by_severity: list[SeverityBreakdown]
    by_camera: list[CameraBreakdown]
    trend: list[DailyCount]
