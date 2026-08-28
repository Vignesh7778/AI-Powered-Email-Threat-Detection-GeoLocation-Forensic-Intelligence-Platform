# Backend CRUD & File Storage Guide

This document translates the API contracts in `README.md` and `docs/` into the backend operations required to ingest, store, analyse, update, and report on suspicious emails.

## 1. Storage model

Store raw evidence outside the relational database. The database stores metadata, references, hashes, workflow state, and audit records.

| Resource | Database record | Binary/object storage |
|---|---|---|
| Uploaded `.eml` | `submissions` | Original RFC 5322 email file |
| Attachments | `attachments` | Attachment bytes, addressed by `storage_ref` |
| Pipeline output | `assessments` | Not required unless storing a signed report artifact |
| Forensic report | `reports` | Generated PDF/JSON package |
| Evidence access | `chain_of_custody` | Not applicable; append-only audit record |

Recommended object key pattern:

```text
tenants/{tenant_id}/submissions/{submission_id}/raw/{sha256}.eml
tenants/{tenant_id}/submissions/{submission_id}/attachments/{sha256}-{filename}
tenants/{tenant_id}/reports/{report_id}/forensic-report.pdf
```

Do not store raw email bodies, raw headers, or file contents in normal application logs. Store their SHA-256 values and object-storage references instead.

## 2. Core tables

The existing high-level schema should be extended with file and report records.

```sql
create table submissions (
  submission_id uuid primary key,
  tenant_id uuid not null,
  source varchar(20) not null,
  sender varchar(320),
  subject varchar(998),
  raw_storage_ref text not null,
  raw_sha256 char(64) not null,
  status varchar(20) not null default 'queued',
  received_at timestamptz,
  ingested_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table attachments (
  attachment_id uuid primary key,
  submission_id uuid not null references submissions(submission_id),
  filename text not null,
  content_type varchar(255),
  size_bytes bigint not null,
  sha256 char(64) not null,
  storage_ref text not null,
  scan_status varchar(20) not null default 'pending',
  malware_score numeric(4,3),
  created_at timestamptz not null default now()
);

create table assessments (
  submission_id uuid primary key references submissions(submission_id),
  fraud_score numeric(4,3) not null,
  risk_level varchar(16) not null,
  classification varchar(32) not null,
  confidence numeric(4,3) not null,
  assessment_json jsonb not null,
  analyzed_at timestamptz not null,
  model_version varchar(64),
  updated_at timestamptz not null default now()
);

create table reports (
  report_id uuid primary key,
  submission_id uuid not null references submissions(submission_id),
  format varchar(10) not null,
  storage_ref text not null,
  sha256 char(64) not null,
  generated_by uuid,
  generated_at timestamptz not null default now()
);
```

Use a unique constraint on `(tenant_id, raw_sha256)` if duplicate raw uploads should be detected within a tenant.

## 3. CRUD operations

### 3.1 Create: ingest an email file

`POST /api/v1/emails/ingest`

1. Authenticate the caller and validate `tenant_id` and `source`.
2. Accept only `.eml` content within a configured size limit.
3. Stream the file to temporary storage while calculating SHA-256; do not load an unbounded file into memory.
4. Parse only the minimum safe metadata needed for the queue: sender, subject, received time, attachment manifest.
5. Move the file to immutable evidence storage using the submission object key.
6. Insert the `submissions` row with `status = queued` and create `attachments` rows.
7. Insert a `chain_of_custody` entry with action `ingested`.
8. Enqueue the pipeline analysis job and return `202 Accepted` with `submission_id`.

Example response:

```json
{
  "submission_id": "f21a4d8f-31a8-4d49-a73c-5ba753f513f1",
  "status": "queued",
  "estimated_processing": "async"
}
```

### 3.2 Read: retrieve email status and assessment

`GET /api/v1/emails/{submission_id}`

Read the submission metadata and join the latest assessment when it exists. Return the `FraudAssessment` shape defined in `README.md` §2.2. Do not return raw email bodies or direct object-storage URLs from this endpoint.

Useful additions:

```text
GET /api/v1/emails/{submission_id}/preview
GET /api/v1/emails/{submission_id}/headers
GET /api/v1/emails/{submission_id}/attachments
GET /api/v1/emails/{submission_id}/evidence
```

- `preview` returns a sanitized, link-defanged rendering for analysts.
- `headers` requires an investigator-capable role and logs `viewed_raw_headers`.
- `attachments` returns metadata and malware status; downloads should use short-lived signed URLs only after authorization.
- `evidence` returns the chain-of-custody records.

### 3.3 Read: list and search the threat queue

`GET /api/v1/emails`

Support the documented filters (`risk_level`, `classification`, date range, campaign) plus practical triage fields:

```text
status, assigned_to, reviewed, department, sender_domain, has_attachment
```

Default sort order should be:

1. `risk_level` descending
2. `fraud_score` descending
3. `received_at` descending

Always scope queries by `tenant_id` from the authenticated user, not an untrusted query parameter alone.

### 3.4 Update: lifecycle and analyst decisions

`PATCH /api/v1/emails/{submission_id}`

