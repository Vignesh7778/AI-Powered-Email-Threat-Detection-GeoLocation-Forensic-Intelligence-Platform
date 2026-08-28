# backend.md — Frontend-Facing Connector APIs

**Scope:** Every screen in `design.md` needs a Gateway endpoint behind it. Most already exist in `software-dev-README.md`; this doc maps each screen to its connector, and specifies the ones that don't exist yet but are required by the design. New endpoints are marked **[NEW]**. All endpoints are under Gateway's existing auth (`Authorization: Bearer <access_token>`) unless noted.

Organized by `design.md` section number so the two documents read side by side.

---

## §4.1 — Login & Access

| Screen need | Connector | Status |
|---|---|---|
| Credential entry + MFA | `POST /auth/login` | Existing. **[NEW]** MFA is a UX requirement per `design.md` §4.1 but `software-dev-README.md` §1 shows only email/password → token. Needs a second step: `POST /auth/mfa/verify {mfa_token, code}` → `{access_token, refresh_token, expires_in, role}` |
| Role-based redirect | Returned in `role` field of `/auth/login` response | Existing — frontend routes on this value |

---

## §4.2 — Dashboard (home)

| Screen need | Connector | Status |
|---|---|---|
| Top strip (scanned/threats/open cases/avg triage time) | `GET /api/v1/dashboard/summary` | Existing (`software-dev-README.md` §5), but response shape only has `total_analyzed_24h, high_risk_24h, active_campaigns, top_origin_countries`. **[NEW]** needs `avg_time_to_triage_seconds`, `high_confidence_fraud_open` added to the response |
| Risk trend chart | **[NEW]** `GET /api/v1/dashboard/trend?days=30&granularity=day` → `{points: [{date, total, by_classification: {...}}]}` | Not in current spec |
| Top offending regions/domains mini-map | `top_origin_countries` from `/dashboard/summary`, plus **[NEW]** `GET /api/v1/dashboard/top-domains?window=7d` | Partial |
| Active campaigns needing attention | **[NEW]** `GET /api/v1/cases?status=investigating&sort=submission_count_desc&limit=5` (reuses case list, filtered) | Composable from existing `/api/v1/cases` |
| Quick action: "Report a suspicious email" | See §4.4 Flow D below — **[NEW]** `POST /api/v1/emails/self-report` | Not in current spec |

---

## §4.3 — Threat Inbox / Alert Queue

| Screen need | Connector | Status |
|---|---|---|
| List view w/ risk band, flags, time | `GET /api/v1/emails` (list/search) | Existing (`software-dev-README.md` §2) — response already carries `risk_level, classification, received_at, sender`. **[NEW]** needs `flags: [spoofed_domain, dkim_fail, suspicious_link, geo_mismatch]` added per row so the UI doesn't have to fetch full detail per email just to render icons |
| Filters (risk, auth-failure type, campaign, date, department) | `GET /api/v1/emails?risk_level=&classification=&campaign_id=&from_date=&to_date=` | Existing params cover most; **[NEW]** `auth_failure_type=` and `department=` query params need adding |
| Bulk triage (mark reviewed / escalate / false positive) | **[NEW]** `POST /api/v1/emails/bulk-action {submission_ids: [uuid], action: "mark_reviewed"\|"escalate_to_case"\|"mark_false_positive", case_id?: uuid}` | Not in current spec — critical gap, since analysts process volume per `design.md` §4.3 |
| Saved views | **[NEW]** `GET/POST /api/v1/users/{user_id}/saved-views {name, filter_params}` | Not in current spec |

---

## §4.4 — Email Detail & Trace View

This is the core screen; each tab maps to a slice of the stored `FraudAssessment`.

