from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.schemas.classify import Features, AuthResults
from app.schemas.attachment import AttachmentScanRequest
from app.schemas.aggregate import FraudAssessment
from app.ml.nlp_engine import nlp_engine
from app.ml.link_engine import link_engine
from app.ml.classifier_model import classifier_model
from app.ml.attachment_engine import attachment_scanner
from app.ml.aggregator import aggregator_engine
from app.schemas.aggregate import AggregateRequest

router = APIRouter()

class PipelineEvaluateRequest(BaseModel):
    submission_id: str
    subject: str
    body_text: str
    body_html: Optional[str] = None
    forensics: Optional[Dict[str, Any]] = None
    attachments: Optional[List[AttachmentScanRequest]] = None

class PipelineEvaluateResponse(BaseModel):
    submission_id: str
    nlp_analysis: Dict[str, Any]
    links_analysis: Dict[str, Any]
    classifier_result: Dict[str, Any]
    attachments_analysis: List[Dict[str, Any]]
    final_assessment: FraudAssessment

@router.post("/pipeline/evaluate", response_model=PipelineEvaluateResponse, status_code=status.HTTP_200_OK)
async def evaluate_pipeline(payload: PipelineEvaluateRequest):
    """
    End-to-end evaluation pipeline running all AI/ML modules in dependency order:
    NLP -> Links -> Attachments -> Classifier -> Aggregate.
    """
    # 1. NLP Analysis
    nlp_res = nlp_engine.analyze(subject=payload.subject, body_text=payload.body_text)

    # 2. Link Analysis
    html_to_scan = payload.body_html or payload.body_text
    link_scores = link_engine.extract_and_score(body_html=html_to_scan)
    link_res = {"links": [l.model_dump() for l in link_scores]}
    link_risk_scores = [l.risk_score for l in link_scores]

    # 3. Attachment Scan
    att_res_list = []
    if payload.attachments:
        for att in payload.attachments:
            scan_res = attachment_scanner.scan(att)
            att_res_list.append(scan_res.model_dump())

    # 4. Assemble Features for Core Classifier
    forensics = payload.forensics or {}
    auth_data = forensics.get("auth_results", {})
    auth_results = AuthResults(
        spf=auth_data.get("spf", "none"),
        dkim=auth_data.get("dkim", "none"),
        dmarc=auth_data.get("dmarc", "none")
    )

    assembled_features = Features(
        auth_results=auth_results,
        domain_age_days=int(forensics.get("domain_age_days", 365)),
        lookalike_score=float(forensics.get("lookalike_score", 0.0)),
        infra_flags=forensics.get("infra_flags", []),
        header_anomalies_count=int(forensics.get("header_anomalies_count", 0)),
        urgency_score=nlp_res["urgency_score"],
        impersonation_language_score=nlp_res["impersonation_language_score"],
        link_risk_scores=link_risk_scores
    )

    classify_res = classifier_model.classify(
        submission_id=payload.submission_id,
        features=assembled_features
    )

    # 5. Final Aggregation
    agg_req = AggregateRequest(
        submission_id=payload.submission_id,
        forensics_results=forensics,
        classify_result=classify_res.model_dump(),
        nlp_result=nlp_res,
        links_result=link_res,
        attachment_results=att_res_list
    )
    final_assessment = aggregator_engine.aggregate(agg_req)

    return PipelineEvaluateResponse(
        submission_id=payload.submission_id,
        nlp_analysis=nlp_res,
        links_analysis=link_res,
        classifier_result=classify_res.model_dump(),
        attachments_analysis=att_res_list,
        final_assessment=final_assessment
    )

