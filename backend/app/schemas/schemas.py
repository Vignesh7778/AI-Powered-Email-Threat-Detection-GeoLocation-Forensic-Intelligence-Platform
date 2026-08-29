from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal, Tuple
from datetime import datetime

# ==========================================
# 🔐 Auth Schemas
# ==========================================

class UserLoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

class UserRegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    role: Optional[Literal["analyst", "admin", "investigator"]] = "analyst"
    tenant_id: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = 3600
    role: str
    user_id: str
    email: str
    tenant_id: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    expires_in: int = 3600

# ==========================================
# 📨 Shared Data Contracts (Authoritative §2)
# ==========================================

class RawBody(BaseModel):
    text_plain: Optional[str] = None
    text_html: Optional[str] = None

class AttachmentItem(BaseModel):
    filename: str
    content_type: str
    sha256: str
    size_bytes: int
    storage_ref: str

class SourceContext(BaseModel):
    ingested_via: Literal["imap", "upload", "forward", "api"] = "upload"
    tenant_id: str
    mailbox: Optional[str] = None

class EmailSubmission(BaseModel):
    submission_id: str
    received_at: str
    raw_headers: str
    raw_body: RawBody
    attachments: List[AttachmentItem] = Field(default_factory=list)
    source_context: SourceContext

# Forensics sub-schemas
class AuthResults(BaseModel):
    spf: Literal["pass", "fail", "softfail", "neutral", "none"] = "none"
    dkim: Literal["pass", "fail", "none"] = "none"
    dmarc: Literal["pass", "fail", "none"] = "none"
    alignment_ok: bool = True

class GeoLocation(BaseModel):
    country: str = "Unknown"
    region: str = "Unknown"
    city: str = "Unknown"
    isp: str = "Unknown"
    hosting_provider: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    asn: Optional[str] = None
    status: str = "verified"
    provenance: Optional[Dict[str, Any]] = None

class OriginInfo(BaseModel):
    originating_ip: Optional[str] = None
    geolocation: Optional[GeoLocation] = None
    infra_flags: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    reasoning: Optional[str] = None
    provenance: Optional[Dict[str, Any]] = None

class RelayHop(BaseModel):
    hop: int
    ip: Optional[str] = None
    hostname: Optional[str] = None
    timestamp: Optional[str] = None
    by_host: Optional[str] = None
    with_protocol: Optional[str] = None

class DomainIntel(BaseModel):
    sender_domain: str
    domain_age_days: Optional[int] = None
    registrar: Optional[str] = "Unknown / Unverified"
    mx_records: List[str] = Field(default_factory=list)
    lookalike_of: Optional[str] = None
    lookalike_score: float = 0.0
    dns_records: Optional[Dict[str, Any]] = None
    provenance: Optional[Dict[str, Any]] = None

class ThreatIndicator(BaseModel):
    type: str
    detail: str
    weight: float

class AttributionInfo(BaseModel):
    linked_campaign_id: Optional[str] = None
    related_submission_ids: List[str] = Field(default_factory=list)
    cluster_confidence: float = 0.0

