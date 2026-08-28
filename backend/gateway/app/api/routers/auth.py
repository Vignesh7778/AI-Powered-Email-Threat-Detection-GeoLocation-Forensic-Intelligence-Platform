"""Auth routes: login, refresh, MFA verify."""
from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas.schemas import (
    LoginRequest,
    LoginResponse,
    MfaVerifyRequest,
    MfaVerifyResponse,
    RefreshRequest,
    RefreshResponse,
)
from app.services.auth import (
    authenticate_user,
    create_access_token,
    create_mfa_pending_token,
    create_refresh_token,
    decode_token,
    verify_mfa_code,
)

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email + password.

    - If the user has MFA enabled: returns `mfa_required=true` and a short-lived
      `mfa_token` — no JWT is issued yet.
    - Otherwise: returns full `access_token` + `refresh_token`.
    """
    user = authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    if user.mfa_enabled:
        mfa_token = create_mfa_pending_token(db, user.user_id)
        return LoginResponse(mfa_required=True, mfa_token=mfa_token, role=user.role)

    token_data = {"sub": user.user_id, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        role=user.role,
        mfa_required=False,
    )


@router.post("/auth/refresh", response_model=RefreshResponse)
def refresh_token(body: RefreshRequest):
    """Exchange a valid refresh token for a new access token."""
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    token_data = {"sub": payload["sub"], "role": payload.get("role")}
    new_access = create_access_token(token_data)
    return RefreshResponse(
        access_token=new_access,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/auth/mfa/verify", response_model=MfaVerifyResponse)
def mfa_verify(body: MfaVerifyRequest, db: Session = Depends(get_db)):
    """
    Complete MFA login.

    Exchange the `mfa_token` (from /auth/login) + TOTP `code` for full JWTs.
    """
    user = verify_mfa_code(db, body.mfa_token, body.code)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA token / code",
        )
    token_data = {"sub": user.user_id, "role": user.role}
    return MfaVerifyResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        expires_in=settings.access_token_expire_minutes * 60,
        role=user.role,
    )
