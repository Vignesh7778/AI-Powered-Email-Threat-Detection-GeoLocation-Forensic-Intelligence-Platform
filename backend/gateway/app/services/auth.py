"""JWT authentication, password hashing, and MFA utilities."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import pyotp
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import MfaToken, User

# PBKDF2 is the default because passlib's bcrypt backend emits compatibility
# errors with the bcrypt package on Python 3.14. Keep bcrypt in the context so
# existing hashes can still be verified during migration.
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT. Returns payload dict or None on failure."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# User helpers
# ---------------------------------------------------------------------------

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.user_id == user_id).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# ---------------------------------------------------------------------------
# MFA helpers
# ---------------------------------------------------------------------------

def create_mfa_pending_token(db: Session, user_id: str) -> str:
    """Issue a short-lived opaque token that represents a completed password
    check, to be exchanged for full JWT once the TOTP code is verified."""
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    entry = MfaToken(
        user_id=user_id,
        mfa_token=token,
        expires_at=expires,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    return token


def verify_mfa_code(db: Session, mfa_token: str, code: str) -> Optional[User]:
    """Verify the TOTP code via the pending MFA token.  Returns the User on
    success, None on any failure (invalid token, expired, wrong code)."""
    entry = db.query(MfaToken).filter(
        MfaToken.mfa_token == mfa_token,
        MfaToken.used == False,  # noqa: E712
    ).first()
    if entry is None:
        return None
    # SQLite stores datetimes without timezone; compare naively
    now_naive = datetime.utcnow()
    expires_naive = entry.expires_at.replace(tzinfo=None) if entry.expires_at.tzinfo else entry.expires_at
    if expires_naive < now_naive:
        return None
    user = get_user_by_id(db, entry.user_id)
    if not user or not user.mfa_secret:
        return None
    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(code, valid_window=1):
        return None
    entry.used = True
    db.commit()
    return user
