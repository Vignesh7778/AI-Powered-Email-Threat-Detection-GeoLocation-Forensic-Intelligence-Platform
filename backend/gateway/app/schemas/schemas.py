"""Pydantic schemas for all Gateway API request/response payloads."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: int = 3600
    role: Optional[str] = None
    mfa_required: bool = False
    mfa_token: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    expires_in: int = 3600


class MfaVerifyRequest(BaseModel):
    mfa_token: str
    code: str


class MfaVerifyResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = 3600
    role: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    email: str
    password: str
    role: Literal["analyst", "admin", "investigator"] = "analyst"
    department: Optional[str] = None
    mfa_enforced: bool = False


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: str
    role: str
    department: Optional[str]
    tenant_id: Optional[str]
    mfa_enabled: bool
    mfa_enforced: bool
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    role: Optional[Literal["analyst", "admin", "investigator"]] = None
    department: Optional[str] = None
    mfa_enforced: Optional[bool] = None
    is_active: Optional[bool] = None


# ---------------------------------------------------------------------------
# Submissions
# ---------------------------------------------------------------------------

class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    submission_id: str
    status: str
    ingested_at: datetime
    sender: Optional[str] = None
    subject: Optional[str] = None
    assessment: Optional[dict[str, Any]] = None
    flags: Optional[list[str]] = None


class SubmissionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    submission_id: str
    risk_level: Optional[str] = None
    classification: Optional[str] = None
    received_at: str
    sender: Optional[str] = None
    flags: Optional[list[str]] = None


class SubmissionListResponse(BaseModel):
    results: list[SubmissionListItem]
    total: int
    page: int
    page_size: int


class BulkActionRequest(BaseModel):
    submission_ids: list[str]
    action: Literal["mark_reviewed", "escalate_to_case", "mark_false_positive"]
    case_id: Optional[str] = None


class BulkActionResponse(BaseModel):
    updated: int
    action: str


class StatusUpdateRequest(BaseModel):
    status: Literal["dismissed", "escalated", "reviewing"]


class SelfReportResponse(BaseModel):
    submission_id: str
    status: str = "queued"


class VerdictRequest(BaseModel):
    analyst_verdict: Literal["legitimate", "phishing", "bec_fraud", "impersonation", "suspicious"]


class VerdictResponse(BaseModel):
    submission_id: str
    analyst_verdict: str
    queued_for_retraining: bool = True


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------

class CaseCreate(BaseModel):
    title: str
    submission_ids: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: str
    title: str
    status: str
    notes: Optional[str]
    assigned_to: Optional[str]
    tenant_id: Optional[str]
    submission_count: int
    created_at: datetime
    updated_at: datetime


class CaseDetailResponse(BaseModel):
    case_id: str
    title: str
    status: str
    notes: Optional[str]
    assigned_to: Optional[str]
    tenant_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    submissions: list[dict[str, Any]] = Field(default_factory=list)


class CaseUpdate(BaseModel):
    status: Optional[Literal["open", "investigating", "escalated", "closed"]] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class CommentCreate(BaseModel):
    body: str


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    comment_id: str
    case_id: str
    author_id: str
    body: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class DashboardSummary(BaseModel):
    total_analyzed_24h: int
    high_risk_24h: int
    active_campaigns: int
    top_origin_countries: list[dict[str, Any]]
    avg_time_to_triage_seconds: Optional[float]
    high_confidence_fraud_open: int


class TrendPoint(BaseModel):
    date: str
    total: int
    by_classification: dict[str, int]


class TrendResponse(BaseModel):
    points: list[TrendPoint]


class TopDomain(BaseModel):
    domain: str
    count: int


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: str
    submission_id: str
    fraud_score: float
    risk_level: str
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    created_at: datetime


class AcknowledgeResponse(BaseModel):
    alert_id: str
    acknowledged_by: str
    acknowledged_at: datetime


# ---------------------------------------------------------------------------
# Geo
# ---------------------------------------------------------------------------

class HeatmapPoint(BaseModel):
    country: str
    region: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    count: int
    avg_confidence: float


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: str
    submission_id: Optional[str]
    tenant_id: str
    format: str
    type: str
    storage_ref: Optional[str]
    exported_by: Optional[str]
    exported_at: datetime


class ScheduleCreate(BaseModel):
    frequency: Literal["daily", "weekly", "monthly"]
    format: Literal["pdf", "json"] = "json"
    recipients: list[str] = Field(default_factory=list)
    filter_params: dict[str, Any] = Field(default_factory=dict)


class ScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    schedule_id: str
    tenant_id: str
    frequency: str
    format: str
    recipients_json: str
    filter_params_json: str
    created_at: datetime

    def model_post_init(self, __context: Any) -> None:
        # expose parsed fields (for convenience, callers can use .recipients)
        object.__setattr__(self, "recipients", json.loads(self.recipients_json or "[]"))
        object.__setattr__(self, "filter_params", json.loads(self.filter_params_json or "{}"))


# ---------------------------------------------------------------------------
# Rules / Watchlists
# ---------------------------------------------------------------------------

class ThresholdRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    alert_threshold: float
    auto_quarantine_threshold: float
    updated_at: datetime


class ThresholdUpdate(BaseModel):
    alert_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    auto_quarantine_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)


class WatchlistEntry(BaseModel):
    value: str


class WatchlistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    list_type: str
    value: str
    added_by: Optional[str]
    created_at: datetime


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

class AuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: str
    actor_id: Optional[str]
    action: str
    target_type: Optional[str]
    target_id: Optional[str]
    submission_id: Optional[str]
    case_id: Optional[str]
    ip_address: Optional[str]
    timestamp: datetime


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class MailboxCreate(BaseModel):
    mailbox_address: str
    domain: Optional[str] = None


class MailboxRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    integration_id: str
    tenant_id: str
    mailbox_address: str
    domain: Optional[str]
    is_active: bool
    created_at: datetime


class NotificationPrefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email_alerts: bool
    sms_alerts: bool
    min_risk_level: str
    updated_at: datetime


class NotificationPrefUpdate(BaseModel):
    email_alerts: Optional[bool] = None
    sms_alerts: Optional[bool] = None
    min_risk_level: Optional[str] = None


class PrivacyConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    retention_days: int
    mask_pii_in_dashboard: bool
    auto_purge_low_risk: bool
    updated_at: datetime


class PrivacyConfigUpdate(BaseModel):
    retention_days: Optional[int] = Field(None, ge=1)
    mask_pii_in_dashboard: Optional[bool] = None
    auto_purge_low_risk: Optional[bool] = None


class SavedViewCreate(BaseModel):
    name: str
    filter_params: dict[str, Any] = Field(default_factory=dict)


class SavedViewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    view_id: str
    user_id: str
    name: str
    filter_params_json: str
    created_at: datetime

    @property
    def filter_params(self) -> dict:
        return json.loads(self.filter_params_json or "{}")
