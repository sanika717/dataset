"""
Password hashing + JWT creation/verification.

JWT_SECRET_KEY must be overridden via .env in any real deployment — the
default here is only so the app doesn't crash on a fresh checkout.

Uses the `bcrypt` package directly rather than passlib: passlib 1.7.4's
bcrypt backend self-test is broken against bcrypt>=4.1 (raises
`AttributeError: module 'bcrypt' has no attribute '__about__'` /
"password cannot be longer than 72 bytes" on the very first hash call) —
a known upstream incompatibility, not a version pin worth chasing.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
# bcrypt silently ignores bytes beyond 72 — truncate up front so a very
# long password doesn't quietly collide with a truncated variant of itself.
_MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    truncated = password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(truncated, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    truncated = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    try:
        return bcrypt.checkpw(truncated, hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """Returns the subject (user id, as a string) or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
