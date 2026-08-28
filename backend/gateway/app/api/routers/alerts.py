"""Alert routes: list and acknowledge."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_user
from app.core.database import get_db
from app.models.models import Alert
from app.schemas.schemas import AcknowledgeResponse, AlertResponse
from app.services import audit as audit_svc

router = APIRouter()

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


@router.get("/api/v1/alerts", response_model=list[AlertResponse])
def list_alerts(
    unacknowledged_only: bool = Query(False),
    min_risk_level: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(Alert)
    if unacknowledged_only:
        q = q.filter(Alert.acknowledged_by == None)  # noqa: E711
    if min_risk_level and min_risk_level in _RISK_ORDER:
        min_val = _RISK_ORDER[min_risk_level]
        allowed = [k for k, v in _RISK_ORDER.items() if v >= min_val]
        q = q.filter(Alert.risk_level.in_(allowed))
    return q.order_by(Alert.created_at.desc()).limit(200).all()


@router.post("/api/v1/alerts/{alert_id}/acknowledge", response_model=AcknowledgeResponse)
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    client_ip: str = Depends(get_client_ip),
):
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    now = datetime.now(timezone.utc)
    alert.acknowledged_by = current_user.user_id
    alert.acknowledged_at = now
    db.commit()

    audit_svc.log_action(
        db, action="acknowledged_alert", target_type="alert",
        target_id=alert_id, actor_id=current_user.user_id, ip_address=client_ip,
    )
    return AcknowledgeResponse(
        alert_id=alert_id,
        acknowledged_by=current_user.user_id,
        acknowledged_at=now,
    )
