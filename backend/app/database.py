"""
SQLAlchemy engine/session setup.

Uses PostgreSQL via DATABASE_URL (see app/config.py + .env).
Do not switch to another database engine - the project standard is
PostgreSQL with SQLAlchemy ORM and Alembic migrations.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # avoids "server closed the connection" errors
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
