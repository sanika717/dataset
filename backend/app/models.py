"""
SQLAlchemy ORM models.

Tables: users, cameras, incidents, notifications — this is the schema the
frontend (built across Phases 1-6) is written against. Supersedes the
Workers/Alerts/Reports schema from earlier phases.

Dashboard statistics are intentionally NOT stored anywhere - they're
always computed on the fly from these tables (see app/crud.py), same
convention as the old schema.
"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    # "admin" | "operator" — no endpoints currently gate on this, it's
    # here so role-based access can be added without a migration later.
    role = Column(String, default="operator")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)
    # RTSP/HTTP source the detection pipeline reads from. Optional so a
    # camera can be registered before its feed is wired up.
    feed_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    incidents = relationship(
        "Incident", back_populates="camera", cascade="all, delete-orphan"
    )


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=True)

    # e.g. "ppe_violation" | "fall_zone_violation"
    type = Column(String, nullable=False)
    title = Column(String, nullable=True)
    # "low" | "medium" | "high" | "critical"
    severity = Column(String, default="medium")
    # "open" | "acknowledged" | "resolved"
    status = Column(String, default="open")
    confidence = Column(Float, nullable=True)
    screenshot_path = Column(String, nullable=True)
    # Raw detection metadata (bbox, track id, zone geometry, etc.) — kept
    # as JSON rather than dedicated columns since its shape varies by
    # incident type.
    detection_meta = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    camera = relationship("Camera", back_populates="incidents")
    notifications = relationship(
        "Notification", back_populates="incident", cascade="all, delete-orphan"
    )


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)

    title = Column(String, nullable=False)
    message = Column(String, nullable=True)
    severity = Column(String, default="medium")
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    incident = relationship("Incident", back_populates="notifications")
