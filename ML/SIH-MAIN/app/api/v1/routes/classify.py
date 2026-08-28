from fastapi import APIRouter, status
from app.schemas.classify import ClassifyRequest, ClassifyResponse
from app.ml.classifier_model import classifier_model

router = APIRouter()

@router.post("/classify", response_model=ClassifyResponse, status_code=status.HTTP_200_OK)
async def classify_features(payload: ClassifyRequest):
    """
    Core Fraud Classifier: takes assembled features (forensics, NLP, link scores)
    and returns classification, fraud_score, confidence, and feature importance contributions.
    """
    result = classifier_model.classify(
        submission_id=payload.submission_id,
        features=payload.features
    )
    return result