| Tab | Connector | Status |
|---|---|---|
| **Overview** — plain-language summary, fraud gauge, sandboxed preview | `GET /api/v1/emails/{submission_id}` returns `assessment` (full `FraudAssessment`). **[NEW]** the summary sentence itself ("This email claims to be from X but was likely sent from Y") is generation, not storage — needs a `narrative_summary` field added to `FraudAssessment` shape, populated during Stage 5 aggregation (`pipeline.md` Stage 5.2) rather than computed client-side | Mostly existing + one new field |
| **Header & Authentication** — SPF/DKIM/DMARC badges, relay timeline, raw headers toggle | Part of `assessment` payload already (forensics output is embedded). No new endpoint — this is a rendering split of existing data | Existing |
| **Origin & Geolocation** — map pin + confidence ring, infra type, domain intel panel | `origin` block within `assessment` (per `forensics-README.md` §5 note: origin is in `FraudAssessment`, not a classifier feature) | Existing |
| **Attribution & Correlation** — "seen in X other incidents," relationship graph | `assessment.correlation` (from `ml/graph/correlate`) for the summary sentence; **[NEW]** `GET /api/v1/emails/{submission_id}/graph` proxies through to AI/ML's `GET /ml/graph/campaign/{campaign_id}` and reshapes for the frontend's node-diagram library | Needs a thin proxy |
| **Forensic Report** — one-click export, evidence-lock status, chain-of-custody | `GET /api/v1/emails/{submission_id}/report?format=pdf\|json` (existing, §6) for export; **[NEW]** `GET /api/v1/emails/{submission_id}/custody` proxies `forensics/evidence/{submission_id}/chain` so the tab can render lock status without generating a full report | Export exists; live custody view is new |
| Analyst actions from this screen (dismiss/escalate/generate report) | `PATCH /api/v1/emails/{submission_id}` **[NEW]** `{status: "dismissed"\|"escalated"}`, plus existing `POST /api/v1/cases` to escalate | Partial gap |

---

## §4.5 — Campaigns / Case Management

| Screen need | Connector | Status |
|---|---|---|
| Case board (Kanban/list) | `GET /api/v1/cases` **[NEW]** — current spec only shows `POST /api/v1/cases` and `GET /api/v1/cases/{case_id}` (single). A list endpoint with `status` filter is needed for the board view | Needs list variant |
| Case detail: timeline, shared indicators, affected recipients, status, assignee | `GET /api/v1/cases/{case_id}` (existing) returns metadata + linked submissions + assessments. **[NEW]** should also embed the `shared_indicators` from each submission's `assessment.correlation` so the frontend doesn't re-fetch per submission | Existing + enrichment |
| Update status | `PATCH /api/v1/cases/{case_id}` | Existing |
| Assign analyst | **[NEW]** `PATCH /api/v1/cases/{case_id} {assigned_to: user_id}` (extend existing PATCH body) | Small extension |
| Notes/comments thread | **[NEW]** `GET/POST /api/v1/cases/{case_id}/comments {body, author_id, created_at}` | Not in current spec |

---

## §4.6 — Geolocation & Threat Map (org-wide)

| Screen need | Connector | Status |
|---|---|---|
| Heat-map, filterable by date/type/confidence | **[NEW]** `GET /api/v1/geo/heatmap?from_date=&to_date=&classification=&min_confidence=` → aggregated `{country, region, lat, lon, count, avg_confidence}[]`, built by aggregating `origin` blocks across `assessments` | Not in current spec — this is distinct from the per-email origin data; it's a rollup |
| Click-through to region's emails/cases | `GET /api/v1/emails?...` with **[NEW]** `origin_country=` / `origin_region=` filter params | Small extension |

---

## §4.7 — Reports & Export Center

| Screen need | Connector | Status |
|---|---|---|
| Library of generated reports | **[NEW]** `GET /api/v1/reports?tenant_id=&type=` → list of previously generated report artifacts (references the report storage table flagged as a gap in `pipeline.md` Stage 7.4) | Not in current spec |
| Scheduled recurring reports (e.g. weekly exec summary) | **[NEW]** `GET/POST /api/v1/reports/schedules {frequency, format, recipients, filter_params}` | Not in current spec |
| Export history | **[NEW]** covered by the same `/api/v1/reports` list with an `exported_at`/`exported_by` field, sourced from `chain_of_custody` entries where `action` implies export | Composable |

---

## §4.8 — Rules, Policies & Watchlists

This is the biggest structural gap — nothing in `software-dev-README.md` currently persists tenant-configurable rules, and `pipeline.md` Stage 3.2 depends on this data existing (`compare_against` brand list for lookalike detection).

