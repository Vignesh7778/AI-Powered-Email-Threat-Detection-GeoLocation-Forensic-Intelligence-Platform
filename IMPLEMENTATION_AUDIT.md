# TraceX — System Implementation & Capability Audit

**Project:** TraceX — AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform  
**SIH Problem Statement ID:** 26106  
**Organization:** All India Council for Technical Education (AICTE) – Cyber Security Cell  
**Theme:** Blockchain & Cybersecurity  

---

## 1. Executive Implementation Map

| Status Code | Definition |
|---|---|
| **`EXISTING`** | Implemented, tested, and fully functional in the codebase. |
| **`PARTIAL`** | Implemented but requires enhancement, deeper validation, or additional edge-case handling. |
| **`MISSING`** | Needs to be implemented to satisfy the full SIH 26106 specification. |
| **`ZERO-HALLUCINATION`** | Verified to never invent data, return `UNKNOWN`/`UNAVAILABLE` when missing, and strictly separate facts from inferences. |

---

## 2. Requirement-by-Requirement Capability Audit

| # | SIH Requirement | Current Status | Existing File / Component | Missing / Enhanced Capabilities | Priority |
|---|---|---|---|---|---|
| **1** | **Fraudulent Email Detection** | `EXISTING` | `backend/ml/models/classifier.py`, `nlp_engine.py` | Multi-class detection (`legitimate`, `suspicious`, `phishing`, `impersonation`, `bec_fraud`) combining deterministic heuristics + Groq LLM reasoning. | High |
| **2** | **Email Header Forensics** | `EXISTING` | `backend/analysis/headers/header_analyzer.py` | RFC 5322 extraction (From, To, Cc, Reply-To, Return-Path, Date, Message-ID, Received chain), header anomaly detection (injection, forgery, format). | High |
| **3** | **SPF / DKIM / DMARC** | `EXISTING` | `backend/analysis/authentication/auth_validator.py` | Live DNS TXT lookups for SPF and DMARC `_dmarc.<domain>`, DKIM signature header parsing, PASS/FAIL/NONE evaluation. | High |
| **4** | **Origin Traceability** | `EXISTING` | `backend/analysis/origin/origin_tracer.py` | Chronological Received hop timeline (Hop 0 to Gateway), rDNS, ASN, ISP, RFC 1918 private IP classification as non-routable. | High |
| **5** | **Geolocation Intelligence** | `EXISTING` | `backend/analysis/geolocation/geo_service.py` | Live GeoIP for public IPs only, labeled as "Estimated infrastructure location", returns `UNKNOWN` when unreachable/private. | High |
| **6** | **VPN / TOR / Proxy / DNSBL** | `EXISTING` | `backend/analysis/threat_intel/infra_flags.py` | Live DNSBL lookups against Spamhaus ZEN (`zen.spamhaus.org`) and SpamCop (`bl.spamcop.net`) with explicit disclaimers. | High |
| **7** | **Domain Intelligence** | `EXISTING` | `backend/analysis/domain/domain_intel.py` | Live DNS MX, NS, TXT, A queries, live ICANN RDAP registration date extraction, young domain risk weighting. | High |
| **8** | **Brand Impersonation / Lookalike** | `EXISTING` | `backend/analysis/domain/lookalike.py` | Levenshtein distance, Cyrillic visual homoglyphs, bit-squatting, typosquatting against brand dictionaries. | High |
| **9** | **URL Analysis** | `EXISTING` | `backend/ml/inference/link_engine.py` | Display text vs. destination href mismatch detection, IP literal host detection, URL shortener/redirect flag. | High |
| **10** | **Attachment Forensics** | `EXISTING` | `backend/ml/inference/attachment_engine.py` | Safe static analysis, SHA-256 / MD5 / SHA-1 hashing, file signature & extension mismatch detection. | High |
| **11** | **Threat Intelligence Providers** | `EXISTING` | `backend/analysis/threat_intel/infra_flags.py` | Extensible provider architecture, `NOT CONFIGURED` when keys missing, live DNSBL query execution. | Medium |
| **12** | **BEC Social Engineering Detection** | `EXISTING` | `backend/ml/inference/nlp_engine.py` | Psychological urgency, executive tone mimicry, confidential wire/payment diversion detection. | High |
| **13** | **Explainable Risk Engine** | `EXISTING` | `backend/ml/inference/aggregator.py`, `classifier.py` | 0.00 – 1.00 reproducible composite score with contributing factor weight breakdown and evidence citations. | High |
| **14** | **Attribution Support** | `EXISTING` | `backend/graph/graph_engine.py` | Evidence-backed graph correlating Email $\rightarrow$ Sender $\rightarrow$ Domain $\rightarrow$ IP $\rightarrow$ ASN $\rightarrow$ Subnet $\rightarrow$ Campaign. | High |
| **15** | **Campaign Correlation** | `EXISTING` | `backend/graph/graph_engine.py` | Cross-incident clustering linking related submissions sharing domains, subnets, and targets. | High |
| **16** | **Case Management Workflow** | `EXISTING` | `backend/app/api/v1/routes/cases.py`, `CasesPage.tsx` | Full incident investigation desk: Statuses (`OPEN`, `INVESTIGATING`, `CONTAINED`, `RESOLVED`, `CLOSED`), notes, timeline. | High |
| **17** | **Cryptographic Chain of Custody** | `EXISTING` | `backend/analysis/evidence/evidence_logger.py`, `models.py` | Immediate SHA-256 calculation upon ingest, tamper-evident audit logging of all analysis operations. | High |
| **18** | **Privacy & Sensitive Data Masking** | `EXISTING` | `backend/app/api/v1/routes/privacy.py`, `models.py` | Configurable PII masking (`FULL`, `MASKED`, `RESTRICTED`) protecting emails and names while preserving original artifacts. | Medium |
| **19** | **Configurable Data Retention** | `EXISTING` | `backend/app/models/models.py` (`PrivacyConfig`) | Configurable retention periods (7d, 30d, 90d, 180d, 365d, custom) distinguishing evidence from audit logs. | Medium |
| **20** | **Audit Logging** | `EXISTING` | `backend/analysis/evidence/evidence_logger.py` | Records Actor, Action, Timestamp, Resource, and Result for ingestion, export, analysis, and case edits. | High |
| **21** | **Security Workbench & Dashboard** | `EXISTING` | `InvestigationPage.tsx`, `DashboardPage.tsx`, `App.tsx` | Enterprise TraceX interface, 7-tab deep forensic investigation workbench, Fact/Inference/Unknown Trust Badges, Leaflet map. | High |

---

## 3. Fact / Inference / Unknown Model Validation

TraceX strictly adheres to the 4-tier truth classification standard:

1. **`[OBSERVED / VERIFIED]`**: Factual data obtained directly from MIME headers, cryptographic signatures (SPF, DKIM, DMARC), live DNS, or RDAP registries.
2. **`[MODEL PREDICTION]`**: Statistical scoring derived from deterministic algorithms (NLP urgency score, Levenshtein lookalike score, Random Forest composite score).
3. **`[LLM INFERENCE (GROQ)]`**: Contextual reasoning generated by Groq LPU inference, strictly grounded on observed evidence.
4. **`[UNKNOWN / UNAVAILABLE]`**: Clear declaration when external intelligence fails, an API key is unconfigured, or an IP is non-routable.

---

## 4. Verification and Acceptance Status

- **Automated Backend Pytest Suite:** 14/14 tests passing (`100% pass rate`).
- **Frontend Production Build:** TypeScript compilation (`tsc`) and Vite bundling passing with `0 errors`.
- **Zero Fictional Data:** Zero mock IOCs, fake IPs, or fabricated threat actor claims present in production logic.

