"""Rules, thresholds and watchlist routes."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_user, require_admin
from app.core.database import get_db
from app.models.models import TenantThreshold, Watchlist
from app.schemas.schemas import (
    ThresholdRead,
    ThresholdUpdate,
    WatchlistEntry,
    WatchlistRead,
)
from app.services import audit as audit_svc

router = APIRouter()

_VALID_LIST_TYPES = {"protected_brands", "blocked_domains", "allowed_domains", "blocked_ips"}


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

@router.get("/api/v1/tenants/{tenant_id}/rules/thresholds", response_model=ThresholdRead)
def get_thresholds(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.query(TenantThreshold).filter(TenantThreshold.tenant_id == tenant_id).first()
    if not row:
        # Return defaults without persisting
        from datetime import datetime, timezone
        return ThresholdRead(
            tenant_id=tenant_id,
            alert_threshold=0.6,
            auto_quarantine_threshold=0.9,
            updated_at=datetime.now(timezone.utc),
        )
    return row


@router.put("/api/v1/tenants/{tenant_id}/rules/thresholds", response_model=ThresholdRead)
def update_thresholds(
    tenant_id: str,
    body: ThresholdUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    client_ip: str = Depends(get_client_ip),
):
    row = db.query(TenantThreshold).filter(TenantThreshold.tenant_id == tenant_id).first()
    if not row:
        row = TenantThreshold(tenant_id=tenant_id)
        db.add(row)
    if body.alert_threshold is not None:
        row.alert_threshold = body.alert_threshold
    if body.auto_quarantine_threshold is not None:
        row.auto_quarantine_threshold = body.auto_quarantine_threshold
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    audit_svc.log_action(
        db, action="updated_thresholds", target_type="tenant",
        target_id=tenant_id, actor_id=current_user.user_id, ip_address=client_ip,
    )
    return row


# ---------------------------------------------------------------------------
# Watchlists
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/tenants/{tenant_id}/watchlists/{list_type}",
    response_model=list[WatchlistRead],
)
def get_watchlist(
    tenant_id: str,
    list_type: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if list_type not in _VALID_LIST_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid list_type. Choose from: {_VALID_LIST_TYPES}")
    return (
        db.query(Watchlist)
        .filter(Watchlist.tenant_id == tenant_id, Watchlist.list_type == list_type)
        .all()
    )


@router.post(
    "/api/v1/tenants/{tenant_id}/watchlists/{list_type}",
    response_model=WatchlistRead,
    status_code=status.HTTP_201_CREATED,
)
def add_watchlist_entry(
    tenant_id: str,
    list_type: str,
    body: WatchlistEntry,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    client_ip: str = Depends(get_client_ip),
):
    if list_type not in _VALID_LIST_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid list_type.")

    existing = db.query(Watchlist).filter(
        Watchlist.tenant_id == tenant_id,
        Watchlist.list_type == list_type,
        Watchlist.value == body.value,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Entry already exists")

    entry = Watchlist(
        tenant_id=tenant_id,
        list_type=list_type,
        value=body.value,
        added_by=current_user.user_id,
    )
    db.add(entry)
    db.commit()
    audit_svc.log_action(
        db, action=f"added_to_{list_type}", target_type="watchlist",
        target_id=str(entry.id), actor_id=current_user.user_id, ip_address=client_ip,
    )
    return entry


@router.delete("/api/v1/tenants/{tenant_id}/watchlists/{list_type}/{entry_id}")
def delete_watchlist_entry(
    tenant_id: str,
    list_type: str,
    entry_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    client_ip: str = Depends(get_client_ip),
):
    entry = db.query(Watchlist).filter(
        Watchlist.id == entry_id,
        Watchlist.tenant_id == tenant_id,
        Watchlist.list_type == list_type,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    db.delete(entry)
    db.commit()
    audit_svc.log_action(
        db, action=f"removed_from_{list_type}", target_type="watchlist",
        target_id=str(entry_id), actor_id=current_user.user_id, ip_address=client_ip,
    )
    return {"deleted": entry_id}
