# AI/ML Fraud Classification Microservice

Production-grade FastAPI backend for the AI/ML pipeline subsystem. This microservice implements content NLP analysis, link risk scoring, machine learning fraud classification, attachment malware heuristic scanning, model operations, and score aggregation into a comprehensive `FraudAssessment`.

*(Note: Graph correlation is excluded per architectural specification).*

---

## 🛠 Features & Endpoints

### 1. NLP Content Analysis
- **`POST /ml/nlp/analyze-content`**
- Scans `subject` and `body_text` for social engineering, urgency cues, fake invoices, payment diversion, and executive impersonation.
- Returns `urgency_score`, `impersonation_language_score`, and detected pattern spans:
  ```json
  {
    "urgency_score": 0.72,
    "impersonation_language_score": 0.65,
    "detected_patterns": [
      {
        "type": "payment_diversion",
        "excerpt_span": [120, 168],
        "confidence": 0.81
      }
    ],
    "language_model_version": "v2.3.1"
  }
  ```
  *(Note: `excerpt_span` contains character offsets `[start, end]` into the original body text).*

---

### 2. Link Extraction & Risk Scoring
- **`POST /ml/links/extract-and-score`**
- Parses HTML body, extracts `<a>` tags and text URLs, checks for IP literal hosts, URL shorteners, punycode/IDN homographs, suspicious TLDs, and display text mismatches (e.g. text claims `paypal.com` but points to an attacker IP/domain).
- Returns list of links with `risk_score` (0.0 to 1.0), `obfuscated` boolean flag, and `reasons`.

---

### 3. Core ML Fraud Classifier
- **`POST /ml/classify`**
- Assembles multi-signal feature vector from Forensics + NLP + Links.
- Returns classification (`legitimate`, `suspicious`, `impersonation`, `phishing`, `bec_fraud`), `fraud_score`, `confidence`, and normalized `feature_importance` contributions:
  ```json
  {
    "classification": "bec_fraud",
    "fraud_score": 0.87,
    "confidence": 0.91,
    "model_version": "v4.1.0",
    "feature_importance": [
      { "feature": "lookalike_score", "contribution": 0.31 },
      { "feature": "impersonation_language_score", "contribution": 0.26 },
      { "feature": "urgency_score", "contribution": 0.22 },
      { "feature": "dmarc_policy", "contribution": 0.14 },
      { "feature": "spf_authentication", "contribution": 0.12 }
    ]
  }
  ```

---

### 4. Attachment Malware Scanner
- **`POST /ml/attachments/scan`**
- Heuristic and signature-based scanner for file payloads, sha256 hash checks, macro droppers (`.xlsm`, `.docm`), executables, and script payloads.
- Returns `status` (`complete` / `sandboxing`), `malware_score`, `detected_type`, and `sandbox_report_ref`.

---

### 5. Final Fraud Score Aggregation
- **`POST /ml/aggregate`**
- Combines Forensics results, Core Classifier output, NLP scores, link risks, and attachment scan results.
- Returns the complete `FraudAssessment` with verdict (`PASS`, `SUSPICIOUS`, `REVIEW_REQUIRED`, `BLOCKED`), risk level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), primary threat category, score breakdown, key findings, and recommended remediation actions.

---

### 6. Model Operations & Retraining Loop
- **`GET /ml/models/health`**: Returns model status, active versions, and training timestamps.
- **`POST /ml/models/feedback`**: Accepts analyst-verified ground truth verdicts and queues for retraining (`202 Accepted`).

---

### 7. End-to-End Evaluation Pipeline
- **`POST /ml/pipeline/evaluate`**: Convenience orchestrator running all AI/ML components sequentially in dependency order.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Virtual environment (recommended)

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Running the Service
```bash
# Start FastAPI application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Interactive API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 5. Running the Tests
```bash
pytest tests/ -v
```

---

## 📂 Project Structure

```
SIH_PROTOTYPE_AI-ML_2026/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── routes/
│   │       │   ├── aggregate.py
│   │       │   ├── attachment.py
│   │       │   ├── classify.py
│   │       │   ├── links.py
│   │       │   ├── model_ops.py
│   │       │   ├── nlp.py
│   │       │   └── pipeline.py
│   │       └── api.py
│   ├── core/
│   │   └── config.py
│   ├── ml/
│   │   ├── aggregator.py
│   │   ├── attachment_engine.py
│   │   ├── classifier_model.py
│   │   ├── link_engine.py
│   │   └── nlp_engine.py
│   ├── schemas/
│   │   ├── aggregate.py
│   │   ├── attachment.py
│   │   ├── classify.py
│   │   ├── links.py
│   │   ├── model_ops.py
│   │   └── nlp.py
│   └── main.py
├── tests/
│   ├── test_aggregate.py
│   ├── test_attachment.py
│   ├── test_classify.py
│   ├── test_links.py
│   ├── test_model_ops.py
│   ├── test_nlp.py
│   └── test_pipeline.py
├── requirements.txt
└── README.md
```

