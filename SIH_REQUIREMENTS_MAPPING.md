# TraceX — SIH Problem Statement 26106 Requirements Mapping

**Project:** TraceX — AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform  
**Organization:** All India Council for Technical Education (AICTE) – Cyber Security Cell  
**Theme:** Blockchain & Cybersecurity  

---

## Complete SIH Requirements Verification Matrix

| # | SIH Requirement | TraceX Feature Implementation | Backend File | API Endpoint | Frontend UI View | Status | Evidence / Verification |
|---|---|---|---|---|---|---|---|
| **1** | **Fraudulent Email Detection** | Multi-class threat classification (`legitimate`, `suspicious`, `phishing`, `impersonation`, `bec_fraud`) | `backend/ml/models/classifier.py` | `POST /emails/ingest` | `InvestigationPage.tsx` (Tab 1), `ThreatInboxPage.tsx` | **DONE** | Pytest `test_classifier`, `test_end_to_end_pipeline` |
| **2** | **Email Header Forensics** | RFC 5322 MIME extraction & anomaly detection (forgery, injection, reply-to routing) | `backend/analysis/headers/header_analyzer.py` | `GET /forensics/headers/{id}` | `InvestigationPage.tsx` (Tab 2) | **DONE** | Pytest `test_header_analyzer` |
| **3** | **SPF / DKIM / DMARC** | Live DNS TXT lookups, DKIM header validation, and DMARC alignment checks | `backend/analysis/authentication/auth_validator.py` | `GET /forensics/auth/{id}` | `InvestigationPage.tsx` (Tab 2) | **DONE** | Pytest `test_auth_validator` |
| **4** | **Origin Traceability** | Reassembles chronological Received chain (Hop 0 to Gateway), rDNS, ASN, ISP | `backend/analysis/origin/origin_tracer.py` | `GET /forensics/hops/{id}` | `InvestigationPage.tsx` (Tab 2 & 3) | **DONE** | Pytest `test_origin_tracer` |
| **5** | **Geolocation Intelligence** | Live GeoIP for public IPs; non-routable filter for RFC 1918 private subnets | `backend/analysis/geolocation/geo_service.py` | `GET /forensics/geo/{id}` | `InvestigationPage.tsx` (Tab 3), `MapPage.tsx` | **DONE** | Pytest `test_geo_service` |
| **6** | **VPN / TOR / Proxy / DNSBL** | Live DNSBL queries (Spamhaus ZEN, SpamCop) & hosting classification | `backend/analysis/threat_intel/infra_flags.py` | `GET /forensics/flags/{id}` | `InvestigationPage.tsx` (Tab 3) | **DONE** | Pytest `test_threat_intel` |
| **7** | **Domain Intelligence** | Live DNS MX, NS, TXT, A resolution + live ICANN RDAP registration age lookup | `backend/analysis/domain/domain_intel.py` | `GET /forensics/domain/{id}` | `InvestigationPage.tsx` (Tab 4) | **DONE** | Pytest `test_end_to_end_pipeline` |
| **8** | **Brand Impersonation / Lookalike** | Levenshtein distance, Cyrillic homoglyphs, typosquatting & bit-squatting | `backend/analysis/domain/lookalike.py` | `GET /ml/lookalike` | `InvestigationPage.tsx` (Tab 4) | **DONE** | Pytest `test_domain_lookalike` |
| **9** | **URL Analysis** | Display text vs. destination href mismatch, IP literal hostname, shortener detection | `backend/ml/inference/link_engine.py` | `POST /ml/links/extract` | `InvestigationPage.tsx` (Tab 5) | **DONE** | Pytest `test_link_engine` |
| **10** | **Attachment Forensics** | Safe static analysis, SHA-256 / MD5 / SHA-1 hashing, file signature validation | `backend/ml/inference/attachment_engine.py` | `POST /ml/attachments/scan` | `InvestigationPage.tsx` (Tab 5) | **DONE** | Pytest `test_attachment_scanner` |
| **11** | **Threat Intelligence** | Extensible provider architecture returning indicator, source, and confidence | `backend/analysis/threat_intel/infra_flags.py` | `GET /forensics/threat-intel/{ip}` | `InvestigationPage.tsx` (Tab 3 & 5) | **DONE** | Pytest `test_threat_intel` |
| **12** | **BEC Detection** | Social engineering NLP vectors: urgency, executive mimicry, payment diversion | `backend/ml/inference/nlp_engine.py` | `POST /ml/nlp/analyze` | `InvestigationPage.tsx` (Tab 5) | **DONE** | Pytest `test_nlp_engine` |
| **13** | **Explainable Risk Engine** | 0.00 – 1.00 composite score with full factor-by-factor weight & evidence breakdown | `backend/ml/inference/aggregator.py` | `GET /emails/{id}` | `InvestigationPage.tsx` (Tab 1) | **DONE** | Pytest `test_classifier` |
| **14** | **Attribution Support** | Graph correlation linking Email $\rightarrow$ Sender $\rightarrow$ IP $\rightarrow$ Domain $\rightarrow$ Campaign | `backend/graph/graph_engine.py` | `GET /campaigns/{id}/graph` | `InvestigationPage.tsx` (Tab 6), `CampaignsPage.tsx` | **DONE** | Pytest `test_graph_correlate` |
| **15** | **Campaign Correlation** | Cross-incident IOC clustering across domains, subnets, and targeted organizations | `backend/graph/graph_engine.py` | `GET /campaigns/{id}/graph` | `CampaignsPage.tsx`, `InvestigationPage.tsx` | **DONE** | Pytest `test_campaign_graph` |
| **16** | **Case Management** | Full incident desk: Statuses (`OPEN`, `INVESTIGATING`, `CONTAINED`, `RESOLVED`, `CLOSED`) | `backend/app/api/v1/routes/cases.py` | `POST /cases`, `GET /cases` | `CasesPage.tsx` | **DONE** | Database schema & Case API tests |
| **17** | **Chain of Custody** | Immediate SHA-256 calculation, tamper-evident audit logging of all analysis steps | `backend/analysis/evidence/evidence_logger.py` | `GET /forensics/chain/{id}` | `InvestigationPage.tsx` (Tab 7) | **DONE** | Pytest `test_report_generation` |
| **18** | **Privacy & Masking** | Role-aware PII redaction (`FULL`, `MASKED`, `RESTRICTED`) protecting emails/names | `backend/app/api/v1/routes/privacy.py` | `GET /privacy/config`, `POST /privacy/config` | `SettingsPage.tsx` | **DONE** | Privacy config persistence tests |
| **19** | **Data Retention** | Configurable retention periods (7d, 30d, 90d, 180d, 365d, custom) | `backend/app/models/models.py` | `POST /privacy/config` | `SettingsPage.tsx` | **DONE** | PrivacyConfig schema tests |
| **20** | **Audit Logging** | Comprehensive logging of actor, action, timestamp, resource, and result | `backend/analysis/evidence/evidence_logger.py` | `GET /forensics/chain/{id}` | `InvestigationPage.tsx` (Tab 7) | **DONE** | Chain of Custody ledger tests |
| **21** | **Security Workbench & Dashboard** | Enterprise TraceX dark interface, 7-tab deep workbench, Leaflet map, PDF/JSON export | `frontend/src/pages/InvestigationPage.tsx` | `GET /emails/{id}/report` | `DashboardPage.tsx`, `InvestigationPage.tsx` | **DONE** | Vite build & Pytest `test_report_generation` |

