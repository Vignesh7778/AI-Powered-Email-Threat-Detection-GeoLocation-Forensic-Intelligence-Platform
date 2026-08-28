# AI/ML Team — API

**Owns:** NLP content analysis, link risk scoring, the fraud classifier, attachment malware scoring, graph correlation/attribution, and final score aggregation.

AI/ML runs after Forensics in the pipeline and consumes forensic output as classifier features. See [`forensics-README.md`](./forensics-README.md) §5 for exactly which forensic endpoint maps to which feature, and [`README.md`](./README.md) for overall system contracts.

---

## 0. Input Contract ← Forensics Team

Before calling `/ml/classify`, the orchestrator assembles a `features` object from Forensics output:

```json
{
  "submission_id": "uuid",
  "features": {
    "auth_results": { "spf": "fail", "dkim": "none", "dmarc": "fail" },
    "domain_age_days": 4,
    "lookalike_score": 0.93,
    "infra_flags": ["vpn"],
    "header_anomalies_count": 2,
    "urgency_score": 0.72,
    "impersonation_language_score": 0.65,
    "link_risk_scores": [0.9]
  }
}
```

- `auth_results`, `domain_age_days`, `lookalike_score`, `infra_flags`, `header_anomalies_count` → come from **Forensics**.
- `urgency_score`, `impersonation_language_score` → come from this team's own `/ml/nlp/analyze-content` (§1).
- `link_risk_scores` → come from this team's own `/ml/links/extract-and-score` (§1).

---

## 1. Fraud Classification Engine

### `POST /ml/nlp/analyze-content`
NLP pass over subject/body for social-engineering and urgency patterns.

**Request**
```json
{ "subject": "string", "body_text": "string" }
```
**Response `200`**
```json
{
  "urgency_score": 0.72,
  "impersonation_language_score": 0.65,
  "detected_patterns": [
    { "type": "payment_diversion|fake_invoice|credential_harvesting|executive_impersonation|urgency_cue", "excerpt_span": [120, 168], "confidence": 0.81 }
  ],
  "language_model_version": "v2.3.1"
}
```
> Note: `excerpt_span` is a character offset into the original body, not a copy of the text — keeps the response from duplicating potentially sensitive email content.

### `POST /ml/links/extract-and-score`
**Request:** `{ "body_html": "string" }`
**Response `200`**
```json
{
  "links": [
    { "displayed_text": "string", "actual_url": "string", "obfuscated": true, "risk_score": 0.9, "reasons": ["url_shortener", "ip_literal_host", "mismatched_display_text"] }
  ]
}
```

### `POST /ml/classify`
The core classifier — takes the `features` object (§0) and returns the classification.

**Request:** see §0

**Response `200`**
```json
{
  "classification": "legitimate|suspicious|impersonation|phishing|bec_fraud",
  "fraud_score": 0.87,
  "confidence": 0.91,
  "model_version": "v4.1.0",
  "feature_importance": [ { "feature": "lookalike_score", "contribution": 0.31 } ]
}
```

### `POST /ml/attachments/scan` *(async-capable)*
**Request:** `{ "storage_ref": "string", "sha256": "string", "content_type": "string" }`
**Response `200` or `202`**
```json
{ "status": "complete|sandboxing", "malware_score": 0.4, "detected_type": "macro_dropper|none|...", "sandbox_report_ref": "string|null" }
```
When `202` is returned, the final result is delivered via the pipeline's async webhook path (see `README.md` §3).

---

## 2. Identity Correlation & Attribution (Graph Engine)

### `POST /ml/graph/correlate`
Runs graph-based correlation against known senders/domains/IPs/campaigns.

**Request**
```json
{
  "submission_id": "uuid",
  "sender_domain": "string",
  "originating_ip": "string",
  "reply_to": "string|null",
  "link_domains": ["string"]
}
```
> `sender_domain` and `originating_ip` come from Forensics (`/forensics/domain/intel` and `/forensics/origin/trace` respectively).

**Response `200`**
```json
{
  "linked_campaign_id": "uuid|null",
  "related_submission_ids": ["uuid"],
  "cluster_confidence": 0.65,
  "shared_indicators": [ { "type": "ip|domain|reply_to|link_target", "value": "string", "seen_in_count": 14 } ]
}
```

### `GET /ml/graph/campaign/{campaign_id}`
Returns the full correlation graph for a campaign (nodes = domains/IPs/emails, edges = shared indicators) — used to render the dashboard's trace map.

**Response `200`**
```json
{
  "campaign_id": "uuid",
  "nodes": [ { "id": "string", "type": "domain|ip|submission", "label": "string" } ],
  "edges": [ { "source": "string", "target": "string", "relation": "string", "weight": 0.5 } ]
}
```

---

## 3. Fraud Score Aggregation

### `POST /ml/aggregate` *(internal — called by the pipeline orchestrator)*
Combines all Forensics output + this team's §1–§2 outputs into the final `FraudAssessment`.

**Request:** all module outputs bundled (forensics results + classify result + correlate result)
**Response `200`:** `FraudAssessment` (`README.md` §2.2) — this is exactly what the pipeline's `/internal/analyze` ultimately returns to Software Dev's Gateway.

---

## 4. Model Ops

### `GET /ml/models/health`
**Response `200`:** `{ "models": [ { "name": "classifier", "version": "v4.1.0", "last_trained": "ISO8601", "status": "healthy" } ] }`

### `POST /ml/models/feedback`
Analyst-confirmed ground truth, fed back for retraining.
```json
{ "submission_id": "uuid", "analyst_verdict": "legitimate|phishing|bec_fraud|...", "analyst_id": "uuid" }
```
**Response `202`:** `{ "status": "queued_for_retraining" }`

---

## 5. Module Dependency Order

```
features from Forensics (see §0)
  ├──────────────────────────────┐
  ├─▶ nlp/analyze-content ────────┤
  ├─▶ links/extract-and-score ────┤
  └─▶ attachments/scan (async)    │
                                  ▼
                            ml/classify ──▶ ml/graph/correlate ──▶ ml/aggregate ──▶ FraudAssessment
```
