# TraceX — AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform

**SIH Problem Statement ID:** 26106  
**Organization:** All India Council for Technical Education (AICTE) – Cyber Security Cell  
**Category:** Software  
**Theme:** Blockchain & Cybersecurity  

---

## Executive Overview

**TraceX** is an enterprise-grade, court-admissible cyber forensics and Security triage intelligence platform engineered specifically for intelligence analysts, cybercrime cells, CERT teams, and enterprise incident response units.

Operating under a **Strict Real-Time / Zero-Hallucination Evidence Standard**, TraceX ingests raw RFC 5322 MIME messages (`.eml`), decomposes headers, authenticates email cryptographic signatures (SPF, DKIM, DMARC), reconstructs relay hop timelines, geolocates originating sending nodes, identifies spoofing and typosquatting domains, evaluates NLP social engineering urgency vectors, scores malicious landing pages, reasons over telemetry with **Groq AI LPU acceleration**, and links disparate attacks into unified Threat Actor Campaigns using graph clustering and cryptographic chain-of-custody ledgers.

---

## System Architecture

```
                                  +----------------------------------------------------+
                                  |            TraceX Security Workbench (React 19)         |
                                  | (Telemetry Grid, Map, Graph, Case Desk, PDF Export)|
                                  +-------------------------+--------------------------+
                                                            |
                                                   HTTP / REST (JWT Auth)
                                                            |
                                  +-------------------------v--------------------------+
                                  |              FastAPI Intelligence Core             |
                                  |       (Multi-Tenant, OpenAPI 3.1, Async IO)        |
                                  +----+--------------------+--------------------+-----+
                                       |                    |                    |
             +-------------------------+      +-------------+------------+       +-------------------------+
             |                                |                          |                                 |
+------------v------------+      +------------v------------+      +------v------------------+    +-------------v-------------+
|    Forensic Parsers     |      |   Threat Heuristics     |      |   Groq AI & Graph Engine|    |   Enterprise Persistence  |
| - RFC 5322 MIME         |      | - GeoIP & ASN Tracker   |      | - llama-3.3-70b-versat  |    | - Supabase PostgreSQL     |
| - Relay Hop Path Tracer |      | - Homoglyph / Lookalike |      | - Disjoint Set Clusters |    | - SQLite3 Local Fallback  |
| - SPF / DKIM / DMARC    |      | - NLP Social Eng. / BEC |      | - Campaign IOC Linking  |    | - SHA-256 Chain-of-Custody|
| - Live DNS & RDAP Age   |      | - Static Attachment /URL|      | - Cross-Submission Graph|    | - Cryptographic Audit Log |
+-------------------------+      +-------------------------+      +-------------------------+    +---------------------------+
```

---

## Key Capabilities & Features

### 1. Multi-Stage Threat Detection Engine
- **Header Decomposition & Hop Timeline:** Reconstructs the complete delivery chain (`Received:` headers) from originating client host (Hop 0) through intermediate mail transfers to the terminating gateway.
- **Protocol Verification:** Validates SPF records via live DNS TXT queries, DKIM public key signatures, and DMARC alignment enforcement policies.
- **GeoLocation & ASN Infrastructure Tracker:** Identifies physical geolocation (City, Country, Coordinates), ISP, Autonomous System Number (ASN), and queries live Spamhaus/SpamCop DNSBL blacklists.
- **Domain Spoofing & Lookalike Engine:** Detects homoglyph substitutions, Cyrillic visual spoofing, Bit-squatting, and Levenshtein edit distances against protected brand registries.
- **NLP Social Engineering & BEC Classifier:** Quantifies psychological coercion, executive impersonation vectors, financial wire instructions, and credential urgency.
- **Defanged URL & Attachment Analyzer:** Extracts embedded hyperlinks with defanging (`hxxp[://]`), analyzes suspicious redirect chains, and computes SHA-256 file hashes.
- **Groq AI Grounded Reasoning:** LPU-accelerated evidence reasoning that separates observed facts, probabilistic inferences, unknowns, and Security action steps.

### 2. Attribution Graph & Incident Correlation
- Automatically correlates multi-submission threats by shared relay subnets, lookalike domain roots, reply-to accounts, and payment diversion beneficiary indicators.
- Interactive Campaign attribution visualization allowing security analysts to track coordinated phishing clusters.

