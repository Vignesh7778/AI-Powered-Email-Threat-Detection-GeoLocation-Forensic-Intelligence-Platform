-- ==============================================================================
-- 🛡️ TraceX — AI-Powered Email Threat Detection & Forensic Intelligence Platform
-- PostgreSQL / Supabase Complete DDL Schema & Initialization Script
-- ==============================================================================

-- Enable UUID & Crypto extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================================================
-- 1. USERS & ANALYSTS TABLE
-- ==============================================================================
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'analyst', -- analyst, admin, investigator
    tenant_id VARCHAR(36) NOT NULL DEFAULT gen_random_uuid()::text,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ==============================================================================
-- 2. EMAIL SUBMISSIONS TABLE
-- ==============================================================================
CREATE TABLE IF NOT EXISTS submissions (
    submission_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    tenant_id VARCHAR(36) NOT NULL,
    file_name VARCHAR(255),
    file_size INTEGER DEFAULT 0,
    raw_storage_ref VARCHAR(500),
    sha256_hash VARCHAR(64) NOT NULL,
    sender VARCHAR(255),
    subject VARCHAR(500),
    recipient VARCHAR(255),
    source VARCHAR(50) DEFAULT 'upload', -- upload, imap, forward, api
    mailbox VARCHAR(255),
    status VARCHAR(50) DEFAULT 'queued', -- queued, analyzing, complete, failed
    received_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_submissions_tenant ON submissions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_submissions_sha256 ON submissions(sha256_hash);
CREATE INDEX IF NOT EXISTS idx_submissions_sender ON submissions(sender);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);