Allow controlled updates to workflow fields, not to immutable evidence fields.

```json
{
  "status": "reviewed",
  "assigned_to": "user-uuid",
  "analyst_verdict": "phishing",
  "notes": "Credential-harvesting link confirmed."
}
```

Allowed status flow:

```text
queued -> analyzing -> complete
                    -> failed
complete -> reviewed -> escalated -> closed
```

Each state change must create an audit entry such as `analysis_started`, `assessment_received`, `marked_reviewed`, `escalated_to_case`, or `closed`.

Do not allow changes to `raw_storage_ref`, `raw_sha256`, evidence timestamps, or the original assessment payload through a normal update endpoint.

### 3.5 Update: persist pipeline output

`POST /internal/webhooks/fraud-assessment`

This is an internal upsert operation. The pipeline sends the complete `FraudAssessment`.

1. Validate the webhook signature and submission ID.
2. Verify that the submission belongs to the expected tenant/workflow.
3. Upsert `assessments` using `submission_id` as the conflict key.
4. Update `submissions.status` to `complete`.
5. Update attachment scan fields if attachment results were included.
6. Create alerts when policy thresholds are met.
7. Append `assessment_received` to chain-of-custody.

The webhook must be idempotent: replaying the same payload should not create duplicate alerts or evidence entries.

### 3.6 Delete: retention-based evidence purge

`DELETE /api/v1/emails/{submission_id}` should normally be restricted or disabled for human users. For forensic evidence, deletion should happen through a retention policy worker.

Retention worker flow:

1. Select records eligible under tenant retention configuration.
2. Exclude evidence holds, active cases, and legal/compliance holds.
3. Write a final `purge_scheduled` audit record.
4. Delete binary files from object storage.
5. Replace sensitive database fields with a tombstone record, retaining the purge timestamp and reason where policy requires it.
6. Write `purged_by_retention_policy` to an immutable audit store.

If a manual deletion endpoint is needed, require administrator role, a reason, dual approval for evidence-locked cases, and a retention-policy check.

## 4. Case management CRUD

Cases group multiple submissions under one investigation.

| Operation | Endpoint | Behaviour |
|---|---|---|
| Create case | `POST /api/v1/cases` | Create the case, attach one or more submission IDs, add `case_created` audit entries. |
| List cases | `GET /api/v1/cases` | Filter by status, analyst, campaign, date, or department. |
| Read case | `GET /api/v1/cases/{case_id}` | Return linked submissions, assessments, notes, assignments, and shared indicators. |
| Update case | `PATCH /api/v1/cases/{case_id}` | Update status, title, assignee, priority, or investigation notes. |
| Add evidence | `POST /api/v1/cases/{case_id}/submissions` | Attach existing submissions without copying raw files. |
| Remove evidence | `DELETE /api/v1/cases/{case_id}/submissions/{submission_id}` | Detach from the case only; never delete the submission itself. |
| Close case | `PATCH /api/v1/cases/{case_id}` | Require final disposition and log who closed it. |

## 5. Project-level updates

When adding or changing backend behaviour, update these project areas together:

| Change | Update required |
|---|---|
| New ingestion field | Request validation, database migration, OpenAPI schema, `EmailSubmission` contract if pipeline needs it |
| New classifier result | `FraudAssessment` contract, assessment JSON persistence, UI mapping, report generator |
| New attachment scan status | `attachments` table, async webhook handling, queue/detail API, alert policy |
| New evidence action | Chain-of-custody enum/schema, audit logger, report timeline |
| New retention policy | Tenant privacy config, scheduled worker, evidence-hold checks, audit logging |
| New case field | Case migration, API serializer, authorization policy, case detail UI |

Use database migrations for every persistent schema change. Avoid editing production tables manually.

## 6. Authorization and integrity requirements

- Require tenant scoping on every database query and object key.
- Use RBAC: analysts triage; investigators access raw headers/evidence; admins manage retention and policy; executives see masked summaries.
- Encrypt raw email and attachment objects at rest and use TLS in transit.
- Generate time-limited signed URLs for authorized downloads instead of exposing bucket paths.
- Treat raw email, headers, attachments, and generated reports as sensitive evidence.
- Log every raw-evidence read, export, update, and retention action.
- Use optimistic locking or `updated_at` checks on analyst/case updates to prevent silent overwrites.
- Make pipeline webhooks idempotent with an event ID or payload hash.

## 7. Suggested backend modules

```text
app/
  api/              # FastAPI routers and request/response models
  services/
    ingestion.py    # Stream upload, hash, parse metadata, enqueue analysis
    storage.py      # Object storage abstraction and signed URLs
    pipeline.py     # Internal analysis calls and webhook verification
    cases.py        # Case workflows and evidence linking
    reports.py      # Report generation and file persistence
    retention.py    # Policy-driven purge and evidence holds
    audit.py        # Append-only chain-of-custody logging
  models/           # ORM models
  migrations/       # Versioned database migrations
  workers/          # Async analysis, report, and retention jobs
```

This separation keeps file handling, forensic integrity, and project workflow logic explicit and independently testable.
