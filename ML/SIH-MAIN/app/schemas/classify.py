from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict

ClassificationType = Literal[
    "legitimate",
    "suspicious",
    "impersonation",
    "phishing",
    "bec_fraud"
]

class AuthResults(BaseModel):
    spf: Optional[str] = Field("none", description="SPF verification result e.g. pass, fail, softfail, neutral, none")
    dkim: Optional[str] = Field("none", description="DKIM verification result e.g. pass, fail, none")
    dmarc: Optional[str] = Field("none", description="DMARC verification result e.g. pass, fail, none")

class Features(BaseModel):
    auth_results: AuthResults
    domain_age_days: int = Field(..., ge=0, description="Age of sender domain in days")
    lookalike_score: float = Field(..., ge=0.0, le=1.0, description="Typosquatting/lookalike similarity score")
    infra_flags: List[str] = Field(default_factory=list, description="Infrastructure flags e.g. vpn, tor, hosting, dynamic_ip")
    header_anomalies_count: int = Field(..., ge=0, description="Count of anomalies detected in email headers")
    urgency_score: float = Field(..., ge=0.0, le=1.0, description="Urgency score from NLP analysis")
    impersonation_language_score: float = Field(..., ge=0.0, le=1.0, description="Impersonation score from NLP analysis")
    link_risk_scores: List[float] = Field(default_factory=list, description="List of risk scores for extracted links")

class ClassifyRequest(BaseModel):
    submission_id: str = Field(..., description="Unique submission UUID")
    features: Features

class FeatureImportance(BaseModel):
    feature: str
    contribution: float

class ClassifyResponse(BaseModel):
    classification: ClassificationType
    fraud_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str = "v4.1.0"
    feature_importance: List[FeatureImportance]

