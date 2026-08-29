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

@router.get("/health", tags=["System Status"])
def check_system_health(db: Session = Depends(get_db)):
    from backend.app.models.models import Submission, Case, Alert, Campaign, User
    from backend.app.core.database import engine
    
    sub_count = db.query(Submission).count()
    case_count = db.query(Case).count()
    alert_count = db.query(Alert).count()
    camp_count = db.query(Campaign).count()
    user_count = db.query(User).count()
    
    db_type = "PostgreSQL" if "postgresql" in str(engine.url) else "SQLite"
    return {
        "status": "healthy",
        "database": db_type,
        "counts": {
            "submissions": sub_count,
            "cases": case_count,
            "alerts": alert_count,
            "campaigns": camp_count,
            "users": user_count
        }
    }

@router.post("/seed", tags=["System Status"])
def force_seed_database(db: Session = Depends(get_db)):
    from backend.app.core.seeder import seed_database_if_empty
    seed_database_if_empty(db, force=True)
    return check_system_health(db)
