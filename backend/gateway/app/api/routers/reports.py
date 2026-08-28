"""Reports & export center routes."""
from __future__ import annotations

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import Report, ReportSchedule
from app.schemas.schemas import ReportRead, ScheduleCreate, ScheduleRead

router = APIRouter()


@router.get("/api/v1/reports", response_model=list[ReportRead])
def list_reports(
    tenant_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List previously generated report artifacts."""
    q = db.query(Report)
    if tenant_id:
        q = q.filter(Report.tenant_id == tenant_id)
    if type:
        q = q.filter(Report.type == type)
    return q.order_by(Report.exported_at.desc()).limit(100).all()


@router.get("/api/v1/reports/schedules", response_model=list[ScheduleRead])
def list_schedules(
    tenant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(ReportSchedule)
    if tenant_id:
        q = q.filter(ReportSchedule.tenant_id == tenant_id)
    return q.order_by(ReportSchedule.created_at.desc()).all()


@router.post(
    "/api/v1/reports/schedules",
    response_model=ScheduleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_schedule(
    body: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Schedule a recurring report."""
    schedule = ReportSchedule(
        schedule_id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id or "default",
        frequency=body.frequency,
        format=body.format,
        recipients_json=json.dumps(body.recipients),
        filter_params_json=json.dumps(body.filter_params),
        created_by=current_user.user_id,
    )
    db.add(schedule)
    db.commit()
    return schedule
