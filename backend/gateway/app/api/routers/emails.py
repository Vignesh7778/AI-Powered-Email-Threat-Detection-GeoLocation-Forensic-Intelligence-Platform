"""Email submission routes — ingest, list, detail, bulk actions, graph, custody, verdict."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_user, require_analyst_or_above
from app.core.database import get_db
from app.models.models import (
    Alert,
    Assessment,
    Case,
    CaseSubmission,
    ChainOfCustody,
    Report,
    Submission,
    TenantThreshold,
)
from app.schemas.schemas import (
    BulkActionRequest,
    BulkActionResponse,
    SelfReportResponse,
    StatusUpdateRequest,
    SubmissionListItem,
    SubmissionListResponse,
    SubmissionResponse,
    VerdictRequest,
    VerdictResponse,
)
from app.services import audit as audit_svc
from app.services.pipeline_client import forensics_client, ml_client
from app.services.storage import save_eml

router = APIRouter()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _assessment_to_dict(a: Assessment) -> dict:
    try:
        return json.loads(a.assessment_json)
    except Exception:
        return {}


def _flags(a: Optional[Assessment]) -> Optional[list[str]]:
    if not a or not a.flags:
        return None
    try:
        return json.loads(a.flags)
    except Exception:
        return []


# ---------------------------------------------------------------------------
# POST /api/v1/emails/ingest
# ---------------------------------------------------------------------------

@router.post("/api/v1/emails/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_email(
    file: UploadFile = File(...),
    tenant_id: str = Form(...),
    source: str = Form("upload"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    request: Request = None,
    client_ip: str = Depends(get_client_ip),
):
    """Ingest a raw .eml file. Saves locally and queues for pipeline analysis."""
    content = await file.read()
    submission_id = str(uuid.uuid4())
    storage_ref = save_eml(content, submission_id)

    sub = Submission(
        submission_id=submission_id,
        tenant_id=tenant_id,
        raw_storage_ref=storage_ref,
        status="queued",
        source=source,
        ingested_at=datetime.now(timezone.utc),
    )
    db.add(sub)

    # Record in chain of custody
    db.add(ChainOfCustody(
        submission_id=submission_id,
        actor=f"user:{current_user.user_id}",
        action="ingested",
    ))
    db.commit()

    # Non-blocking evidence log to Forensics API
    forensics_client.log_evidence(submission_id, f"user:{current_user.user_id}", "ingested")

    audit_svc.log_action(
        db, action="ingested_email", target_type="submission",
        target_id=submission_id, actor_id=current_user.user_id,
        submission_id=submission_id, ip_address=client_ip,
    )

    return {"submission_id": submission_id, "status": "queued", "estimated_processing": "async"}


# ---------------------------------------------------------------------------
# POST /api/v1/emails/self-report
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/emails/self-report",
    response_model=SelfReportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def self_report_email(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    client_ip: str = Depends(get_client_ip),
):
    """Lightweight employee self-report endpoint — tenant inferred from logged-in user."""
    content = await file.read()
    submission_id = str(uuid.uuid4())
    tenant_id = current_user.tenant_id or "default"
    storage_ref = save_eml(content, submission_id)

    sub = Submission(
        submission_id=submission_id,
        tenant_id=tenant_id,
        raw_storage_ref=storage_ref,
        status="queued",
        source="self_report",
        ingested_at=datetime.now(timezone.utc),
    )
    db.add(sub)
    db.add(ChainOfCustody(
        submission_id=submission_id,
        actor=f"user:{current_user.user_id}",
        action="self_reported",
    ))
    db.commit()

    forensics_client.log_evidence(submission_id, f"user:{current_user.user_id}", "self_reported")
    audit_svc.log_action(
        db, action="self_reported_email", target_type="submission",
        target_id=submission_id, actor_id=current_user.user_id,
        submission_id=submission_id, ip_address=client_ip,
    )

    return SelfReportResponse(submission_id=submission_id, status="queued")


# ---------------------------------------------------------------------------
# GET /api/v1/emails  (list / search)
# ---------------------------------------------------------------------------

@router.get("/api/v1/emails", response_model=SubmissionListResponse)
def list_emails(
    tenant_id: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    campaign_id: Optional[str] = Query(None),
    auth_failure_type: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    origin_country: Optional[str] = Query(None),
    origin_region: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List/search emails. Supports risk, classification, date, and new filter params."""
    q = db.query(Submission)

    if tenant_id:
        q = q.filter(Submission.tenant_id == tenant_id)
    if from_date:
        try:
            q = q.filter(Submission.ingested_at >= datetime.fromisoformat(from_date))
        except ValueError:
            pass
    if to_date:
        try:
            q = q.filter(Submission.ingested_at <= datetime.fromisoformat(to_date))
        except ValueError:
            pass

    # Assessment-based filters — join only when needed
    if risk_level or classification or campaign_id or auth_failure_type or origin_country or origin_region:
        q = q.join(Assessment, Submission.submission_id == Assessment.submission_id, isouter=True)
        if risk_level:
            q = q.filter(Assessment.risk_level == risk_level)
        if classification:
            q = q.filter(Assessment.classification == classification)
        # campaign_id, auth_failure_type, origin filters require JSON parsing — done post-query

    total = q.count()
    submissions = q.offset((page - 1) * page_size).limit(page_size).all()

    results = []
    for sub in submissions:
        a = sub.assessment
        # Post-filter for JSON-embedded fields
        if campaign_id and a:
            try:
                data = json.loads(a.assessment_json)
                if data.get("attribution", {}).get("linked_campaign_id") != campaign_id:
                    continue
            except Exception:
                pass
        if origin_country and a:
            try:
                data = json.loads(a.assessment_json)
                if data.get("origin", {}).get("geolocation", {}).get("country") != origin_country:
                    continue
            except Exception:
                pass

        results.append(SubmissionListItem(
            submission_id=sub.submission_id,
            risk_level=a.risk_level if a else None,
            classification=a.classification if a else None,
            received_at=sub.ingested_at.isoformat(),
            sender=sub.sender,
            flags=_flags(a),
        ))

    return SubmissionListResponse(results=results, total=total, page=page, page_size=page_size)


