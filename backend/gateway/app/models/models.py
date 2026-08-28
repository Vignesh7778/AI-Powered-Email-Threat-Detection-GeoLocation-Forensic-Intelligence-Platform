"""SQLAlchemy ORM models for the Gateway database (SQLite)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Users & Auth
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="analyst")  # analyst|admin|investigator
    department = Column(String, nullable=True)
    tenant_id = Column(String, nullable=True, index=True)
    mfa_secret = Column(String, nullable=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_enforced = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    mfa_tokens = relationship("MfaToken", back_populates="user", cascade="all, delete-orphan")
    saved_views = relationship("SavedView", back_populates="user", cascade="all, delete-orphan")
    notification_pref = relationship("NotificationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")


class MfaToken(Base):
    """Short-lived token issued after password check when MFA is required."""
    __tablename__ = "mfa_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    mfa_token = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=_now)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)

    user = relationship("User", back_populates="mfa_tokens")


# ---------------------------------------------------------------------------
# Email Submissions & Assessments
# ---------------------------------------------------------------------------

class Submission(Base):
    __tablename__ = "submissions"

    submission_id = Column(String, primary_key=True, default=_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    raw_storage_ref = Column(String, nullable=True)  # path to .eml on disk
    status = Column(String, default="queued")         # queued|analyzing|complete|failed|dismissed|escalated
    source = Column(String, default="upload")          # upload|imap|forward|api|self_report
    sender = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    ingested_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    assessment = relationship("Assessment", back_populates="submission", uselist=False, cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="submission", cascade="all, delete-orphan")
    custody_entries = relationship("ChainOfCustody", back_populates="submission", cascade="all, delete-orphan")
    audit_entries = relationship("AuditLog", back_populates="submission")
    reports = relationship("Report", back_populates="submission")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(String, ForeignKey("submissions.submission_id"), unique=True, nullable=False)
    assessment_json = Column(Text, nullable=False)   # full FraudAssessment as JSON string
    risk_level = Column(String, nullable=True)        # low|medium|high|critical
    classification = Column(String, nullable=True)    # legitimate|suspicious|impersonation|phishing|bec_fraud
    fraud_score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    flags = Column(Text, nullable=True)              # JSON list: ["spoofed_domain","dkim_fail",...]
    narrative_summary = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, default=_now)

    submission = relationship("Submission", back_populates="assessment")


# ---------------------------------------------------------------------------
# Cases & Comments
# ---------------------------------------------------------------------------

class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String, primary_key=True, default=_uuid)
    title = Column(String, nullable=False)
    status = Column(String, default="open")   # open|investigating|escalated|closed
    notes = Column(Text, nullable=True)
    assigned_to = Column(String, ForeignKey("users.user_id"), nullable=True)
    tenant_id = Column(String, nullable=True, index=True)
    submission_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    case_submissions = relationship("CaseSubmission", back_populates="case", cascade="all, delete-orphan")
    comments = relationship("CaseComment", back_populates="case", cascade="all, delete-orphan")
    assignee = relationship("User", foreign_keys=[assigned_to])


class CaseSubmission(Base):
    __tablename__ = "case_submissions"

    case_id = Column(String, ForeignKey("cases.case_id"), primary_key=True)
    submission_id = Column(String, ForeignKey("submissions.submission_id"), primary_key=True)

    case = relationship("Case", back_populates="case_submissions")


class CaseComment(Base):
    __tablename__ = "case_comments"

    comment_id = Column(String, primary_key=True, default=_uuid)
    case_id = Column(String, ForeignKey("cases.case_id"), nullable=False)
    author_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_now)

    case = relationship("Case", back_populates="comments")
    author = relationship("User", foreign_keys=[author_id])


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String, primary_key=True, default=_uuid)
    submission_id = Column(String, ForeignKey("submissions.submission_id"), nullable=False)
    fraud_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    acknowledged_by = Column(String, ForeignKey("users.user_id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now)

    submission = relationship("Submission", back_populates="alerts")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])


# ---------------------------------------------------------------------------
# Evidence / Chain of Custody
# ---------------------------------------------------------------------------

class ChainOfCustody(Base):
    __tablename__ = "chain_of_custody"

    log_id = Column(String, primary_key=True, default=_uuid)
    submission_id = Column(String, ForeignKey("submissions.submission_id"), nullable=False)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=_now)
    metadata_json = Column(Text, nullable=True)   # optional JSON dict

    submission = relationship("Submission", back_populates="custody_entries")


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id = Column(String, primary_key=True, default=_uuid)
    actor_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    action = Column(String, nullable=False)
    target_type = Column(String, nullable=True)  # submission|case|alert|user|report
    target_id = Column(String, nullable=True)
    submission_id = Column(String, ForeignKey("submissions.submission_id"), nullable=True)
    case_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=_now)

    actor = relationship("User", foreign_keys=[actor_id])
    submission = relationship("Submission", back_populates="audit_entries")


# ---------------------------------------------------------------------------
# Reports & Schedules
# ---------------------------------------------------------------------------

class Report(Base):
    __tablename__ = "reports"

    report_id = Column(String, primary_key=True, default=_uuid)
    submission_id = Column(String, ForeignKey("submissions.submission_id"), nullable=True)
    tenant_id = Column(String, nullable=False, index=True)
    format = Column(String, default="json")       # pdf|json
    type = Column(String, default="on_demand")    # on_demand|scheduled
    storage_ref = Column(String, nullable=True)
    exported_by = Column(String, ForeignKey("users.user_id"), nullable=True)
    exported_at = Column(DateTime, default=_now)

    submission = relationship("Submission", back_populates="reports")
    exporter = relationship("User", foreign_keys=[exported_by])


class ReportSchedule(Base):
    __tablename__ = "report_schedules"

    schedule_id = Column(String, primary_key=True, default=_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    frequency = Column(String, nullable=False)   # daily|weekly|monthly
    format = Column(String, default="json")
    recipients_json = Column(Text, default="[]")
    filter_params_json = Column(Text, default="{}")
    created_by = Column(String, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=_now)

    creator = relationship("User", foreign_keys=[created_by])


# ---------------------------------------------------------------------------
# Tenant Configuration — Thresholds, Watchlists, Privacy, Mailboxes
# ---------------------------------------------------------------------------

class TenantThreshold(Base):
    __tablename__ = "tenant_thresholds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, unique=True, nullable=False, index=True)
    alert_threshold = Column(Float, default=0.6)
    auto_quarantine_threshold = Column(Float, default=0.9)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    list_type = Column(String, nullable=False)  # protected_brands|blocked_domains|allowed_domains|blocked_ips
    value = Column(String, nullable=False)
    added_by = Column(String, ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime, default=_now)

    __table_args__ = (
        UniqueConstraint("tenant_id", "list_type", "value", name="uq_watchlist_entry"),
    )

    adder = relationship("User", foreign_keys=[added_by])


class PrivacyConfig(Base):
    __tablename__ = "privacy_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, unique=True, nullable=False)
    retention_days = Column(Integer, default=180)
    mask_pii_in_dashboard = Column(Boolean, default=True)
    auto_purge_low_risk = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class MailboxIntegration(Base):
    __tablename__ = "mailbox_integrations"

    integration_id = Column(String, primary_key=True, default=_uuid)
    tenant_id = Column(String, nullable=False, index=True)
    mailbox_address = Column(String, nullable=False)
    domain = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)


# ---------------------------------------------------------------------------
# User Preferences & Saved Views
# ---------------------------------------------------------------------------

class SavedView(Base):
    __tablename__ = "saved_views"

    view_id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    name = Column(String, nullable=False)
    filter_params_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=_now)

    user = relationship("User", back_populates="saved_views")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), unique=True, nullable=False)
    email_alerts = Column(Boolean, default=True)
    sms_alerts = Column(Boolean, default=False)
    min_risk_level = Column(String, default="high")
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    user = relationship("User", back_populates="notification_pref")
