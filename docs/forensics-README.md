# Cyber Forensics Team — API

**Owns:** email header/protocol forensics, origin tracing, geolocation, infrastructure flagging, domain intelligence.

Forensics runs first in the pipeline and produces the **feature inputs** the AI/ML team consumes (see [`aiml-README.md`](./aiml-README.md) §0 for the exact handoff schema). Software Dev never calls these endpoints directly in production — they're called internally by the pipeline orchestrator — but are documented as standalone REST endpoints so Forensics can build/test independently. See [`README.md`](./README.md) for the overall system contracts.

---

## 1. Email Header & Protocol Analysis

### `POST /forensics/headers/parse`
Parses raw header block into structured fields.

**Request**
```json
{ "raw_headers": "string" }
```
**Response `200`**
```json
{
  "message_id": "string",
  "return_path": "string",
  "reply_to": "string|null",
  "from_display": "string",
  "from_address": "string",
  "received_chain": [
    { "hop": 0, "from_host": "string", "by_host": "string", "with_protocol": "string", "timestamp": "ISO8601", "ip": "string|null" }
  ],
  "anomalies": [
    { "type": "forged_return_path|relay_manipulation|header_injection|timestamp_inconsistency", "detail": "string", "severity": "low|medium|high" }
  ]
}
```

### `POST /forensics/auth/validate`
Validates SPF/DKIM/DMARC.

**Request**
```json
{ "raw_headers": "string", "sender_domain": "string" }
```
**Response `200`**
```json
{
  "spf": { "result": "pass|fail|softfail|neutral|none", "record": "string|null" },
  "dkim": { "result": "pass|fail|none", "selector": "string|null", "domain": "string|null" },
  "dmarc": { "result": "pass|fail|none", "policy": "none|quarantine|reject" },
  "alignment_ok": true
}
```

---

## 2. Origin Traceability & Geolocation

### `POST /forensics/origin/trace`
Extracts the earliest reliable sending IP from the `Received` chain, filtering out internal/trusted relay hops.

**Request**
```json
{ "received_chain": [ { "hop": 0, "ip": "string", "hostname": "string|null" } ], "trusted_relay_ranges": ["10.0.0.0/8"] }
```
**Response `200`**
```json
{
  "originating_ip": "203.0.113.42",
  "confidence": 0.88,
  "reasoning": "string — e.g. first hop outside trusted infra with consistent timestamp ordering"
}
```

### `POST /forensics/geo/lookup`
**Request:** `{ "ip": "203.0.113.42" }`
**Response `200`**
```json
{
  "ip": "203.0.113.42",
  "country": "string", "region": "string", "city": "string",
  "lat": 0.0, "lon": 0.0,
  "isp": "string",
  "hosting_provider": "string|null",
  "asn": "string"
}
```

### `POST /forensics/infra/flags`
Checks IP against VPN/TOR/open-relay/botnet indicator lists.

**Request:** `{ "ip": "203.0.113.42" }`
**Response `200`**
```json
{ "ip": "203.0.113.42", "flags": ["vpn", "tor", "open_relay", "cloud_hosted", "botnet_suspected"], "source_lists": ["string"] }
```

---

## 3. Domain Intelligence

### `POST /forensics/domain/intel`
**Request:** `{ "domain": "example.com" }`
**Response `200`**
```json
{
  "domain": "example.com",
  "registrar": "string",
  "created_date": "ISO8601",
  "age_days": 4,
  "mx_records": ["mx1.example.com"],
  "dns_records": { "a": ["string"], "txt": ["string"] },
  "hosting_fingerprint": "string"
}
```

### `POST /forensics/domain/lookalike-check`
Compares sender domain against a protected-brand/known-domain list using edit-distance + homoglyph detection.

**Request:** `{ "domain": "paypa1.com", "compare_against": ["paypal.com", "yourbank.com"] }`
**Response `200`**
```json
{ "domain": "paypa1.com", "lookalike_of": "paypal.com", "technique": "character_substitution|homoglyph|combosquatting|tld_swap", "score": 0.93 }
```

---

## 4. Chain-of-Custody / Evidence Logging

### `POST /forensics/evidence/log`
Every forensic module call that touches raw evidence should log an access record.

**Request**
```json
{ "submission_id": "uuid", "actor": "system|user_id", "action": "parsed_headers|traced_origin|geo_lookup|domain_lookup", "timestamp": "ISO8601" }
```
**Response `201`:** `{ "log_id": "uuid" }`

### `GET /forensics/evidence/{submission_id}/chain`
Returns the full chain-of-custody log for a submission — required for the forensic report export (Software Dev's `GET /api/v1/emails/{submission_id}/report`).

**Response `200`**
```json
{ "submission_id": "uuid", "entries": [ { "log_id": "uuid", "actor": "string", "action": "string", "timestamp": "ISO8601" } ] }
```

---

## 5. Output Contract → AI/ML Team

Forensics doesn't call AI/ML endpoints directly — the pipeline orchestrator (in Software Dev's gateway or a thin coordination layer) collects forensics output and shapes it into the `features` object the AI/ML `/ml/classify` endpoint expects:

| Forensics endpoint | Feeds AI/ML feature |
|---|---|
| `/forensics/auth/validate` | `features.auth_results` |
| `/forensics/domain/intel` | `features.domain_age_days` |
| `/forensics/domain/lookalike-check` | `features.lookalike_score` |
| `/forensics/infra/flags` | `features.infra_flags` |
| `/forensics/headers/parse` (`anomalies`) | `features.header_anomalies_count` |
| `/forensics/origin/trace` + `/forensics/geo/lookup` | `origin` block in final `FraudAssessment` (not a classifier feature, but required for the report/map) |

Full feature schema is owned by the AI/ML team — see [`aiml-README.md`](./aiml-README.md) §0.

---

## 6. Module Dependency Order

```
raw email
  ├─▶ headers/parse ──▶ origin/trace ──▶ geo/lookup ──▶ infra/flags
  ├─▶ auth/validate
  └─▶ domain/intel ──▶ domain/lookalike-check

  all outputs ──▶ handed to AI/ML as `features` (see §5) ──▶ /ml/classify
```
