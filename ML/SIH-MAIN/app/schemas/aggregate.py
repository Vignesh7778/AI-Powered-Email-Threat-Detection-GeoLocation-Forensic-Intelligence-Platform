from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ModuleResults(BaseModel):
    forensics: Optional[Dict[str, Any]] = None
    nlp: Optional[Dict[str, Any]] = None
    links: Optional[Dict[str, Any]] = None
    classify: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, Any]]] = None

class AggregateRequest(BaseModel):
    submission_id: str
    forensics_results: Optional[Dict[str, Any]] = Field(default_factory=dict)
    classify_result: Optional[Dict[str, Any]] = Field(default_factory=dict)
    nlp_result: Optional[Dict[str, Any]] = None
    links_result: Optional[Dict[str, Any]] = None
    attachment_results: Optional[List[Dict[str, Any]]] = None

class ScoreBreakdown(BaseModel):
    forensics_risk: float
    nlp_risk: float
    link_risk: float
    attachment_risk: float
    classifier_score: float

class FraudAssessment(BaseModel):
    submission_id: str
    verdict: str = Field(..., description="Overall verdict: PASS, SUSPICIOUS, BLOCKED, REVIEW_REQUIRED")
    fraud_score: float = Field(..., ge=0.0, le=1.0, description="Aggregated 0-1 fraud probability score")
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    primary_threat: str = Field(..., description="Classification category")
    confidence: float = Field(..., ge=0.0, le=1.0)
    score_breakdown: ScoreBreakdown
    key_findings: List[str]
    recommended_actions: List[str]
    evaluated_at: str
    pipeline_version: str = "v4.1.0"

