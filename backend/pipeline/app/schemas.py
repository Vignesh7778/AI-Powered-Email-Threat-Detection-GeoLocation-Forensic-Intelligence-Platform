from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class RawBody(BaseModel):
    text_plain: Optional[str] = None
    text_html: Optional[str] = None


class Attachment(BaseModel):
    filename: str
    content_type: str
    sha256: str = Field(min_length=32, max_length=128)
    size_bytes: int = Field(ge=0)
    storage_ref: str


class SourceContext(BaseModel):
    ingested_via: Literal["imap", "upload", "forward", "api", "self_report"]
    tenant_id: str
    mailbox: Optional[str] = None


class EmailSubmission(BaseModel):
    submission_id: str
    received_at: datetime
    raw_headers: str
    raw_body: RawBody
    attachments: list[Attachment] = Field(default_factory=list)
    source_context: SourceContext


class AuthResults(BaseModel):
    spf: Literal["pass", "fail", "softfail", "none", "neutral"] = "none"
    dkim: Literal["pass", "fail", "none"] = "none"
    dmarc: Literal["pass", "fail", "none"] = "none"
    alignment_ok: bool = False


class RelayHop(BaseModel):
    hop: int
    ip: Optional[str] = None
    hostname: Optional[str] = None
    timestamp: Optional[datetime] = None


class Geolocation(BaseModel):
    country: str
    region: str
    city: str
    isp: str
    hosting_provider: Optional[str] = None
    lat: float
    lon: float


class Origin(BaseModel):
    originating_ip: str
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    geolocation: Geolocation
    infra_flags: list[str] = Field(default_factory=list)


class DomainIntel(BaseModel):
    sender_domain: str
    registrar: str
    created_date: datetime
    domain_age_days: int
    mx_records: list[str] = Field(default_factory=list)
    lookalike_of: Optional[str] = None
    lookalike_score: float = Field(ge=0, le=1)


class Indicator(BaseModel):
    type: str
    detail: str
    weight: float = Field(ge=0, le=1)


class Attribution(BaseModel):
    linked_campaign_id: Optional[str] = None
    related_submission_ids: list[str] = Field(default_factory=list)
    cluster_confidence: float = Field(ge=0, le=1)
    shared_indicators: list[dict[str, object]] = Field(default_factory=list)


class FraudAssessment(BaseModel):
    submission_id: str
    analyzed_at: datetime
    fraud_score: float = Field(ge=0, le=1)
    risk_level: Literal["low", "medium", "high", "critical"]
    classification: Literal["legitimate", "suspicious", "impersonation", "phishing", "bec_fraud"]
    confidence: float = Field(ge=0, le=1)
    model_version: str
    auth_results: AuthResults
    origin: Origin
    relay_path: list[RelayHop]
    domain_intel: DomainIntel
    indicators: list[Indicator]
    attribution: Attribution
    narrative_summary: str
    processing_mode: Literal["sync", "async"]
    webhook_status: Literal["not_applicable", "pending", "delivered"] = "not_applicable"


class AnalyzeAccepted(BaseModel):
    submission_id: str
    status: Literal["processing"] = "processing"
    estimated_processing: Literal["async"] = "async"


class AnalysisRecord(BaseModel):
    submission_id: str
    status: Literal["processing", "complete", "failed"]
    assessment: Optional[FraudAssessment] = None
    error: Optional[str] = None


class EvidenceEntry(BaseModel):
    submission_id: str
    action: str
    actor: str = "system:pipeline"
    timestamp: datetime
    metadata: dict[str, str] = Field(default_factory=dict)
