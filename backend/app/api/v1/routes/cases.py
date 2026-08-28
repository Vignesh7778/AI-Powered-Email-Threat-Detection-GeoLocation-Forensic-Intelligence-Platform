from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.models.models import Case, CaseSubmission, Submission
from backend.app.schemas.schemas import CaseCreateRequest, CaseUpdateRequest, CaseResponse

router = APIRouter()

@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(req: CaseCreateRequest, db: Session = Depends(get_db)):
    case = Case(
        title=req.title,
        status="open",
        severity=req.severity or "medium",
        notes=req.notes
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    for sid in req.submission_ids:
        sub_link = CaseSubmission(case_id=case.case_id, submission_id=sid)
        db.add(sub_link)
    db.commit()

    return CaseResponse(
        case_id=case.case_id,
        title=case.title,
        status=case.status,
        severity=case.severity,
        notes=case.notes,
        assigned_analyst=case.assigned_analyst,
        submission_ids=req.submission_ids,
        created_at=case.created_at.isoformat(),
        updated_at=case.updated_at.isoformat()
    )

@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    sub_ids = [cs.submission_id for cs in case.case_submissions]
    return CaseResponse(
        case_id=case.case_id,
        title=case.title,
        status=case.status,
        severity=case.severity,
        notes=case.notes,
        assigned_analyst=case.assigned_analyst,
        submission_ids=sub_ids,
        created_at=case.created_at.isoformat(),
        updated_at=case.updated_at.isoformat()
    )

@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(case_id: str, req: CaseUpdateRequest, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if req.title is not None:
        case.title = req.title
    if req.status is not None:
        case.status = req.status
    if req.severity is not None:
        case.severity = req.severity
    if req.notes is not None:
        case.notes = req.notes

    if req.submission_ids is not None:
        # Clear and re-add
        db.query(CaseSubmission).filter(CaseSubmission.case_id == case_id).delete()
        for sid in req.submission_ids:
            db.add(CaseSubmission(case_id=case_id, submission_id=sid))

    db.commit()
    db.refresh(case)

    sub_ids = [cs.submission_id for cs in case.case_submissions]
    return CaseResponse(
        case_id=case.case_id,
        title=case.title,
        status=case.status,
        severity=case.severity,
        notes=case.notes,
        assigned_analyst=case.assigned_analyst,
        submission_ids=sub_ids,
        created_at=case.created_at.isoformat(),
        updated_at=case.updated_at.isoformat()
    )

@router.get("", response_model=List[CaseResponse])
def list_cases(db: Session = Depends(get_db)):
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    results = []
    for c in cases:
        sub_ids = [cs.submission_id for cs in c.case_submissions]
        results.append(
            CaseResponse(
                case_id=c.case_id,
                title=c.title,
                status=c.status,
                severity=c.severity,
                notes=c.notes,
                assigned_analyst=c.assigned_analyst,
                submission_ids=sub_ids,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat()
            )
        )
    return results