| Screen need | Connector | Status |
|---|---|---|
| Sensitivity thresholds (e.g. auto-quarantine above risk X) | **[NEW]** `GET/PUT /api/v1/tenants/{tenant_id}/rules/thresholds {alert_threshold, auto_quarantine_threshold}` | Not in current spec |
| Watchlists/allowlists (domains, IPs) | **[NEW]** `GET/POST/DELETE /api/v1/tenants/{tenant_id}/watchlists/{list_type}` where `list_type` is `protected_brands\|blocked_domains\|allowed_domains\|blocked_ips` — the `protected_brands` list is exactly what feeds `forensics/domain/lookalike-check`'s `compare_against` in `pipeline.md` Stage 3.2 | Not in current spec — required for the pipeline itself, not just UI |
| Auto-actions | Folded into `rules/thresholds` above (`auto_quarantine_threshold` triggers an action, not just an alert) | Not in current spec |

---

## §4.9 — User & Access Management

| Screen need | Connector | Status |
|---|---|---|
| Roles, permissions, department mapping, MFA enforcement | **[NEW]** `GET/POST/PATCH /api/v1/tenants/{tenant_id}/users {email, role, department, mfa_enforced}` | `users` table exists in DB schema (`software-dev-README.md` §7) but no CRUD API is documented |

---

## §4.10 — Audit Log / Chain of Custody

| Screen need | Connector | Status |
|---|---|---|
| Append-only searchable log of who viewed/exported/acted on a case/email | **[NEW]** `GET /api/v1/audit-log?submission_id=&case_id=&actor=&from_date=&to_date=` — this is broader than forensic evidence logging: it needs to also log Gateway-side actions (viewed detail, exported report, acknowledged alert), not just Forensics module calls | Forensics-side logging exists (`forensics/evidence/log`); Gateway-side action logging on the same actions (view/export/acknowledge) is **not yet wired** and is the actual gap |

---

## §4.11 — Settings

| Screen need | Connector | Status |
|---|---|---|
| Mail integrations (monitored mailboxes/domains) | **[NEW]** `GET/POST /api/v1/tenants/{tenant_id}/integrations/mailboxes` | Not in current spec |
| Notification preferences | **[NEW]** `GET/PUT /api/v1/users/{user_id}/notification-preferences` | Not in current spec |
| Retention/masking config | `GET/PUT /api/v1/tenants/{tenant_id}/privacy-config` | Existing (`software-dev-README.md` §8) |

---

## Flow D — Employee Self-Report (design.md §4.4)

Deliberately lightweight — "a non-technical person submitting a tip shouldn't see any of the complexity above."

**[NEW]** `POST /api/v1/emails/self-report` (multipart, same shape as ingest but no `tenant_id`-level analyst context required — inferred from the logged-in employee's account)
→ `202 {submission_id, status: "queued"}` — same response shape as `/api/v1/emails/ingest`, reuses the exact same pipeline (`pipeline.md` Stage 0 onward), just tagged `source: "self_report"` so it routes into the analyst queue rather than any employee-facing view.

---

## Summary: New Endpoints Required

Grouped for backend implementation planning:

**Auth/MFA:** `POST /auth/mfa/verify`

**Dashboard:** `GET /api/v1/dashboard/trend`, `GET /api/v1/dashboard/top-domains`

**Queue/Triage:** `POST /api/v1/emails/bulk-action`, `GET/POST /api/v1/users/{user_id}/saved-views`, `PATCH /api/v1/emails/{submission_id}`

**Detail view:** `GET /api/v1/emails/{submission_id}/graph`, `GET /api/v1/emails/{submission_id}/custody`

**Cases:** `GET /api/v1/cases` (list), `GET/POST /api/v1/cases/{case_id}/comments`

**Map:** `GET /api/v1/geo/heatmap`

**Reports:** `GET /api/v1/reports`, `GET/POST /api/v1/reports/schedules`

**Rules/Watchlists:** `GET/PUT /api/v1/tenants/{tenant_id}/rules/thresholds`, `GET/POST/DELETE /api/v1/tenants/{tenant_id}/watchlists/{list_type}`

**Admin:** `GET/POST/PATCH /api/v1/tenants/{tenant_id}/users`

**Audit:** `GET /api/v1/audit-log`

**Settings:** `GET/POST /api/v1/tenants/{tenant_id}/integrations/mailboxes`, `GET/PUT /api/v1/users/{user_id}/notification-preferences`

**Self-report:** `POST /api/v1/emails/self-report`

**Model feedback surface:** `POST /api/v1/emails/{submission_id}/verdict {analyst_verdict}` — Gateway-side wrapper that calls AI/ML's `POST /ml/models/feedback` internally, so analysts never call the AI/ML API directly.
