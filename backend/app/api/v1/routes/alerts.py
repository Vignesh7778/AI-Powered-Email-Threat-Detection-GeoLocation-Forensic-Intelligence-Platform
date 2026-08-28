from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import Alert
from backend.app.schemas.schemas import AlertResponse, AlertAcknowledgeResponse

router = APIRouter()

@router.get("", response_model=List[AlertResponse])
def get_alerts(
    unacknowledged_only: bool = Query(False),
    min_risk_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    if unacknowledged_only:
        query = query.filter(Alert.acknowledged == False)

    if min_risk_level:
        if min_risk_level == "critical":
            query = query.filter(Alert.severity == "critical")
        elif min_risk_level == "high":
            query = query.filter(Alert.severity.in_(["high", "critical"]))
        elif min_risk_level == "medium":
            query = query.filter(Alert.severity.in_(["medium", "high", "critical"]))

    alerts = query.order_by(Alert.triggered_at.desc()).limit(100).all()
    results = []
    for a in alerts:
        results.append(
            AlertResponse(
                alert_id=a.alert_id,
                submission_id=a.submission_id,
                severity=a.severity,
                fraud_score=a.fraud_score,
                title=a.title,
                reason=a.reason,
                acknowledged=a.acknowledged,
                acknowledged_by=a.acknowledged_by,
                acknowledged_at=a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                triggered_at=a.triggered_at.isoformat() if a.triggered_at else ""
            )
        )
    return results

@router.post("/{alert_id}/acknowledge", response_model=AlertAcknowledgeResponse)
def acknowledge_alert(
    alert_id: str,
    analyst_id: str = Query("analyst@org.gov"),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    now = datetime.now(timezone.utc)
    alert.acknowledged = True
    alert.acknowledged_by = analyst_id
    alert.acknowledged_at = now
    db.commit()

    return AlertAcknowledgeResponse(
        alert_id=alert.alert_id,
        acknowledged_by=analyst_id,
        acknowledged_at=now.isoformat()
    )