# ---------------------------------------------------------------------------
# GET /api/v1/emails/{submission_id}
# ---------------------------------------------------------------------------

@router.get("/api/v1/emails/{submission_id}", response_model=SubmissionResponse)
def get_email(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    client_ip: str = Depends(get_client_ip),
):
    sub = db.query(Submission).filter(Submission.submission_id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    audit_svc.log_action(
        db, action="viewed_email_detail", target_type="submission",
        target_id=submission_id, actor_id=current_user.user_id,
        submission_id=submission_id, ip_address=client_ip,
    )

    assessment_dict = None
    flags = None
    if sub.assessment:
        assessment_dict = _assessment_to_dict(sub.assessment)
        flags = _flags(sub.assessment)

    return SubmissionResponse(
        submission_id=sub.submission_id,
        status=sub.status,
        ingested_at=sub.ingested_at,
        sender=sub.sender,
        subject=sub.subject,
        assessment=assessment_dict,
        flags=flags,
    )


# ---------------------------------------------------------------------------
# PATCH /api/v1/emails/{submission_id}
# ---------------------------------------------------------------------------

@router.patch("/api/v1/emails/{submission_id}")
def update_email_status(
    submission_id: str,
    body: StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    client_ip: str = Depends(get_client_ip),
):
    """Update submission status: dismissed | escalated | reviewing."""
    sub = db.query(Submission).filter(Submission.submission_id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    sub.status = body.status
    db.commit()

    audit_svc.log_action(
        db, action=f"status_updated_to_{body.status}", target_type="submission",
        target_id=submission_id, actor_id=current_user.user_id,
        submission_id=submission_id, ip_address=client_ip,
    )
    return {"submission_id": submission_id, "status": body.status}


# ---------------------------------------------------------------------------
# POST /api/v1/emails/bulk-action
# ---------------------------------------------------------------------------

@router.post("/api/v1/emails/bulk-action", response_model=BulkActionResponse)
def bulk_action(
    body: BulkActionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    client_ip: str = Depends(get_client_ip),
):
    """Apply a triage action to multiple submissions at once."""
    updated = 0
    for sid in body.submission_ids:
        sub = db.query(Submission).filter(Submission.submission_id == sid).first()
        if not sub:
            continue
        if body.action == "mark_reviewed":
            sub.status = "reviewing"
        elif body.action == "mark_false_positive":
            sub.status = "dismissed"
        elif body.action == "escalate_to_case":
            sub.status = "escalated"
            if body.case_id:
                existing = db.query(CaseSubmission).filter(
                    CaseSubmission.case_id == body.case_id,
                    CaseSubmission.submission_id == sid,
                ).first()
                if not existing:
                    db.add(CaseSubmission(case_id=body.case_id, submission_id=sid))
                    # update case submission count
                    case = db.query(Case).filter(Case.case_id == body.case_id).first()
                    if case:
                        case.submission_count = (case.submission_count or 0) + 1
        updated += 1
        audit_svc.log_action(
            db, action=f"bulk_{body.action}", target_type="submission",
            target_id=sid, actor_id=current_user.user_id,
            submission_id=sid, ip_address=client_ip,
        )
    db.commit()
    return BulkActionResponse(updated=updated, action=body.action)


# ---------------------------------------------------------------------------
# GET /api/v1/emails/{submission_id}/report
# ---------------------------------------------------------------------------

@router.get("/api/v1/emails/{submission_id}/report")
def get_report(
    submission_id: str,
    format: str = Query("json", pattern="^(json|pdf)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    client_ip: str = Depends(get_client_ip),
):
    """Generate forensic report for a submission (JSON or PDF placeholder)."""
    sub = db.query(Submission).filter(Submission.submission_id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    assessment_dict = _assessment_to_dict(sub.assessment) if sub.assessment else {}

    # Fetch evidence chain from Forensics API
    custody_chain = forensics_client.evidence_chain(submission_id)

    # Persist report record
    report = Report(
        submission_id=submission_id,
        tenant_id=sub.tenant_id,
        format=format,
        type="on_demand",
        exported_by=current_user.user_id,
    )
    db.add(report)
    db.commit()

    audit_svc.log_action(
        db, action="exported_report", target_type="report",
        target_id=report.report_id, actor_id=current_user.user_id,
        submission_id=submission_id, ip_address=client_ip,
    )

    report_payload = {
        "report_id": report.report_id,
        "submission_id": submission_id,
        "format": format,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "assessment": assessment_dict,
        "chain_of_custody": custody_chain,
        "exported_by": current_user.user_id,
    }

    if format == "pdf":
        report_payload["_note"] = "PDF rendering requires a PDF library (e.g. WeasyPrint). JSON payload provided."

    return report_payload


# ---------------------------------------------------------------------------
# GET /api/v1/emails/{submission_id}/graph
# ---------------------------------------------------------------------------

@router.get("/api/v1/emails/{submission_id}/graph")
def get_email_graph(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Proxy to ML graph API for the campaign linked to this submission."""
    sub = db.query(Submission).filter(Submission.submission_id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    campaign_id = None
    if sub.assessment:
        try:
            data = json.loads(sub.assessment.assessment_json)
            campaign_id = data.get("attribution", {}).get("linked_campaign_id")
        except Exception:
            pass

    if not campaign_id:
        raise HTTPException(status_code=404, detail="No linked campaign found for this submission")

    try:
        graph = ml_client.get_campaign_graph(campaign_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"ML API error: {exc}")

    return {"submission_id": submission_id, "campaign_id": campaign_id, "graph": graph}


# ---------------------------------------------------------------------------
# GET /api/v1/emails/{submission_id}/custody
# ---------------------------------------------------------------------------

@router.get("/api/v1/emails/{submission_id}/custody")
def get_custody(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    client_ip: str = Depends(get_client_ip),
):
    """Chain of custody: local DB records + live Forensics API chain."""
    sub = db.query(Submission).filter(Submission.submission_id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    local_entries = db.query(ChainOfCustody).filter(
        ChainOfCustody.submission_id == submission_id
    ).order_by(ChainOfCustody.timestamp).all()

    forensics_chain = forensics_client.evidence_chain(submission_id)

    audit_svc.log_action(
        db, action="viewed_custody_chain", target_type="submission",
        target_id=submission_id, actor_id=current_user.user_id,
        submission_id=submission_id, ip_address=client_ip,
    )

    return {
        "submission_id": submission_id,
        "local_chain": [
            {
                "log_id": e.log_id,
                "actor": e.actor,
                "action": e.action,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in local_entries
        ],
        "forensics_chain": forensics_chain,
    }


# ---------------------------------------------------------------------------
# POST /api/v1/emails/{submission_id}/verdict
# ---------------------------------------------------------------------------

@router.post("/api/v1/emails/{submission_id}/verdict", response_model=VerdictResponse)
def submit_verdict(
    submission_id: str,
    body: VerdictRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    client_ip: str = Depends(get_client_ip),
):
    """Analyst verdict — proxies to ML /ml/models/feedback for retraining."""
    sub = db.query(Submission).filter(Submission.submission_id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    try:
        ml_client.submit_feedback(submission_id, body.analyst_verdict, current_user.user_id)
    except Exception:
        # Non-blocking — feedback queue may be unavailable
        pass

    audit_svc.log_action(
        db, action="submitted_verdict", target_type="submission",
        target_id=submission_id, actor_id=current_user.user_id,
        submission_id=submission_id, ip_address=client_ip,
    )

    return VerdictResponse(
        submission_id=submission_id,
        analyst_verdict=body.analyst_verdict,
        queued_for_retraining=True,
    )
