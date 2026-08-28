"""User management, saved views, and notification preferences."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_user, require_admin
from app.core.database import get_db
from app.models.models import NotificationPreference, SavedView, User
from app.schemas.schemas import (
    NotificationPrefRead,
    NotificationPrefUpdate,
    SavedViewCreate,
    SavedViewRead,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.services import audit as audit_svc
from app.services.auth import get_password_hash

router = APIRouter()


# ---------------------------------------------------------------------------
# Tenant user management (admin only)
# ---------------------------------------------------------------------------

@router.get("/api/v1/tenants/{tenant_id}/users", response_model=list[UserRead])
def list_tenant_users(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    return db.query(User).filter(User.tenant_id == tenant_id).all()


@router.post(
    "/api/v1/tenants/{tenant_id}/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    tenant_id: str,
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    client_ip: str = Depends(get_client_ip),
):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        user_id=str(uuid.uuid4()),
        email=body.email,
        hashed_password=get_password_hash(body.password),
        role=body.role,
        department=body.department,
        tenant_id=tenant_id,
        mfa_enforced=body.mfa_enforced,
    )
    db.add(user)
    db.commit()
    audit_svc.log_action(
        db, action="created_user", target_type="user",
        target_id=user.user_id, actor_id=current_user.user_id, ip_address=client_ip,
    )
    return user


@router.patch("/api/v1/tenants/{tenant_id}/users/{user_id}", response_model=UserRead)
def update_user(
    tenant_id: str,
    user_id: str,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    client_ip: str = Depends(get_client_ip),
):
    user = db.query(User).filter(User.user_id == user_id, User.tenant_id == tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.role is not None:
        user.role = body.role
    if body.department is not None:
        user.department = body.department
    if body.mfa_enforced is not None:
        user.mfa_enforced = body.mfa_enforced
    if body.is_active is not None:
        user.is_active = body.is_active
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    audit_svc.log_action(
        db, action="updated_user", target_type="user",
        target_id=user_id, actor_id=current_user.user_id, ip_address=client_ip,
    )
    return user


# ---------------------------------------------------------------------------
# Saved views
# ---------------------------------------------------------------------------

@router.get("/api/v1/users/{user_id}/saved-views", response_model=list[SavedViewRead])
def list_saved_views(
    user_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.user_id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Cannot access other users' views")
    return db.query(SavedView).filter(SavedView.user_id == user_id).all()


@router.post(
    "/api/v1/users/{user_id}/saved-views",
    response_model=SavedViewRead,
    status_code=status.HTTP_201_CREATED,
)
def create_saved_view(
    user_id: str,
    body: SavedViewCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.user_id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Cannot create views for other users")

    view = SavedView(
        view_id=str(uuid.uuid4()),
        user_id=user_id,
        name=body.name,
        filter_params_json=json.dumps(body.filter_params),
    )
    db.add(view)
    db.commit()
    return view


# ---------------------------------------------------------------------------
# Notification preferences
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/users/{user_id}/notification-preferences",
    response_model=NotificationPrefRead,
)
def get_notification_prefs(
    user_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.user_id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    pref = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user_id
    ).first()
    if not pref:
        # Return defaults
        return NotificationPrefRead(
            email_alerts=True,
            sms_alerts=False,
            min_risk_level="high",
            updated_at=datetime.now(timezone.utc),
        )
    return pref


@router.put(
    "/api/v1/users/{user_id}/notification-preferences",
    response_model=NotificationPrefRead,
)
def update_notification_prefs(
    user_id: str,
    body: NotificationPrefUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.user_id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    pref = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user_id
    ).first()
    if not pref:
        pref = NotificationPreference(user_id=user_id)
        db.add(pref)

    if body.email_alerts is not None:
        pref.email_alerts = body.email_alerts
    if body.sms_alerts is not None:
        pref.sms_alerts = body.sms_alerts
    if body.min_risk_level is not None:
        pref.min_risk_level = body.min_risk_level
    pref.updated_at = datetime.now(timezone.utc)
    db.commit()
    return pref
