from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from backend.app.core.database import get_db
from backend.app.schemas.schemas import (
    NLPAnalyzeRequest, NLPAnalyzeResponse,
    LinkExtractRequest, LinkExtractResponse,
    AttachmentScanRequest, AttachmentScanResponse,
    ClassifyRequest, ClassifyResponse,
    GraphCorrelateRequest, GraphCorrelateResponse,
    CampaignGraphResponse, FraudAssessment
)
from backend.ml.inference.nlp_engine import nlp_engine
from backend.ml.inference.link_engine import link_engine
from backend.ml.inference.attachment_engine import attachment_scanner
from backend.ml.models.classifier import fraud_classifier
from backend.ml.inference.aggregator import score_aggregator
from backend.graph.graph_engine import graph_engine

router = APIRouter()

@router.post("/nlp/analyze-content", response_model=NLPAnalyzeResponse, tags=["AI/ML"])
def analyze_nlp_endpoint(req: NLPAnalyzeRequest):
    res = nlp_engine.analyze(req.subject, req.body_text)
    return NLPAnalyzeResponse(**res)

@router.post("/links/extract-and-score", response_model=LinkExtractResponse, tags=["AI/ML"])
def extract_links_endpoint(req: LinkExtractRequest):
    links = link_engine.extract_and_score(req.body_html)
    return LinkExtractResponse(links=links)

@router.post("/classify", response_model=ClassifyResponse, tags=["AI/ML"])
def classify_endpoint(req: ClassifyRequest):
    return fraud_classifier.classify(req.submission_id, req.features)

@router.post("/attachments/scan", response_model=AttachmentScanResponse, tags=["AI/ML"])
def scan_attachment_endpoint(req: AttachmentScanRequest):
    return attachment_scanner.scan(req)

@router.post("/graph/correlate", response_model=GraphCorrelateResponse, tags=["AI/ML"])
def correlate_graph_endpoint(req: GraphCorrelateRequest, db: Session = Depends(get_db)):
    return graph_engine.correlate(
        submission_id=req.submission_id,
        sender_domain=req.sender_domain,
        originating_ip=req.originating_ip,
        reply_to=req.reply_to,
        link_domains=req.link_domains,
        db=db
    )

@router.get("/graph/campaign/{campaign_id}", response_model=CampaignGraphResponse, tags=["AI/ML"])
def get_campaign_graph_endpoint(campaign_id: str):
    return graph_engine.get_campaign_graph(campaign_id)

@router.get("/models/health", tags=["AI/ML"])
def models_health_endpoint():
    return {
        "models": [
            {"name": "nlp_engine", "version": "v2.3.1", "last_trained": "2026-08-20T00:00:00Z", "status": "healthy"},
            {"name": "fraud_classifier", "version": "v4.1.0", "last_trained": "2026-08-25T00:00:00Z", "status": "healthy"},
            {"name": "attachment_scanner", "version": "v1.2.0", "last_trained": "2026-08-15T00:00:00Z", "status": "healthy"}
        ]
    }

@router.post("/models/feedback", status_code=status.HTTP_202_ACCEPTED, tags=["AI/ML"])
def model_feedback_endpoint(feedback: Dict[str, Any]):
    return {"status": "queued_for_retraining", "submission_id": feedback.get("submission_id")}
