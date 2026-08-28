"""Internal webhook from the Pipeline: receives FraudAssessment, stores it, fires alerts."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.models import Alert, Assessment, ChainOfCustody, Submission, TenantThreshold

router = APIRouter()


@router.post("/internal/webhooks/fraud-assessment", status_code=status.HTTP_204_NO_CONTENT)
async def receive_fraud_assessment(
    request: Request,
    x_pipeline_signature: str = Header(...),
    db: Session = Depends(get_db),
):
    """
    Called by the Pipeline orchestrator (backend/pipeline/) after analysis.
    Validates the shared-secret header, persists the FraudAssessment, and
    creates an Alert if fraud_score >= tenant threshold.
    """
    if x_pipeline_signature != settings.pipeline_signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid pipeline signature")

    try:
        payload: dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    submission_id = payload.get("submission_id")
    if not submission_id:
        raise HTTPException(status_code=400, detail="Missing submission_id in payload")

    sub = db.query(Submission).filter(Submission.submission_id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")

    fraud_score = float(payload.get("fraud_score", 0.0))
    risk_level = payload.get("risk_level", "low")
    classification = payload.get("classification", "legitimate")
    confidence = float(payload.get("confidence", 0.0))
    narrative_summary = payload.get("narrative_summary")

    # Derive flags for inbox quick-render
    auth = payload.get("auth_results", {})
    flags = []
    if auth.get("spf") in ("fail", "softfail"):
        flags.append("spf_fail")
    if auth.get("dkim") == "fail":
        flags.append("dkim_fail")
    if auth.get("dmarc") == "fail":
        flags.append("dmarc_fail")
    domain_intel = payload.get("domain_intel", {})
    if domain_intel.get("lookalike_score", 0) > 0.7:
        flags.append("spoofed_domain")
    indicators = payload.get("indicators", [])
    for ind in indicators:
        if "link" in str(ind.get("type", "")).lower():
            flags.append("suspicious_link")
            break
    origin = payload.get("origin", {})
    geo = origin.get("geolocation", {})
    if geo.get("country") and geo["country"] not in ("IN", "US", "GB"):  # example baseline
        flags.append("geo_mismatch")

    # Upsert Assessment
    existing_assessment = db.query(Assessment).filter(
        Assessment.submission_id == submission_id
    ).first()
    if existing_assessment:
        existing_assessment.assessment_json = json.dumps(payload)
        existing_assessment.risk_level = risk_level
        existing_assessment.classification = classification
        existing_assessment.fraud_score = fraud_score
        existing_assessment.confidence = confidence
        existing_assessment.flags = json.dumps(list(set(flags)))
        existing_assessment.narrative_summary = narrative_summary
        existing_assessment.analyzed_at = datetime.now(timezone.utc)
    else:
        db.add(Assessment(
            submission_id=submission_id,
            assessment_json=json.dumps(payload),
            risk_level=risk_level,
            classification=classification,
            fraud_score=fraud_score,
            confidence=confidence,
            flags=json.dumps(list(set(flags))),
            narrative_summary=narrative_summary,
        ))

    sub.status = "complete"
    sub.sender = (
        payload.get("domain_intel", {}).get("sender_domain")
        or sub.sender
    )

    db.add(ChainOfCustody(
        submission_id=submission_id,
        actor="system:pipeline",
        action="assessment_delivered",
    ))

    db.flush()

    # Fire alert if fraud_score >= tenant threshold
    tenant_threshold = db.query(TenantThreshold).filter(
        TenantThreshold.tenant_id == sub.tenant_id
    ).first()
    alert_threshold = tenant_threshold.alert_threshold if tenant_threshold else 0.6

    if fraud_score >= alert_threshold:
        db.add(Alert(
            alert_id=str(uuid.uuid4()),
            submission_id=submission_id,
            fraud_score=fraud_score,
            risk_level=risk_level,
        ))

    db.commit()
