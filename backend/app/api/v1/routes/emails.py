import uuid
import os
import hashlib
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.models import Submission, Assessment, ChainOfCustody
from backend.app.schemas.schemas import (
    IngestResponse, EmailDetailResponse, EmailListResponse,
    EmailListItem, FraudAssessment, EmailSubmission, RawBody, SourceContext
)
from backend.analysis.parser.email_parser import email_parser
from backend.analysis.evidence.evidence_logger import evidence_logger
from backend.app.services.pipeline_orchestrator import pipeline_orchestrator
from backend.reports.report_generator import report_generator

router = APIRouter()

@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_email(
    file: Optional[UploadFile] = File(None),
    raw_content: Optional[str] = Form(None),
    tenant_id: str = Form("tenant-cyber-sec-01"),
    source: str = Form("upload"),
    mailbox: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    submission_id = str(uuid.uuid4())
    storage_dir = settings.STORAGE_PATH
    try:
        os.makedirs(storage_dir, exist_ok=True)
    except Exception:
        storage_dir = "/tmp/storage"
        try:
            os.makedirs(storage_dir, exist_ok=True)
        except Exception:
            pass

    if file:
        file_bytes = await file.read()
        file_name = file.filename
    elif raw_content:
        file_bytes = raw_content.encode('utf-8')
        file_name = "raw_email_push.eml"
    else:
        raise HTTPException(status_code=400, detail="Either .eml file or raw_content must be provided")

    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    import re
    safe_file_name = re.sub(r'[^a-zA-Z0-9_\.-]', '_', file_name or 'unnamed.eml')[:80]
    storage_ref = os.path.join(storage_dir, f"{submission_id[:8]}_{safe_file_name}")
    try:
        with open(storage_ref, "wb") as f:
            f.write(file_bytes)
    except Exception:
        storage_ref = os.path.join(storage_dir, f"{submission_id[:8]}.eml")
        try:
            with open(storage_ref, "wb") as f:
                f.write(file_bytes)
        except Exception:
            pass

    # Parse .eml
    parsed = email_parser.parse_raw_eml(file_bytes, submission_id, storage_dir)

    # Persist initial submission record
    sub = Submission(
        submission_id=submission_id,
        tenant_id=tenant_id,
        file_name=file_name,
        file_size=len(file_bytes),
        raw_storage_ref=storage_ref,
        sha256_hash=sha256_hash,
        sender=parsed.get("sender"),
        recipient=parsed.get("recipient"),
        subject=parsed.get("subject"),
        source=source,
        mailbox=mailbox,
        status="analyzing",
        received_at=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc)
    )
    db.add(sub)
    db.commit()

    # Log initial custody event
    evidence_logger.log_event(
        db=db,
        submission_id=submission_id,
        actor="gateway_ingest",
        action="ingested_raw_artifact",
        details={"file_name": file_name, "size_bytes": len(file_bytes), "sha256": sha256_hash},
        raw_bytes=file_bytes
    )

    # Construct EmailSubmission
    submission_obj = EmailSubmission(
        submission_id=submission_id,
        received_at=datetime.now(timezone.utc).isoformat(),
        raw_headers=parsed["raw_headers"],
        raw_body=RawBody(
            text_plain=parsed.get("text_plain"),
            text_html=parsed.get("text_html")
        ),
        attachments=parsed.get("attachments", []),
        source_context=SourceContext(
            ingested_via=source if source in ["imap", "upload", "forward", "api"] else "upload",
            tenant_id=tenant_id,
            mailbox=mailbox
        )
    )

    # Execute synchronous analysis
    try:
        pipeline_orchestrator.analyze_submission(submission_obj, db=db, actor="gateway_pipeline")
    except Exception as e:
        print(f"Pipeline error for submission {submission_id}: {e}")

    return IngestResponse(
        submission_id=submission_id,
        status="analyzing",
        estimated_processing="sync"
    )

