# Software Development Team — Gateway API

**Stack:** Python (FastAPI) · Owns: ingestion gateway, auth, case DB, dashboard/alerting APIs, calling the Forensics+AI/ML pipeline internally.

See [`README.md`](./README.md) for the shared `EmailSubmission` / `FraudAssessment` contracts referenced below.

---

## 1. Auth

### `POST /auth/login`
**Request**
```json
{ "email": "analyst@org.gov", "password": "string" }
```
**Response `200`**
```json
{ "access_token": "jwt", "refresh_token": "jwt", "expires_in": 3600, "role": "analyst|admin|investigator" }
```

### `POST /auth/refresh`
**Request:** `{ "refresh_token": "jwt" }`
**Response `200`:** `{ "access_token": "jwt", "expires_in": 3600 }`

All endpoints below require `Authorization: Bearer <access_token>` unless noted.

---

## 2. Email Ingestion

### `POST /api/v1/emails/ingest`
Accepts a raw email (upload, forwarded `.eml`, or programmatic push). This is the entry point that eventually calls the pipeline service.

**Request** (`multipart/form-data`)
| Field | Type | Notes |
|---|---|---|
| `file` | `.eml` file | raw RFC 5322 message |
| `tenant_id` | uuid | required |
| `source` | string | `upload`\|`imap`\|`forward`\|`api` |

**Response `202 Accepted`**
```json
{
  "submission_id": "uuid",
  "status": "queued",
  "estimated_processing": "sync|async"
}
```

### `GET /api/v1/emails/{submission_id}`
Returns ingestion + analysis status and, if complete, the `FraudAssessment`.

**Response `200`**
```json
{
  "submission_id": "uuid",
  "status": "queued|analyzing|complete|failed",
  "ingested_at": "ISO8601",
  "assessment": { "...": "FraudAssessment object, see README.md §2.2, null if not complete" }
}
```

### `GET /api/v1/emails` (list/search)
**Query params:** `tenant_id`, `risk_level`, `classification`, `from_date`, `to_date`, `campaign_id`, `page`, `page_size`

**Response `200`**
```json
{
  "results": [ { "submission_id": "uuid", "risk_level": "high", "classification": "phishing", "received_at": "ISO8601", "sender": "string" } ],
  "total": 128,
  "page": 1,
  "page_size": 25
}
```

---

## 3. Internal calls to the Forensics+AI/ML Pipeline

These are calls **Gateway makes outbound** — documented here so Software Dev knows exactly what to send/expect; full spec owned by the Forensics+AI/ML team in their doc.

### `POST {PIPELINE_BASE_URL}/internal/analyze`
Gateway sends `EmailSubmission` (README §2.1). Receives either:
- `200` + `FraudAssessment` inline (sync path), or
- `202` + `{ "submission_id": "uuid", "status": "processing" }` (async path)

### `POST /internal/webhooks/fraud-assessment` *(Gateway exposes this, Pipeline calls it)*
**Request:** full `FraudAssessment` object (README §2.2)
**Response:** `204 No Content`
Gateway must validate a shared-secret header (`X-Pipeline-Signature`) before trusting this payload.

---

## 4. Case Management

### `POST /api/v1/cases`
Groups related submissions (e.g. a phishing campaign) into a case.
```json
{ "title": "string", "submission_ids": ["uuid"], "notes": "string" }
```
**Response `201`:** `{ "case_id": "uuid", "created_at": "ISO8601" }`

### `GET /api/v1/cases/{case_id}`
Returns case metadata, linked submissions, and their assessments.

### `PATCH /api/v1/cases/{case_id}`
Update status: `{ "status": "open|investigating|escalated|closed" }`

---

## 5. Dashboard & Alerts

### `GET /api/v1/dashboard/summary`
**Response `200`**
```json
{
  "total_analyzed_24h": 3420,
  "high_risk_24h": 47,
  "active_campaigns": 5,
  "top_origin_countries": [{ "country": "string", "count": 12 }]
}
```

### `GET /api/v1/alerts`
**Query params:** `unacknowledged_only`, `min_risk_level`
**Response `200`:** list of alert objects, each referencing a `submission_id` and `fraud_score`.

### `POST /api/v1/alerts/{alert_id}/acknowledge`
**Response `200`:** `{ "alert_id": "uuid", "acknowledged_by": "user_id", "acknowledged_at": "ISO8601" }`

---

## 6. Forensic Report Export

### `GET /api/v1/emails/{submission_id}/report`
**Query params:** `format=pdf|json`
Generates the structured forensic report for legal/law-enforcement handoff, pulling the stored `FraudAssessment` plus chain-of-custody log.

**Response `200`:** binary (PDF) or JSON report object.

---

## 7. DB Schema (high level)

| Table | Key columns |
|---|---|
| `submissions` | `submission_id`, `tenant_id`, `raw_storage_ref`, `status`, `ingested_at` |
| `assessments` | `submission_id` (FK), full `FraudAssessment` as JSONB, `analyzed_at` |
| `cases` | `case_id`, `title`, `status`, `created_at` |
| `case_submissions` | `case_id`, `submission_id` (many-to-many) |
| `alerts` | `alert_id`, `submission_id`, `acknowledged_by`, `acknowledged_at` |
| `chain_of_custody` | `log_id`, `submission_id`, `actor`, `action`, `timestamp` |
| `users` | `user_id`, `email`, `role`, `tenant_id` |

---

## 8. Config: Privacy/Retention

### `GET /api/v1/tenants/{tenant_id}/privacy-config`
### `PUT /api/v1/tenants/{tenant_id}/privacy-config`
```json
{
  "retention_days": 180,
  "mask_pii_in_dashboard": true,
  "auto_purge_low_risk": true
}
```
