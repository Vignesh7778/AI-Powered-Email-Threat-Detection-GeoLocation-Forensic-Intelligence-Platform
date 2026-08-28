# TraceX — System Architecture Document

**Project:** TraceX — AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform  
**SIH Problem Statement ID:** 26106  
**Organization:** All India Council for Technical Education (AICTE) – Cyber Security Cell  
**Theme:** Blockchain & Cybersecurity  

---

## 1. System Architecture Overview

TraceX is engineered with a modular, decoupled microservice-ready architecture comprising four primary tiers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION TIER (UI/UX)                          │
│  React 19 + TypeScript + Vite + Tailwind CSS + Leaflet Maps + Lucide Icons   │
│  7-Tab Deep Forensic Workbench • Incident Desk • Live Re-Query • PII Masking│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ RESTful HTTPS / JSON (Bearer JWT)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION & API TIER                             │
│       FastAPI (Async) Core • Pydantic v2 Contracts • SQLAlchemy 2.0 ORM     │
│  Endpoints: /auth, /emails, /forensics, /ml, /cases, /alerts, /privacy      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
┌─────────────────────────┐ ┌──────────────────────┐ ┌────────────────────────┐
│  FORENSIC & ML ENGINE   │ │  REAL-TIME NETWORK   │ │    GROQ AI REASONING   │
│ • RFC 5322 MIME Parser  │ │ • dnspython Live DNS │ │ • llama-3.3-70b-versat │
│ • Header Analyzer       │ │ • ICANN RDAP Client  │ │ • Zero-Hallucination   │
│ • SPF/DKIM/DMARC Val.   │ │ • ip-api GeoIP Trace │ │   Grounding Validator  │
│ • NLP Heuristics Engine │ │ • Spamhaus/SpamCop   │ │ • Structured Output    │
│ • Levenshtein Lookalike │ │   DNSBL Blacklists   │ │   (Facts/Inferences)   │
│ • Static Attachment &   │ │ • RFC 1918 Private   │ │ • Security Action Advisory  │
│   URL Obfuscation Scans │ │   Subnet Filter      │ │                        │
└─────────────────────────┘ └──────────────────────┘ └────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PERSISTENCE & DATA TIER                           │
│  Primary: Supabase (PostgreSQL 15)                                          │
│  Automated Local Development Fallback: SQLite3 (Async WAL)                  │
│  Artifact Storage: Defanged SHA-256 Storage Repository (`./data/storage`)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory & Package Structure

```
TraceX/
├── backend/
│   ├── analysis/
│   │   ├── authentication/    # Live SPF (DNS TXT), DKIM parser, DMARC alignment
│   │   ├── domain/            # Live DNS (A, MX, NS, TXT) + RDAP age + Lookalike
│   │   ├── evidence/          # Tamper-evident Chain of Custody logger & SHA-256
│   │   ├── geolocation/       # Live GeoIP resolver + RFC 1918 private filter
│   │   ├── headers/           # RFC 5322 MIME parser & header anomaly detector
│   │   ├── llm/               # Groq AI Evidence-Grounded Reasoning Engine
│   │   ├── origin/            # Received-chain chronological hop tracer
│   │   ├── parser/            # Raw .eml multi-part extractor
│   │   └── threat_intel/      # Spamhaus ZEN & SpamCop DNSBL provider
│   ├── app/
│   │   ├── api/v1/routes/     # REST API route controllers
│   │   ├── core/              # Config, Security, Database connectors
│   │   ├── models/            # SQLAlchemy database ORM entities
│   │   ├── schemas/           # Pydantic wire contract schemas
│   │   └── services/          # Central Pipeline Orchestrator
│   ├── ml/
│   │   ├── inference/         # NLP urgency, link deobfuscator, attachment scanner
│   │   └── models/            # Multi-class threat heuristic classifier
│   ├── graph/                 # Cross-incident campaign correlation engine
│   ├── reports/               # Court-admissible PDF & JSON dossier generator
│   └── tests/                 # Automated Pytest suite (14 test modules)
├── frontend/
│   ├── src/
│   │   ├── api/               # Typed API client with JWT auth
│   │   ├── components/        # Reusable UI components & Trust Badges
│   │   ├── pages/             # 10 dedicated Security views (Workbench, Map, Cases, etc.)
│   │   └── types/             # TypeScript forensic data interfaces
│   ├── index.html
│   └── vite.config.ts
├── datasets/sample_emails/    # Authentic .eml test artifacts
├── scripts/seed_demo_data.py  # Zero-hallucination live ingestion seeder
├── IMPLEMENTATION_AUDIT.md    # SIH 26106 capability audit
├── SIH_REQUIREMENTS_MAPPING.md# Requirement-by-requirement mapping
└── ARCHITECTURE.md            # System architecture reference
```

---

## 3. Database Schema Entity-Relationship Model

- **`users`**: Identity management with bcrypt salted hashing and RBAC (`analyst`, `admin`, `investigator`).
- **`submissions`**: Core email artifact metadata, source, mailbox, SHA-256 fingerprint, and processing status.
- **`assessments`**: Composite fraud score (0.00 – 1.00), risk level, threat category, and structured JSON assessment.
- **`cases`**: Security incident tracking with severity, analyst assignment, notes, and status (`open`, `investigating`, `contained`, `resolved`, `closed`).
- **`case_submissions`**: Many-to-many link associating multiple email submissions to a unified case.
- **`alerts`**: High/Critical threat triggers requiring analyst acknowledgment.
- **`chain_of_custody`**: Append-only tamper-evident audit ledger with SHA-256 integrity sealing.
- **`campaigns`**: Clustered threat campaigns sharing IOCs, subnets, or sender domains.
- **`privacy_configs`**: Tenant-specific data retention periods and PII masking preferences.

