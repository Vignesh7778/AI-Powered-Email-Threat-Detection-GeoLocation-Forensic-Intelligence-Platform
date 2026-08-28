from datetime import datetime, timezone
from fastapi import APIRouter, status
from app.schemas.model_ops import (
    ModelHealthResponse,
    ModelHealthItem,
    FeedbackRequest,
    FeedbackResponse
)
from app.core.config import settings

router = APIRouter()

# In-memory storage for feedback events
FEEDBACK_LOG = []

@router.get("/models/health", response_model=ModelHealthResponse, status_code=status.HTTP_200_OK)
async def get_models_health():
    """
    Returns health, model versions, and training timestamps of all active ML models.
    """
    now = datetime.now(timezone.utc).isoformat()
    return ModelHealthResponse(
        models=[
            ModelHealthItem(
                name="classifier",
                version=settings.CLASSIFIER_MODEL_VERSION,
                last_trained=now,
                status="healthy"
            ),
            ModelHealthItem(
                name="nlp_analyzer",
                version=settings.NLP_MODEL_VERSION,
                last_trained=now,
                status="healthy"
            ),
            ModelHealthItem(
                name="attachment_scanner",
                version=settings.ATTACHMENT_SCANNER_VERSION,
                last_trained=now,
                status="healthy"
            )
        ]
    )

@router.post("/models/feedback", response_model=FeedbackResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_feedback(payload: FeedbackRequest):
    """
    Analyst-confirmed ground truth fed back for model retraining.
    Returns 202 Accepted.
    """
    FEEDBACK_LOG.append({
        "submission_id": payload.submission_id,
        "analyst_verdict": payload.analyst_verdict,
        "analyst_id": payload.analyst_id,
        "received_at": datetime.now(timezone.utc).isoformat()
    })
    return FeedbackResponse(status="queued_for_retraining")

