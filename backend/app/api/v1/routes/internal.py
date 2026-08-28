from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import Optional
from backend.app.core.database import get_db
from backend.app.schemas.schemas import EmailSubmission, FraudAssessment
from backend.app.services.pipeline_orchestrator import pipeline_orchestrator
from backend.app.models.models import Assessment

router = APIRouter()

@router.post("/analyze", response_model=FraudAssessment, tags=["Internal Pipeline"])
def analyze_internal(submission: EmailSubmission, db: Session = Depends(get_db)):
    """
    Internal synchronous analysis pipeline orchestrator.
    Called by Gateway or test runners to evaluate an EmailSubmission object.
    """
    assessment = pipeline_orchestrator.analyze_submission(submission, db=db, actor="internal_pipeline")
    return assessment

@router.post("/webhooks/fraud-assessment", status_code=status.HTTP_204_NO_CONTENT, tags=["Internal Pipeline"])
def receive_fraud_webhook(
    assessment: FraudAssessment,
    x_pipeline_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    # Upsert assessment in database
    ass_record = db.query(Assessment).filter(Assessment.submission_id == assessment.submission_id).first()
    if not ass_record:
        ass_record = Assessment(
            submission_id=assessment.submission_id,
            fraud_score=assessment.fraud_score,
            risk_level=assessment.risk_level,
            classification=assessment.classification,
            confidence=assessment.confidence,
            raw_assessment=assessment.model_dump()
        )
        db.add(ass_record)
    else:
        ass_record.fraud_score = assessment.fraud_score
        ass_record.risk_level = assessment.risk_level
        ass_record.classification = assessment.classification
        ass_record.confidence = assessment.confidence
        ass_record.raw_assessment = assessment.model_dump()
    db.commit()
    return
