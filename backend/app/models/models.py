import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Table
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def get_utc_now():
    return datetime.now(timezone.utc)

# User Table
class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="analyst", nullable=False)  # analyst, admin, investigator
    tenant_id = Column(String(36), default=generate_uuid, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_utc_now)

# Email Submissions Table
class Submission(Base):
    __tablename__ = "submissions"

    submission_id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), index=True, nullable=False)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, default=0)
    raw_storage_ref = Column(String(500), nullable=True)
    sha256_hash = Column(String(64), index=True, nullable=False)
    sender = Column(String(255), nullable=True)
    subject = Column(String(500), nullable=True)
    recipient = Column(String(255), nullable=True)
    source = Column(String(50), default="upload")  # upload, imap, forward, api
    mailbox = Column(String(255), nullable=True)
    status = Column(String(50), default="queued")  # queued, analyzing, complete, failed
    received_at = Column(DateTime, default=get_utc_now)
    ingested_at = Column(DateTime, default=get_utc_now)

    # Relationships
    assessment = relationship("Assessment", back_populates="submission", uselist=False, cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="submission", cascade="all, delete-orphan")
    chain_entries = relationship("ChainOfCustody", back_populates="submission", cascade="all, delete-orphan")

# Fraud Assessments Table
class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.submission_id"), unique=True, index=True, nullable=False)
    fraud_score = Column(Float, nullable=False)
    risk_level = Column(String(50), nullable=False)  # low, medium, high, critical
    classification = Column(String(50), nullable=False)  # legitimate, suspicious, impersonation, phishing, bec_fraud
    confidence = Column(Float, nullable=False)
    raw_assessment = Column(JSON, nullable=False)
    analyzed_at = Column(DateTime, default=get_utc_now)

    # Relationships
    submission = relationship("Submission", back_populates="assessment")

# Cases Table
class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    status = Column(String(50), default="open")  # open, investigating, escalated, closed
    severity = Column(String(50), default="medium")  # low, medium, high, critical
    notes = Column(Text, nullable=True)
    assigned_analyst = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    # Relationships
    case_submissions = relationship("CaseSubmission", back_populates="case", cascade="all, delete-orphan")

# Case Submissions Link Table
class CaseSubmission(Base):
    __tablename__ = "case_submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("cases.case_id"), index=True, nullable=False)
    submission_id = Column(String(36), ForeignKey("submissions.submission_id"), index=True, nullable=False)
    added_at = Column(DateTime, default=get_utc_now)

    # Relationships
    case = relationship("Case", back_populates="case_submissions")
    submission = relationship("Submission")

# Alerts Table
class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.submission_id"), index=True, nullable=False)
    severity = Column(String(50), nullable=False)  # low, medium, high, critical
    fraud_score = Column(Float, nullable=False)
    title = Column(String(255), nullable=False)
    reason = Column(Text, nullable=False)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(255), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    triggered_at = Column(DateTime, default=get_utc_now)

    # Relationships
    submission = relationship("Submission", back_populates="alerts")

# Chain of Custody Table
class ChainOfCustody(Base):
    __tablename__ = "chain_of_custody"

    log_id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.submission_id"), index=True, nullable=False)
    actor = Column(String(255), nullable=False)
    action = Column(String(255), nullable=False)
    integrity_hash = Column(String(64), nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=get_utc_now)

    # Relationships
    submission = relationship("Submission", back_populates="chain_entries")

# Tenant Privacy Configuration Table
class PrivacyConfig(Base):
    __tablename__ = "privacy_configs"

    tenant_id = Column(String(36), primary_key=True)
    retention_days = Column(Integer, default=180)
    mask_pii_in_dashboard = Column(Boolean, default=True)
    auto_purge_low_risk = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

# Campaigns Table
class Campaign(Base):
    __tablename__ = "campaigns"

    campaign_id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    threat_actor = Column(String(255), nullable=True)
    status = Column(String(50), default="active")  # active, mitigated, archived
    description = Column(Text, nullable=True)
    indicators = Column(JSON, default=list)
    first_seen = Column(DateTime, default=get_utc_now)
    last_seen = Column(DateTime, default=get_utc_now)