class FraudAssessment(BaseModel):
    submission_id: str
    analyzed_at: str
    fraud_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: Literal["low", "medium", "high", "critical"]
    classification: Literal["legitimate", "suspicious", "impersonation", "phishing", "bec_fraud"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    auth_results: AuthResults
    origin: OriginInfo
    relay_path: List[RelayHop] = Field(default_factory=list)
    domain_intel: DomainIntel
    indicators: List[ThreatIndicator] = Field(default_factory=list)
    attribution: AttributionInfo
    groq_analysis: Optional[Dict[str, Any]] = None
    signal_breakdown: Optional[Dict[str, Any]] = None
    processing_mode: Literal["sync", "async"] = "sync"
    webhook_status: Literal["not_applicable", "pending", "delivered"] = "not_applicable"

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    submission_id: Optional[str] = None
    retryable: bool = False

# ==========================================
# 📥 Ingestion & Email List Schemas
# ==========================================

class EmailDetailResponse(BaseModel):
    submission_id: str
    status: Literal["queued", "analyzing", "complete", "failed"]
    ingested_at: str
    file_name: Optional[str] = None
    sha256_hash: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    subject: Optional[str] = None
    assessment: Optional[FraudAssessment] = None

class IngestResponse(BaseModel):
    submission_id: str
    status: Literal["queued", "analyzing", "complete", "failed"] = "queued"
    estimated_processing: Literal["sync", "async"] = "sync"
    detail: Optional[EmailDetailResponse] = None

class EmailListItem(BaseModel):
    submission_id: str
    risk_level: Optional[str] = None
    classification: Optional[str] = None
    fraud_score: Optional[float] = None
    received_at: str
    sender: Optional[str] = None
    recipient: Optional[str] = None
    subject: Optional[str] = None
    origin_ip: Optional[str] = None
    origin_asn: Optional[str] = None
    status: str

class EmailListResponse(BaseModel):
    results: List[EmailListItem]
    total: int
    page: int
    page_size: int

# ==========================================
# 📁 Case Management Schemas
# ==========================================

class CaseCreateRequest(BaseModel):
    title: str
    submission_ids: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    severity: Optional[Literal["low", "medium", "high", "critical"]] = "medium"

class CaseUpdateRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[Literal["open", "investigating", "escalated", "closed"]] = None
    severity: Optional[Literal["low", "medium", "high", "critical"]] = None
    notes: Optional[str] = None
    submission_ids: Optional[List[str]] = None

class CaseResponse(BaseModel):
    case_id: str
    title: str
    status: str
    severity: str
    notes: Optional[str] = None
    assigned_analyst: Optional[str] = None
    submission_ids: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str

# ==========================================
# 🚨 Alert Schemas
# ==========================================

class AlertResponse(BaseModel):
    alert_id: str
    submission_id: str
    severity: str
    fraud_score: float
    title: str
    reason: str
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    triggered_at: str

class AlertAcknowledgeResponse(BaseModel):
    alert_id: str
    acknowledged_by: str
    acknowledged_at: str

# ==========================================
# 📊 Dashboard Summary
# ==========================================

class OriginCountryStat(BaseModel):
    country: str
    count: int

class DashboardSummaryResponse(BaseModel):
    total_analyzed_24h: int
    high_risk_24h: int
    critical_risk_24h: int
    active_campaigns: int
    phishing_count: int
    bec_count: int
    impersonation_count: int
    legitimate_count: int
    top_origin_countries: List[OriginCountryStat]

# ==========================================
# 🔍 Forensics Specific Schemas
# ==========================================

class HeaderParseRequest(BaseModel):
    raw_headers: str

class HeaderAnomaly(BaseModel):
    type: Literal["forged_return_path", "relay_manipulation", "header_injection", "timestamp_inconsistency"]
    detail: str
    severity: Literal["low", "medium", "high"]

class HeaderParseResponse(BaseModel):
    message_id: str
    return_path: str
    reply_to: Optional[str] = None
    from_display: str
    from_address: str
    subject: Optional[str] = ""
    received_chain: List[RelayHop] = Field(default_factory=list)
    anomalies: List[HeaderAnomaly] = Field(default_factory=list)

class AuthValidateRequest(BaseModel):
    raw_headers: str
    sender_domain: str

class SPFDetails(BaseModel):
    result: Literal["pass", "fail", "softfail", "neutral", "none"]
    record: Optional[str] = None

class DKIMDetails(BaseModel):
    result: Literal["pass", "fail", "none"]
    selector: Optional[str] = None
    domain: Optional[str] = None

class DMARCDetails(BaseModel):
    result: Literal["pass", "fail", "none"]
    policy: Literal["none", "quarantine", "reject"] = "none"

class AuthValidateResponse(BaseModel):
    spf: SPFDetails
    dkim: DKIMDetails
    dmarc: DMARCDetails
    alignment_ok: bool

class OriginTraceRequest(BaseModel):
    received_chain: List[RelayHop]
    trusted_relay_ranges: List[str] = Field(default_factory=lambda: ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8"])

class OriginTraceResponse(BaseModel):
    originating_ip: Optional[str] = None
    confidence: float = 0.0
    reasoning: str = "Origin could not be reliably determined."
    provenance: Optional[Dict[str, Any]] = None

class GeoLookupRequest(BaseModel):
    ip: str

class InfraFlagsRequest(BaseModel):
    ip: str

class InfraFlagsResponse(BaseModel):
    ip: str
    flags: List[str]
    source_lists: List[str]

class DomainIntelRequest(BaseModel):
    domain: str

class LookalikeCheckRequest(BaseModel):
    domain: str
    compare_against: List[str] = Field(default_factory=lambda: ["paypal.com", "microsoft.com", "google.com", "apple.com", "amazon.com", "chase.com", "bankofamerica.com", "wellsfargo.com"])

class LookalikeCheckResponse(BaseModel):
    domain: str
    lookalike_of: Optional[str] = None
    technique: Optional[Literal["character_substitution", "homoglyph", "combosquatting", "tld_swap"]] = None
    score: float

class EvidenceLogRequest(BaseModel):
    submission_id: str
    actor: str
    action: str
    timestamp: Optional[str] = None
    integrity_hash: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class EvidenceLogResponse(BaseModel):
    log_id: str

class ChainEntry(BaseModel):
    log_id: str
    actor: str
    action: str
    timestamp: str
    integrity_hash: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ChainOfCustodyResponse(BaseModel):
    submission_id: str
    entries: List[ChainEntry]

# ==========================================
# 🧠 AI/ML Specific Schemas
# ==========================================

class DetectedPattern(BaseModel):
    type: Literal["payment_diversion", "fake_invoice", "credential_harvesting", "executive_impersonation", "urgency_cue"]
    excerpt_span: Tuple[int, int]
    confidence: float

class NLPAnalyzeRequest(BaseModel):
    subject: str
    body_text: str

class NLPAnalyzeResponse(BaseModel):
    urgency_score: float
    impersonation_language_score: float
    detected_patterns: List[DetectedPattern]
    language_model_version: str = "v2.3.1"

class LinkScore(BaseModel):
    displayed_text: str
    actual_url: str
    obfuscated: bool
    risk_score: float
    reasons: List[str]

class LinkExtractRequest(BaseModel):
    body_html: str

class LinkExtractResponse(BaseModel):
    links: List[LinkScore]

class AttachmentScanRequest(BaseModel):
    storage_ref: str
    sha256: str
    content_type: str

class AttachmentScanResponse(BaseModel):
    status: Literal["complete", "sandboxing"] = "complete"
    malware_score: float
    detected_type: str
    sandbox_report_ref: Optional[str] = None

class FeatureImportance(BaseModel):
    feature: str
    contribution: float

class MLFeatures(BaseModel):
    auth_results: AuthResults
    domain_age_days: Optional[int] = None
    lookalike_score: float
    infra_flags: List[str] = Field(default_factory=list)
    header_anomalies_count: int
    urgency_score: float
    impersonation_language_score: float
    link_risk_scores: List[float] = Field(default_factory=list)

class ClassifyRequest(BaseModel):
    submission_id: str
    features: MLFeatures

class ClassifyResponse(BaseModel):
    classification: Literal["legitimate", "suspicious", "impersonation", "phishing", "bec_fraud"]
    fraud_score: float
    confidence: float
    model_version: str = "v4.1.0"
    feature_importance: List[FeatureImportance]

# ==========================================
# 🕸️ Graph Intelligence Schemas
# ==========================================

class SharedIndicator(BaseModel):
    type: Literal["ip", "domain", "reply_to", "link_target"]
    value: str
    seen_in_count: int

class GraphCorrelateRequest(BaseModel):
    submission_id: str
    sender_domain: str
    originating_ip: str
    reply_to: Optional[str] = None
    link_domains: List[str] = Field(default_factory=list)

class GraphCorrelateResponse(BaseModel):
    linked_campaign_id: Optional[str] = None
    related_submission_ids: List[str] = Field(default_factory=list)
    cluster_confidence: float
    shared_indicators: List[SharedIndicator]

class GraphNode(BaseModel):
    id: str
    type: Literal["domain", "ip", "submission", "email", "campaign"]
    label: str

class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    weight: float = 1.0

class CampaignGraphResponse(BaseModel):
    campaign_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]

# ==========================================
# 🔒 Privacy Config Schema
# ==========================================

class PrivacyConfigSchema(BaseModel):
    retention_days: int = 180
    mask_pii_in_dashboard: bool = True
    auto_purge_low_risk: bool = False
