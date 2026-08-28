from fastapi import APIRouter, status
from app.schemas.aggregate import AggregateRequest, FraudAssessment
from app.ml.aggregator import aggregator_engine

router = APIRouter()

@router.post("/aggregate", response_model=FraudAssessment, status_code=status.HTTP_200_OK)
async def aggregate_results(payload: AggregateRequest):
    """
    Internal aggregator: Combines forensics results, classifier output,
    NLP analysis, link risk, and attachment scan results into the final FraudAssessment.
    """
    assessment = aggregator_engine.aggregate(payload)
    return assessment