-- ==============================================================================
-- 3. FRAUD & FORENSIC ASSESSMENTS TABLE
-- ==============================================================================
CREATE TABLE IF NOT EXISTS assessments (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    submission_id VARCHAR(36) UNIQUE NOT NULL REFERENCES submissions(submission_id) ON DELETE CASCADE,
    fraud_score FLOAT NOT NULL,
    risk_level VARCHAR(50) NOT NULL, -- low, medium, high, critical
    classification VARCHAR(50) NOT NULL, -- legitimate, suspicious, impersonation, phishing, bec_fraud
    confidence FLOAT NOT NULL,
    raw_assessment JSONB NOT NULL,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_assessments_sub_id ON assessments(submission_id);
CREATE INDEX IF NOT EXISTS idx_assessments_risk ON assessments(risk_level);
CREATE INDEX IF NOT EXISTS idx_assessments_class ON assessments(classification);

-- ==============================================================================
-- 4. INCIDENT & CASE DESK TABLE
-- ==============================================================================
CREATE TABLE IF NOT EXISTS cases (
    case_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'open', -- open, investigating, contained, resolved, closed
    severity VARCHAR(50) DEFAULT 'medium', -- low, medium, high, critical
    notes TEXT,
    assigned_analyst VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_cases_severity ON cases(severity);

-- ==============================================================================
-- 5. CASE-SUBMISSION JUNCTION TABLE
-- ==============================================================================
CREATE TABLE IF NOT EXISTS case_submissions (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    case_id VARCHAR(36) NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    submission_id VARCHAR(36) NOT NULL REFERENCES submissions(submission_id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_case_subs_case ON case_submissions(case_id);
CREATE INDEX IF NOT EXISTS idx_case_subs_sub ON case_submissions(submission_id);

-- ==============================================================================
-- 6. THREAT ALERTS STREAM TABLE
-- ==============================================================================
CREATE TABLE IF NOT EXISTS alerts (
    alert_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    submission_id VARCHAR(36) NOT NULL REFERENCES submissions(submission_id) ON DELETE CASCADE,
    severity VARCHAR(50) NOT NULL, -- low, medium, high, critical
    fraud_score FLOAT NOT NULL,
    title VARCHAR(255) NOT NULL,
    reason TEXT NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_alerts_sub ON alerts(submission_id);
CREATE INDEX IF NOT EXISTS idx_alerts_ack ON alerts(acknowledged);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);

-- ==============================================================================
-- 7. CRYPTOGRAPHIC CHAIN OF CUSTODY TABLE
-- ==============================================================================
CREATE TABLE IF NOT EXISTS chain_of_custody (
    log_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    submission_id VARCHAR(36) NOT NULL REFERENCES submissions(submission_id) ON DELETE CASCADE,
    actor VARCHAR(255) NOT NULL,
    action VARCHAR(255) NOT NULL,
    integrity_hash VARCHAR(64),
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_custody_sub ON chain_of_custody(submission_id);
CREATE INDEX IF NOT EXISTS idx_custody_time ON chain_of_custody(timestamp);

-- ==============================================================================
-- 8. THREAT CAMPAIGNS TABLE
-- ==============================================================================
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(255) NOT NULL,
    threat_actor VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active', -- active, mitigated, archived
    description TEXT,
    indicators JSONB DEFAULT '[]'::jsonb,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- 9. PRIVACY & GOVERNANCE CONFIG TABLE
-- ==============================================================================
CREATE TABLE IF NOT EXISTS privacy_configs (
    tenant_id VARCHAR(36) PRIMARY KEY,
    retention_days INTEGER DEFAULT 180,
    mask_pii_in_dashboard BOOLEAN DEFAULT TRUE,
    auto_purge_low_risk BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- 10. SEED INITIAL DATA (Analyst User, Campaigns & Multi-Stage Cases)
-- ==============================================================================

-- Default Analyst Account (analyst@org.gov / Analyst@2026!)
INSERT INTO users (user_id, email, hashed_password, full_name, role, is_active)
VALUES (
    'u-analyst-default',
    'analyst@org.gov',
    '$2b$12$e8Y60kF9FwB1eEw.0w1wreY.aE3vVwGzRj9Z4f5U8.N3wK0L3qRte',
    'Senior Digital Forensics Analyst',
    'analyst',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- Initial Threat Campaigns
INSERT INTO campaigns (campaign_id, name, threat_actor, status, description, indicators)
VALUES 
(
    'camp-fin-001',
    'FinTarget BEC Campaign (ShadowInvoice)',
    'UNC2165 / Financial Fraud Nexus',
    'active',
    'Coordinated business email compromise campaign targeting corporate accounting departments using lookalike remittance domains.',
    '["paypa1.com", "wire-remittance.net", "185.220.101.5", "45.142.214.10"]'::jsonb
),
(
    'camp-gov-002',
    'Executive Impersonation SWIFT Divert',
    'TA412 State-Aligned Phishing',
    'active',
    'Spear-phishing operations targeting C-suite executives requesting urgent international funds transfers.',
    '["exec-notice.org", "auth-portal-secure.info", "203.0.113.42"]'::jsonb
)
ON CONFLICT (campaign_id) DO NOTHING;

-- Initial Forensic Cases across all 5 Stages
INSERT INTO cases (case_id, title, status, severity, notes, assigned_analyst)
VALUES
(
    'case-open-001',
    'Inbound Wire Transfer Redirect - Urgent Executive Request',
    'open',
    'critical',
    'Urgent CFO impersonation requesting immediate international SWIFT remittance. DMARC alignment failed.',
    'analyst@org.gov'
),
(
    'case-open-002',
    'Suspicious PDF Macro Attachment - Credential Harvester',
    'open',
    'high',
    'Encrypted PDF attachment containing obfuscated JavaScript redirect stream.',
    'analyst@org.gov'
),
(
    'case-inv-003',
    'Active Phishing Campaign - Financial Brand Spoofing',
    'investigating',
    'high',
    'Lookalike domain targeting corporate banking portal with homoglyph substitution.',
    'analyst@org.gov'
),
(
    'case-cnt-004',
    'Lookalike Domain Targeted BEC - Perimeter Quarantined',
    'contained',
    'critical',
    'Perimeter firewall rules deployed to block lookalike domain and transit IP subnet AS15169.',
    'analyst@org.gov'
),
(
    'case-res-005',
    'Corporate Gateway Phish Vector - Domain Blacklisted',
    'resolved',
    'medium',
    'Domain and URL IOCs submitted to threat intelligence feeds. Mailbox purged.',
    'analyst@org.gov'
),
(
    'case-cls-006',
    'Automated Vendor Notification - Verified Legitimacy',
    'closed',
    'low',
    'SPF, DKIM, and DMARC strictly aligned. Confirmed authentic vendor billing receipt.',
    'analyst@org.gov'
)
ON CONFLICT (case_id) DO NOTHING;
