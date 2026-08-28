# pipeline.md — End-to-End Orchestration Pipeline

**Scope:** This document maps every feature in the problem statement to the actual sequence of API calls across the three teams (Software Dev Gateway → Forensics → AI/ML), and specifies what gets fetched, what gets processed, and what gets stored at each step. This is the orchestrator's runbook — it lives in the pipeline coordination layer referenced in `software-dev-README.md` §3 (`{PIPELINE_BASE_URL}/internal/analyze`).

Three actors appear throughout:
- **Gateway** — Software Dev's ingestion/auth/case API (`software-dev-README.md`)
- **Forensics** — header/origin/geo/domain module (`forensics-README.md`)
- **AI/ML** — NLP/classification/graph module (`aiml-README.md`)
- **Orchestrator** — the thin coordination layer that calls Forensics then AI/ML then writes back to Gateway's DB. Not owned by any one team; this doc *is* its spec.

---

## 0. Trigger — Email Ingestion

**Feature:** *"ingest raw email content, metadata, and headers"*

| Step | Call | Fetch | Process | Store |
|---|---|---|---|---|
| 0.1 | Client → Gateway `POST /api/v1/emails/ingest` (multipart: `.eml`, `tenant_id`, `source`) | Raw `.eml` bytes | Validate MIME structure, virus-scan the container file (not attachments yet — that's AI/ML §5), extract `raw_headers` block + `body_text` + `body_html` + attachment refs | `submissions` row (`status=queued`, `raw_storage_ref` → blob store) |
| 0.2 | Gateway → Orchestrator (async, fire-and-forget) | `submission_id`, storage ref | Enqueue job | Job queue entry |
| 0.3 | Gateway → Client | — | — | Returns `202 { submission_id, status: "queued" }` immediately (per `software-dev-README.md` §2) |

Orchestrator picks up the job and runs Stages 1–5 below. Every module call that touches raw evidence is logged in parallel (see Stage 6).

---

## Stage 1 — Header & Protocol Forensics

**Feature:** *"Email Header and Protocol Analysis Module"* — Return-Path, Received headers, Message-ID, Reply-To, DKIM/SPF/DMARC, relay anomalies.

| Step | Call | Fetch | Process | Store |
|---|---|---|---|---|
| 1.1 | Orchestrator → Forensics `POST /forensics/headers/parse` `{raw_headers}` | Structured header fields from raw text | Extract `received_chain`, detect `anomalies` (forged_return_path, relay_manipulation, header_injection, timestamp_inconsistency) | Cache in job context (not yet persisted — persisted once full assessment lands, Stage 5) |
| 1.2 | Orchestrator → Forensics `POST /forensics/auth/validate` `{raw_headers, sender_domain}` | SPF/DKIM/DMARC results | Compute `alignment_ok` | Job context |
| 1.3 | Orchestrator → Forensics `POST /forensics/evidence/log` `{submission_id, actor: "system", action: "parsed_headers"}` | — | — | `chain_of_custody` row |

**Output carried forward:** `received_chain`, `anomalies` (→ `header_anomalies_count` feature), `auth_results = {spf, dkim, dmarc}`.

---

## Stage 2 — Origin Traceability & Geolocation

**Feature:** *"Origin Traceability and Location Analysis"* — earliest reliable sending IP, geolocation, infra flags.

| Step | Call | Fetch | Process | Store |
|---|---|---|---|---|
| 2.1 | Orchestrator → Forensics `POST /forensics/origin/trace` `{received_chain, trusted_relay_ranges}` | `originating_ip`, `confidence`, `reasoning` | Filter internal/trusted hops, walk chain to earliest external hop | Job context |
| 2.2 | Orchestrator → Forensics `POST /forensics/geo/lookup` `{ip: originating_ip}` | `country, region, city, lat, lon, isp, hosting_provider, asn` | — | Job context — this becomes the `origin` block in `FraudAssessment` (per `forensics-README.md` §5, this is *not* a classifier feature, it's report/map data) |
| 2.3 | Orchestrator → Forensics `POST /forensics/infra/flags` `{ip: originating_ip}` | `flags: [vpn, tor, open_relay, cloud_hosted, botnet_suspected]` | → `infra_flags` feature | Job context |
| 2.4 | Orchestrator → Forensics `POST /forensics/evidence/log` `{action: "traced_origin"}` then `{action: "geo_lookup"}` | — | — | `chain_of_custody` rows |

**Output carried forward:** `originating_ip`, `origin_confidence`, `geo` block, `infra_flags`.

---

## Stage 3 — Domain Intelligence

**Feature:** *"Domain intelligence analysis using WHOIS data, DNS records, MX records, hosting fingerprints, and registrar details"*

| Step | Call | Fetch | Process | Store |
|---|---|---|---|---|
| 3.1 | Orchestrator → Forensics `POST /forensics/domain/intel` `{domain: sender_domain}` | `registrar, created_date, age_days, mx_records, dns_records, hosting_fingerprint` | → `domain_age_days` feature | Job context |
| 3.2 | Orchestrator → Forensics `POST /forensics/domain/lookalike-check` `{domain, compare_against: [protected_brand_list]}` | `lookalike_of, technique, score` | → `lookalike_score` feature. `compare_against` list is pulled from the tenant's watchlist config (see `backend.md` §4 Rules/Watchlists API — this is a **new** connector, not in the current Gateway spec) | Job context |
| 3.3 | Orchestrator → Forensics `POST /forensics/evidence/log` `{action: "domain_lookup"}` | — | — | `chain_of_custody` row |

**Output carried forward:** `domain_age_days`, `lookalike_score`.

---

## Stage 4 — Fraud Detection Engine (AI/ML)

**Feature:** *"Fraudulent Email Detection Engine"* — NLP social-engineering patterns, phishing indicators, classification, BEC pattern detection.

This is the point where Forensics output crosses the team boundary. Per `aiml-README.md` §0, the orchestrator assembles the `features` object.

| Step | Call | Fetch | Process | Store |
|---|---|---|---|---|
| 4.1 | Orchestrator → AI/ML `POST /ml/nlp/analyze-content` `{subject, body_text}` | `urgency_score, impersonation_language_score, detected_patterns[]` (payment_diversion, fake_invoice, credential_harvesting, executive_impersonation, urgency_cue) | These feed `features.urgency_score` / `features.impersonation_language_score` | Job context |
| 4.2 | Orchestrator → AI/ML `POST /ml/links/extract-and-score` `{body_html}` | `links[]` each with `risk_score`, `reasons` (url_shortener, ip_literal_host, mismatched_display_text) | Max risk score per link → `features.link_risk_scores[]` | Job context |
| 4.3 | Orchestrator → AI/ML `POST /ml/attachments/scan` `{storage_ref, sha256, content_type}` (once per attachment, parallel, async-capable) | `status, malware_score, detected_type, sandbox_report_ref` | If `202` (sandboxing), orchestrator does **not** block Stage 4.4 on this — result arrives later via `POST /internal/webhooks/fraud-assessment`-style callback and triggers a re-aggregation (Stage 5) | Job context; if async, job marked `partial`, final `malware_score` patched in on webhook |
| 4.4 | Orchestrator assembles `features` object (per `aiml-README.md` §0 schema) from Stages 1–3 + 4.1–4.2, then calls AI/ML `POST /ml/classify` `{submission_id, features}` | `classification, fraud_score, confidence, model_version, feature_importance[]` | This is the BEC/phishing/impersonation classification the feature calls for | Job context |

**Output carried forward:** `classification`, `fraud_score`, `confidence`, `feature_importance`, `malware_score` (or pending).

---

## Stage 5 — Identity Correlation & Attribution

**Feature:** *"Identity Correlation and Attribution Support"* — graph-based relationship analysis, campaign clustering, confidence-based attribution.

| Step | Call | Fetch | Process | Store |
|---|---|---|---|---|
| 5.1 | Orchestrator → AI/ML `POST /ml/graph/correlate` `{submission_id, sender_domain, originating_ip, reply_to, link_domains}` (`sender_domain`/`originating_ip` sourced from Stage 2–3, not re-fetched) | `linked_campaign_id, related_submission_ids, cluster_confidence, shared_indicators[]` | Determines whether this joins an existing campaign or seeds a new one | Job context; if `linked_campaign_id` is new, orchestrator calls Gateway `POST /api/v1/cases` internally (or a lighter-weight internal variant) to auto-create/attach a case |
| 5.2 | Orchestrator → AI/ML `POST /ml/aggregate` (bundles all Forensics + §4 + §5.1 output) | `FraudAssessment` object (`README.md` §2.2 shape) | Final assembly — this **is** the object returned by `/internal/analyze` | — |
| 5.3 | Orchestrator → Gateway `POST /internal/webhooks/fraud-assessment` `{FraudAssessment}` with `X-Pipeline-Signature` header (or inline `200` return if sync path was used) | — | Gateway validates signature | `assessments` row (`submission_id` FK, full JSONB), `submissions.status = complete` |
| 5.4 | Gateway derives alert | `fraud_score`, `classification` | If `fraud_score` ≥ tenant's alert threshold (see `backend.md` §4) | `alerts` row |

**On async attachment result arriving late:** re-run 5.2–5.4 with patched `malware_score`; this is a re-aggregation, not a new submission.

---

## Stage 6 — Evidence Integrity (runs alongside every stage, not after)

**Feature:** *"Logging, evidence preservation, and chain-of-custody support"*

Every Forensics call that touches raw evidence (1.1–1.3, 2.1–2.4, 3.1–3.3) fires a paired `POST /forensics/evidence/log` call, non-blocking. On report export:

| Step | Call | Fetch | Process | Store |
|---|---|---|---|---|
| 6.1 | Gateway → Forensics `GET /forensics/evidence/{submission_id}/chain` | Full ordered log | Rendered into the report's chain-of-custody section | — |

---

## Stage 7 — Reporting & Alerting Surface

**Feature:** *"Alerting, Dashboard, and Forensic Reporting"*

| Step | Call | Fetch | Process | Store |
|---|---|---|---|---|
| 7.1 | Client → Gateway `GET /api/v1/emails/{submission_id}` (poll or WebSocket push) | `status`, `assessment` | — | — |
| 7.2 | Client → Gateway `GET /api/v1/alerts?unacknowledged_only=true&min_risk_level=high` | Alert list | — | — |
| 7.3 | Analyst → Gateway `POST /api/v1/alerts/{alert_id}/acknowledge` | — | — | `alerts.acknowledged_by/at` |
| 7.4 | Client → Gateway `GET /api/v1/emails/{submission_id}/report?format=pdf` | Assessment + Stage 6 chain | Renders narrative report (per `design.md` §4.4 Forensic Report tab: plain-language summary + evidence lock status) | Report artifact (Reports & Export Center library, `design.md` §4.7 — **new** storage table, see `backend.md`) |

---

## Stage 8 — Feedback Loop (Model Ops)

**Feature:** implied by *"AI/ML models to classify"* needing to improve over time; not in the problem statement explicitly but required for a production system and present in the AI/ML API.

| Step | Call | Fetch | Process | Store |
|---|---|---|---|---|
| 8.1 | Analyst → Gateway (new connector, see `backend.md` §5) → AI/ML `POST /ml/models/feedback` `{submission_id, analyst_verdict, analyst_id}` | — | Queued for retraining | `202 queued_for_retraining` — AI/ML side, not Gateway DB |
| 8.2 | Ops → AI/ML `GET /ml/models/health` | Model versions/status | Surfaced on an admin/ops view | — |

---

## Full Pipeline Diagram

```
Client
  │ POST /api/v1/emails/ingest
  ▼
Gateway ── enqueue ──▶ Orchestrator
                          │
                          ├─▶ [Stage 1] Forensics: headers/parse, auth/validate
                          ├─▶ [Stage 2] Forensics: origin/trace → geo/lookup → infra/flags
                          ├─▶ [Stage 3] Forensics: domain/intel → domain/lookalike-check
                          │        (each of 1–3 paired with forensics/evidence/log)
                          │
                          ├─▶ [Stage 4] AI/ML: nlp/analyze-content, links/extract-and-score,
                          │             attachments/scan (async-capable)
                          │             → assemble `features` → ml/classify
                          │
                          ├─▶ [Stage 5] AI/ML: graph/correlate → ml/aggregate → FraudAssessment
                          │
                          ▼
                    Gateway: POST /internal/webhooks/fraud-assessment
                          │
                          ├─▶ assessments row, submissions.status=complete
                          ├─▶ alerts row (if fraud_score ≥ threshold)
                          └─▶ case auto-attach (if linked_campaign_id)

Client polls/subscribes: GET /api/v1/emails/{id}, /alerts, /dashboard/summary
Report export: GET /api/v1/emails/{id}/report ← pulls assessment + evidence chain
Feedback: analyst verdict → ml/models/feedback → retraining queue
```

---

## Gaps this pipeline surfaces (not present in the three team READMEs as-is)

These are needed to fully satisfy the problem statement + `design.md`, and are addressed as new connectors in `backend.md`:

1. **Rules/Watchlists storage** — `domain/lookalike-check`'s `compare_against` list and alert thresholds need a tenant-configurable source (`design.md` §4.8).
2. **Employee self-report flow** (`design.md` §4.4 Flow D) — a lightweight ingestion variant, not the full analyst-facing ingest.
3. **Campaign/case detail aggregation** — `GET /api/v1/cases/{case_id}` needs to join Gateway's case data with AI/ML's `GET /ml/graph/campaign/{campaign_id}` for the trace map (`design.md` §4.5, §4.6).
4. **Reports & Export Center library** (`design.md` §4.7) — scheduled/recurring reports and export history aren't in `software-dev-README.md` §6, which only covers on-demand single-submission export.
5. **Model feedback surfaced to analysts** — `/ml/models/feedback` exists on the AI/ML side but Gateway has no analyst-facing endpoint to trigger it.
