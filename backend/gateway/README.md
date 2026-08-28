# Gateway API — Email Threat Detection Platform

The **Gateway** is the main Software Dev backend service. It handles authentication, email ingestion, case management, dashboard analytics, and proxies to the Forensics & ML microservices.

---

## 🚀 Quick Start

```bash
cd backend/gateway
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

- **API Docs:** http://localhost:8001/docs  
- **ReDoc:** http://localhost:8001/redoc  
- **Health check:** http://localhost:8001/health  

SQLite database is auto-created at `backend/gateway/gateway.db` on first startup.  
Raw `.eml` files are stored in `backend/gateway/storage/`.

---

## ⚙️ Configuration

Reads from `md/.env` (4 directories up from `app/core/`):

| Variable | Description | Default |
|---|---|---|
| `FORENSIC_API` | Forensics service base URL | `https://sih-nine-flax.vercel.app` |
| `ML_API` | ML service base URL | `https://email-validation-micro-service.vercel.app` |

Additional config (override via environment variables):

| Variable | Default |
|---|---|
| `SECRET_KEY` | `super-secret-change-in-production-use-env-var` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
| `PIPELINE_SIGNATURE` | `pipeline-shared-secret` |

---

## 🔐 Authentication

All endpoints (except `/health`) require `Authorization: Bearer <access_token>`.

### Local demo administrator

Create the demo admin explicitly for local development:

```bash
cd backend/gateway
python scripts/seed_demo_admin.py
```

Demo login (never use these credentials in production):

```text
Email:    admin@aiemil.demo
Password: AIEMIL-Demo-2026!
Tenant:   demo-tenant
Role:     admin
```

### Login flow (no MFA)
```
POST /auth/login  { "email": "...", "password": "..." }
→ { "access_token": "...", "refresh_token": "...", "expires_in": 3600, "role": "analyst" }
```

### Login flow (MFA enabled)
```
POST /auth/login
→ { "mfa_required": true, "mfa_token": "<opaque>" }

POST /auth/mfa/verify  { "mfa_token": "<opaque>", "code": "<6-digit TOTP>" }
→ { "access_token": "...", "refresh_token": "...", "expires_in": 3600, "role": "analyst" }
```

### Refresh
```
POST /auth/refresh  { "refresh_token": "..." }
→ { "access_token": "...", "expires_in": 3600 }
```

---

## 📡 Endpoint Reference

### Auth
| Method | Path | Description |
|---|---|---|
| POST | `/auth/login` | Password login → JWT or MFA challenge |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/mfa/verify` | Complete MFA login with TOTP code |

### Email Ingestion & Triage
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/emails/ingest` | Ingest `.eml` file (multipart: file, tenant_id, source) |
| POST | `/api/v1/emails/self-report` | Employee self-report (tenant from logged-in user) |
| GET | `/api/v1/emails` | List/search: risk_level, classification, date, origin_country, auth_failure_type, etc. |
| GET | `/api/v1/emails/{id}` | Full detail + FraudAssessment |
| PATCH | `/api/v1/emails/{id}` | Update status (dismissed/escalated/reviewing) |
| POST | `/api/v1/emails/bulk-action` | Bulk: mark_reviewed / escalate_to_case / mark_false_positive |
| GET | `/api/v1/emails/{id}/report` | Forensic report (format=json\|pdf) |
| GET | `/api/v1/emails/{id}/graph` | Campaign relationship graph (proxied from ML API) |
| GET | `/api/v1/emails/{id}/custody` | Chain of custody (local DB + Forensics API) |
| POST | `/api/v1/emails/{id}/verdict` | Analyst verdict → ML retraining feedback |

