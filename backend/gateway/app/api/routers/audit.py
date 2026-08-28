"""Audit log query endpoint."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import AuditLog
from app.schemas.schemas import AuditLogEntry

router = APIRouter()


@router.get("/api/v1/audit-log", response_model=list[AuditLogEntry])
def get_audit_log(
    submission_id: Optional[str] = Query(None),
    case_id: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Searchable append-only audit log of all gateway-side actions."""
    q = db.query(AuditLog)

    if submission_id:
        q = q.filter(AuditLog.submission_id == submission_id)
    if case_id:
        q = q.filter(AuditLog.case_id == case_id)
    if actor:
        q = q.filter(AuditLog.actor_id == actor)
    if from_date:
        try:
            q = q.filter(AuditLog.timestamp >= datetime.fromisoformat(from_date))
        except ValueError:
            pass
    if to_date:
        try:
            q = q.filter(AuditLog.timestamp <= datetime.fromisoformat(to_date))
        except ValueError:
            pass

    return q.order_by(AuditLog.timestamp.desc()).limit(limit).all()
