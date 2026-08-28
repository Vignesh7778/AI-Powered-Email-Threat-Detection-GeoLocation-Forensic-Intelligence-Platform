"""Case management routes."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_user
from app.core.database import get_db
from app.models.models import Assessment, Case, CaseComment, CaseSubmission, Submission
from app.schemas.schemas import (
    CaseCreate,
    CaseDetailResponse,
    CaseResponse,
    CaseUpdate,
    CommentCreate,
    CommentResponse,
)
from app.services import audit as audit_svc

router = APIRouter()


@router.get("/api/v1/cases", response_model=list[CaseResponse])
def list_cases(
    status_filter: Optional[str] = Query(None, alias="status"),
    sort: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List cases with optional status filter. Supports sort=submission_count_desc."""
    q = db.query(Case)
    if status_filter:
        q = q.filter(Case.status == status_filter)
    if sort == "submission_count_desc":
        q = q.order_by(Case.submission_count.desc())
    else:
        q = q.order_by(Case.updated_at.desc())
    cases = q.offset((page - 1) * page_size).limit(min(limit, page_size)).all()
    return cases


@router.post("/api/v1/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    body: CaseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    client_ip: str = Depends(get_client_ip),
):
    """Create a new case and link submissions."""
    case = Case(
        case_id=str(uuid.uuid4()),
        title=body.title,
        notes=body.notes,
        tenant_id=current_user.tenant_id or "default",
        submission_count=len(body.submission_ids),
    )
    db.add(case)
    db.flush()

    for sid in body.submission_ids:
        db.add(CaseSubmission(case_id=case.case_id, submission_id=sid))
        sub = db.query(Submission).filter(Submission.submission_id == sid).first()
        if sub:
            sub.status = "escalated"

    db.commit()
    audit_svc.log_action(
        db, action="created_case", target_type="case",
        target_id=case.case_id, actor_id=current_user.user_id,
        case_id=case.case_id, ip_address=client_ip,
    )
    return case


@router.get("/api/v1/cases/{case_id}", response_model=CaseDetailResponse)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    client_ip: str = Depends(get_client_ip),
):
    """Case detail with linked submissions and shared_indicators from assessments."""
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    audit_svc.log_action(
        db, action="viewed_case", target_type="case",
        target_id=case_id, actor_id=current_user.user_id,
        case_id=case_id, ip_address=client_ip,
    )

    submissions_data = []
    for cs in case.case_submissions:
        sub = db.query(Submission).filter(Submission.submission_id == cs.submission_id).first()
        if not sub:
            continue
        entry: dict = {
            "submission_id": sub.submission_id,
            "status": sub.status,
            "sender": sub.sender,
            "ingested_at": sub.ingested_at.isoformat(),
            "risk_level": None,
            "classification": None,
            "shared_indicators": [],
        }
        if sub.assessment:
            entry["risk_level"] = sub.assessment.risk_level
            entry["classification"] = sub.assessment.classification
            try:
                data = json.loads(sub.assessment.assessment_json)
                entry["shared_indicators"] = (
                    data.get("attribution", {}).get("shared_indicators", [])
                )
            except Exception:
                pass
        submissions_data.append(entry)

    return CaseDetailResponse(
        case_id=case.case_id,
        title=case.title,
        status=case.status,
        notes=case.notes,
        assigned_to=case.assigned_to,
        tenant_id=case.tenant_id,
        created_at=case.created_at,
        updated_at=case.updated_at,
        submissions=submissions_data,
    )


@router.patch("/api/v1/cases/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: str,
    body: CaseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    client_ip: str = Depends(get_client_ip),
):
    """Update case status, assignee, or notes."""
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if body.status is not None:
        case.status = body.status
    if body.assigned_to is not None:
        case.assigned_to = body.assigned_to
    if body.notes is not None:
        case.notes = body.notes
    case.updated_at = datetime.now(timezone.utc)
    db.commit()

    audit_svc.log_action(
        db, action="updated_case", target_type="case",
        target_id=case_id, actor_id=current_user.user_id,
        case_id=case_id, ip_address=client_ip,
    )
    return case


@router.get("/api/v1/cases/{case_id}/comments", response_model=list[CommentResponse])
def list_comments(
    case_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return db.query(CaseComment).filter(CaseComment.case_id == case_id).order_by(CaseComment.created_at).all()


@router.post(
    "/api/v1/cases/{case_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    case_id: str,
    body: CommentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    comment = CaseComment(
        comment_id=str(uuid.uuid4()),
        case_id=case_id,
        author_id=current_user.user_id,
        body=body.body,
    )
    db.add(comment)
    db.commit()
    return comment