### 3. Court-Admissible Forensic Reporting
- Generates sealed, cryptographically signed PDF and JSON forensic investigation dossiers formatted with RFC 5322 headers, technical findings, geolocation coordinates, and chain-of-custody integrity hashes.

### 4. Enterprise Analyst Security Workbench (React + Vite)
- **Command Dashboard:** Live attack ingestion trends, severity distribution gauges, and real-time alerts.
- **Threat Inbox:** Comprehensive triage table with multi-factor filtering by risk and attack taxonomy.
- **7-Tab Forensic Workbench:** Overview, Headers & Protocols, GeoLocation Map, Domain Intel, AI / NLP Threat Signals, Attribution Graph, and Chain of Custody.
- **Interactive Global Map:** Leaflet-powered geospatial threat radar.
- **Case Management Desk:** Correlate multiple message submissions into active forensic investigation cases.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Lucide Icons, Leaflet / React-Leaflet, Recharts |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 Async, Uvicorn |
| **Database** | Supabase (PostgreSQL 16) with SQLite / aiosqlite local fallback |
| **ML / NLP** | Scikit-Learn, Custom Heuristic NLP Engine, Homoglyph Matrix |
| **Forensics** | ReportLab PDF Generator, Hashlib (SHA-256 / SHA-512), dnspython |
| **DevOps** | Docker, Docker Compose, Nginx, Pytest, Pytest-Asyncio |

---

## Quick Start & Deployment

### Option A: Running with Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/Vignesh7778/AI-Powered-Email-Threat-Detection-GeoLocation-Forensic-Intelligence-Platform.git
cd "AI-Powered-Email-Threat-Detection-GeoLocation-Forensic-Intelligence-Platform"

# 2. Build and launch container stack
docker-compose up --build -d

# 3. Access Platform Services:
# Frontend Security Platform: http://localhost:80 (or http://localhost:5173)
# Backend OpenAPI / Swagger: http://localhost:8000/docs
```

---

### Option B: Local Development Setup

#### 1. Backend Setup
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed synthetic test telemetry
python ../scripts/seed_demo_data.py

# Start FastAPI server
python -m uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev

# Open http://localhost:5173
```

---

## Automated Test Suite

The platform includes a test suite covering headers, DNS authentication, GeoIP, domain homoglyphs, NLP threat scoring, attachment scanning, graph correlation, end-to-end API pipeline, and PDF generation.

```bash
# Run full test suite
python -m pytest backend/tests/test_all_modules.py -v
```

**Results:** `14 passed in ~16s (100% test pass rate)`

---

## API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/login` | JWT Authentication & Session Token |
| `POST` | `/api/v1/emails/ingest` | Multipart upload for RFC 5322 `.eml` analysis |
| `GET` | `/api/v1/emails` | Paginated threat queue with search & filters |
| `GET` | `/api/v1/emails/{id}` | Comprehensive forensic assessment details |
| `GET` | `/api/v1/dashboard/stats` | Aggregate Security telemetry metrics & 24h attack trend |
| `GET` | `/api/v1/alerts` | Real-time threat alerts feed |
| `POST` | `/api/v1/alerts/{id}/acknowledge` | Mark security alert as reviewed |
| `GET` | `/api/v1/cases` | Incident case management listings |
| `POST` | `/api/v1/cases` | Create and associate incident cases |
| `GET` | `/api/v1/campaigns/{id}/graph` | Cross-submission threat attribution graph |
| `GET` | `/api/v1/forensics/chain/{id}` | Cryptographic chain-of-custody audit log |
| `GET` | `/api/v1/reports/{id}?format=pdf` | Court-admissible forensic PDF export |
| `GET` | `/api/v1/reports/{id}?format=json` | Raw forensic JSON telemetry export |

---

## Synthetic Sample Datasets

Synthetic, privacy-safe RFC 5322 `.eml` sample test emails are provided in `datasets/sample_emails/`:
1. `phishing.eml` — Credential harvesting with obfuscated lookalike link.
2. `bec.eml` — Executive wire fraud payment diversion attempt.
3. `impersonation.eml` — Brand domain visual spoofing attack.
4. `suspicious.eml` — Message originating through TOR exit node infrastructure.
5. `clean.eml` — Valid enterprise communication with SPF/DKIM/DMARC pass.
6. `attachment_malware.eml` — Disallowed high-risk executable script payload.

---

## License & Compliance

Developed for **Problem Statement 26106** — **AICTE Cyber Security Cell**.  
Licensed under the Apache 2.0 License.