### Cases
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/cases` | List cases (status filter, sort=submission_count_desc) |
| POST | `/api/v1/cases` | Create case + link submissions |
| GET | `/api/v1/cases/{id}` | Detail with shared_indicators from assessments |
| PATCH | `/api/v1/cases/{id}` | Update status / assignee / notes |
| GET | `/api/v1/cases/{id}/comments` | List comments |
| POST | `/api/v1/cases/{id}/comments` | Add comment |

### Dashboard
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/dashboard/summary` | 24h stats: scanned, threats, campaigns, avg triage time |
| GET | `/api/v1/dashboard/trend` | Daily/weekly trend chart (days, granularity params) |
| GET | `/api/v1/dashboard/top-domains` | Top offending sender domains (window=7d) |

### Alerts
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/alerts` | List alerts (unacknowledged_only, min_risk_level) |
| POST | `/api/v1/alerts/{id}/acknowledge` | Acknowledge alert |

### Geo
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/geo/heatmap` | Country/region rollup (from_date, to_date, classification, min_confidence) |

### Reports
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/reports` | Report library (tenant_id, type filter) |
| GET | `/api/v1/reports/schedules` | List scheduled reports |
| POST | `/api/v1/reports/schedules` | Create recurring report schedule |

### Rules & Watchlists *(admin only for writes)*
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/tenants/{id}/rules/thresholds` | Tenant alert thresholds |
| PUT | `/api/v1/tenants/{id}/rules/thresholds` | Update alert / auto-quarantine threshold |
| GET | `/api/v1/tenants/{id}/watchlists/{type}` | List watchlist (protected_brands / blocked_domains / allowed_domains / blocked_ips) |
| POST | `/api/v1/tenants/{id}/watchlists/{type}` | Add entry |
| DELETE | `/api/v1/tenants/{id}/watchlists/{type}/{entry_id}` | Remove entry |

### Users *(admin only)*
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/tenants/{id}/users` | List tenant users |
| POST | `/api/v1/tenants/{id}/users` | Create user |
| PATCH | `/api/v1/tenants/{id}/users/{uid}` | Update role / department / MFA / active |

### User Preferences
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/users/{uid}/saved-views` | List saved filter views |
| POST | `/api/v1/users/{uid}/saved-views` | Create saved view |
| GET | `/api/v1/users/{uid}/notification-preferences` | Get notification prefs |
| PUT | `/api/v1/users/{uid}/notification-preferences` | Update notification prefs |

### Audit Log
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/audit-log` | Search log (submission_id, case_id, actor, date range) |

### Settings
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/tenants/{id}/integrations/mailboxes` | List monitored mailboxes |
| POST | `/api/v1/tenants/{id}/integrations/mailboxes` | Add mailbox |
| GET | `/api/v1/tenants/{id}/privacy-config` | Retention / PII masking config |
| PUT | `/api/v1/tenants/{id}/privacy-config` | Update retention config |

### Internal / Pipeline
| Method | Path | Description |
|---|---|---|
| POST | `/internal/webhooks/fraud-assessment` | Receives `FraudAssessment` from pipeline (requires `X-Pipeline-Signature` header) |

---

## 🗄️ Database Schema (SQLite)

| Table | Purpose |
|---|---|
| `users` | Accounts with role, department, MFA config |
| `mfa_tokens` | Short-lived tokens for MFA flow |
| `submissions` | Ingested emails + status + local storage ref |
| `assessments` | Full `FraudAssessment` JSON + indexed fields |
| `cases` | Campaign cases grouping submissions |
| `case_submissions` | Many-to-many: cases ↔ submissions |
| `case_comments` | Analyst comment threads per case |
| `alerts` | Fired when fraud_score ≥ tenant threshold |
| `chain_of_custody` | Gateway-side evidence log (view/export/ingest) |
| `audit_log` | All gateway-side actions (append-only) |
| `reports` | Generated report artifacts |
| `report_schedules` | Recurring report schedules |
| `tenant_thresholds` | Per-tenant alert & auto-quarantine thresholds |
| `watchlists` | Protected brands, blocked/allowed domains/IPs |
| `privacy_config` | Retention days, PII masking, auto-purge |
| `mailbox_integrations` | Monitored mailboxes per tenant |
| `saved_views` | User-saved inbox filter configurations |
| `notification_preferences` | Per-user alert notification settings |