@router.post("/{submission_id}/refresh", response_model=EmailDetailResponse)
def refresh_email_analysis(submission_id: str, db: Session = Depends(get_db)):
    sub = db.query(Submission).filter(Submission.submission_id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    if not sub.raw_storage_ref or not os.path.exists(sub.raw_storage_ref):
        raise HTTPException(status_code=400, detail="Original raw email artifact is not present on disk")

    with open(sub.raw_storage_ref, "rb") as f:
        file_bytes = f.read()

    parsed = email_parser.parse_raw_eml(file_bytes, submission_id, settings.STORAGE_PATH)

    submission_obj = EmailSubmission(
        submission_id=submission_id,
        received_at=sub.received_at.isoformat() if sub.received_at else datetime.now(timezone.utc).isoformat(),
        raw_headers=parsed["raw_headers"],
        raw_body=RawBody(
            text_plain=parsed.get("text_plain"),
            text_html=parsed.get("text_html")
        ),
        attachments=parsed.get("attachments", []),
        source_context=SourceContext(
            ingested_via=sub.source if sub.source in ["imap", "upload", "forward", "api"] else "upload",
            tenant_id=sub.tenant_id or "tenant-cyber-sec-01",
            mailbox=sub.mailbox
        )
    )

    # Re-execute real-time live queries and analysis
    evidence_logger.log_event(
        db=db,
        submission_id=submission_id,
        actor="analyst_refresh",
        action="re_queried_live_intelligence",
        details={"re_analyzed_at": datetime.now(timezone.utc).isoformat(), "action": "live_dns_geoip_requery"}
    )

    assessment = pipeline_orchestrator.analyze_submission(submission_obj, db=db, actor="analyst_refresh")

    return EmailDetailResponse(
        submission_id=sub.submission_id,
        status=sub.status,
        ingested_at=sub.ingested_at.isoformat() if sub.ingested_at else "",
        file_name=sub.file_name,
        sha256_hash=sub.sha256_hash,
        sender=sub.sender,
        recipient=sub.recipient,
        subject=sub.subject,
        assessment=assessment
    )

@router.get("", response_model=EmailListResponse)
def list_emails(
    tenant_id: Optional[str] = None,
    risk_level: Optional[str] = None,
    classification: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    limit: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    if limit is not None:
        page_size = max(1, min(limit, 100))

    query = db.query(Submission)
    if tenant_id:
        query = query.filter(Submission.tenant_id == tenant_id)

    total = query.count()
    submissions = query.order_by(Submission.ingested_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    results: List[EmailListItem] = []
    for s in submissions:
        r_level = s.assessment.risk_level if s.assessment else "unknown"
        c_class = s.assessment.classification if s.assessment else "unknown"
        f_score = s.assessment.fraud_score if s.assessment else 0.0

        if risk_level and r_level != risk_level:
            continue
        if classification and c_class != classification:
            continue

        orig_ip = None
        orig_asn = None
        if s.assessment and s.assessment.raw_assessment:
            orig = s.assessment.raw_assessment.get("origin", {})
            orig_ip = orig.get("origin_ip") or orig.get("originating_ip")
            orig_asn = orig.get("asn", {}).get("asn") or orig.get("geolocation", {}).get("asn")

        results.append(
            EmailListItem(
                submission_id=s.submission_id,
                risk_level=r_level or "unknown",
                classification=c_class or "unknown",
                fraud_score=f_score if f_score is not None else 0.0,
                received_at=s.received_at.isoformat() if s.received_at else (s.ingested_at.isoformat() if s.ingested_at else ""),
                sender=s.sender or "Unknown Sender",
                recipient=s.recipient or "security-team@org.gov",
                subject=s.subject or "No Subject",
                origin_ip=orig_ip,
                origin_asn=orig_asn,
                status=s.status or "complete"
            )
        )

    return EmailListResponse(
        results=results,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/{submission_id}", response_model=EmailDetailResponse)
def get_email_detail(submission_id: str, db: Session = Depends(get_db)):
    sub = db.query(Submission).filter(Submission.submission_id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    assessment_obj = None
    if sub.assessment and sub.assessment.raw_assessment:
        assessment_obj = FraudAssessment(**sub.assessment.raw_assessment)

    return EmailDetailResponse(
        submission_id=sub.submission_id,
        status=sub.status,
        ingested_at=sub.ingested_at.isoformat() if sub.ingested_at else "",
        file_name=sub.file_name,
        sha256_hash=sub.sha256_hash,
        sender=sub.sender,
        recipient=sub.recipient,
        subject=sub.subject,
        assessment=assessment_obj
    )


@router.get("/{submission_id}/report")
def export_report(
    submission_id: str,
    format: str = Query("json", pattern="^(json|pdf)$"),
    db: Session = Depends(get_db)
):
    sub = db.query(Submission).filter(Submission.submission_id == submission_id).first()
    if not sub or not sub.assessment or not sub.assessment.raw_assessment:
        raise HTTPException(status_code=404, detail="Completed assessment not found for this submission")

    assessment = FraudAssessment(**sub.assessment.raw_assessment)
    chain_entries = db.query(ChainOfCustody).filter(ChainOfCustody.submission_id == submission_id).order_by(ChainOfCustody.timestamp.asc()).all()

    sub_meta = {
        "submission_id": sub.submission_id,
        "file_name": sub.file_name,
        "sha256_hash": sub.sha256_hash,
        "sender": sub.sender,
        "recipient": sub.recipient,
        "subject": sub.subject,
        "source": sub.source,
        "received_at": sub.received_at.isoformat() if sub.received_at else ""
    }

    if format == "pdf":
        pdf_bytes = report_generator.generate_pdf_report(assessment, sub_meta, chain_entries)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=forensic_report_{submission_id[:8]}.pdf"}
        )
    else:
        json_report = report_generator.generate_json_report(assessment, sub_meta, chain_entries)
        return json_report
