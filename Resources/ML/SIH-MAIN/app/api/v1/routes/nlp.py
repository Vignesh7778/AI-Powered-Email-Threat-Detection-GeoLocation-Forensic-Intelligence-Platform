from fastapi import APIRouter, status
from app.schemas.nlp import NLPAnalyzeRequest, NLPAnalyzeResponse
from app.ml.nlp_engine import nlp_engine

router = APIRouter()

@router.post("/nlp/analyze-content", response_model=NLPAnalyzeResponse, status_code=status.HTTP_200_OK)
async def analyze_content(payload: NLPAnalyzeRequest):
    """
    NLP pass over subject/body for social-engineering and urgency patterns.
    Returns urgency_score, impersonation_language_score, detected_patterns with character offset spans.
    """
    result = nlp_engine.analyze(subject=payload.subject, body_text=payload.body_text)
    return result

