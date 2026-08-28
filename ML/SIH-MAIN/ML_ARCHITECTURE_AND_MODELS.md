# AI/ML Threat Detection Platform: Architecture, Algorithms & Models Reference Document

---

## 1. Executive Summary

This document provides a comprehensive technical breakdown of the machine learning algorithms, analytical engines, mathematical formulations, and Explainable AI (XAI) techniques implemented in the **AI-Powered Email Threat Detection & Forensic Intelligence Platform** (`ML/SIH-MAIN`).

The platform uses a **Layered Multi-Stage Ensemble Architecture** designed for high-throughput ($< 50\text{ ms}$ latency), high accuracy across complex attack vectors (such as Business Email Compromise and Spear Phishing), and privacy preservation.

---

## 2. Multi-Tier AI/ML Pipeline Overview

```
Raw Email Input (Subject, Body, Links, Attachments, Forensic Headers)
  │
  ├──▶ [Layer 1: NLP Intent Engine] ──────────▶ Urgency & Impersonation Scores + Coordinate Spans
  │
  ├──▶ [Layer 2: Link Obfuscation Scorer] ────▶ Obfuscation Flags & Link Risk Scores
  │
  ├──▶ [Layer 3: Attachment Malware Scanner] ─▶ Payload Risk & Sandbox Handoff
  │
  ▼
[Layer 4: Core Multi-Class ML Classifier (Random Forest)]
  │
  ├── Threat Category (legitimate | suspicious | impersonation | phishing | bec_fraud)
  ├── Calibrated Fraud Probability & Confidence
  └── Explainable AI (XAI) Feature Importance Contributions
  │
  ▼
[Layer 5: Multi-Signal Decision Aggregator]
  │
  ▼
Final FraudAssessment (Verdict: PASS / SUSPICIOUS / REVIEW_REQUIRED / BLOCKED)
```

---

## 3. Detailed Model Specifications

### 3.1. Core Multi-Class Threat Classifier (`classifier_model.py`)

* **Algorithm**: **Supervised Random Forest Ensemble (`RandomForestClassifier`) / Multi-Class Calibrated Decision Trees**.
* **Input**: 11-Dimensional Normalized Feature Vector ($\vec{X}$):
  $$\vec{X} = \begin{bmatrix}
  x_{\text{spf\_risk}} \\
  x_{\text{dkim\_risk}} \\
  x_{\text{dmarc\_risk}} \\
  x_{\text{domain\_age\_risk}} \\
  x_{\text{lookalike\_score}} \\
  x_{\text{infra\_risk}} \\
  x_{\text{header\_anomalies\_risk}} \\
  x_{\text{urgency\_score}} \\
  x_{\text{impersonation\_score}} \\
  x_{\text{max\_link\_risk}} \\
  x_{\text{avg\_link\_risk}}
  \end{bmatrix} \in [0.0, 1.0]^{11}$$

* **Target Classes**:
  1. `legitimate`: Clean, authenticated communications.
  2. `suspicious`: Inconclusive forensic or linguistic anomalies.
  3. `impersonation`: Executive / brand identity spoofing with high lookalike similarity.
  4. `phishing`: High-risk links, credential harvesting intent, and auth failures.
  5. `bec_fraud`: High impersonation language, urgency, payment diversion, and lookalike domains.

* **Probability & Confidence Calibration**:
  $$\text{FraudScore} = \text{clip}\Big(0.60 \cdot (1 - P(\text{legitimate})) + 0.40 \cdot \mathcal{S}_{\text{severe}}, 0.01, 0.99\Big)$$

---

### 3.2. Explainable AI (XAI) & Dynamic Feature Attribution

* **Methodology**: Localized Linear Contribution Decomposition.
* **Formula**:
  $$\text{Contribution}(f_i) = \frac{v_i \cdot w_i}{\sum_{j} v_j \cdot w_j}$$
  Where:
  * $v_i$ is the observed feature value.
  * $w_i$ is the empirical feature severity weight.
* **Output**: Top 5 normalized drivers explaining the exact reasons behind the classification (e.g., Lookalike Score: 31%, Impersonation Language: 26%, Urgency: 22%).

---

### 3.3. NLP Intent & Social Engineering Engine (`nlp_engine.py`)

* **Algorithm**: Semantic Pattern Matcher with **Non-Linear Cumulative Saturated Aggregation**.
* **Target Pattern Taxonomies**:
  * `urgency_cue`: Artificial deadlines, immediate suspension threats.
  * `executive_impersonation`: VIP/CEO authority manipulation, confidential requests.
  * `payment_diversion`: Bank routing alterations, gift card/crypto demands.
  * `fake_invoice`: Unsolicited invoices, overdue billing statements.
  * `credential_harvesting`: Password resets, fake re-authentication prompts.
* **Mathematical Saturation Formula**:
  $$\text{Score}_{k+1} = \text{Score}_k + w_k \cdot (1 - \text{Score}_k) \cdot \gamma$$
  *(Prevents score overflow while exponentially elevating risk when multiple cues co-occur).*
* **Privacy Feature**: Emits character offset spans `[start, end]` rather than raw text, ensuring zero exposure of sensitive email content.

---

### 3.4. Link Risk & Obfuscation Scorer (`link_engine.py`)

* **Algorithm**: Multi-Factor Structural Heuristic Risk Scorer.
* **Detection Vectors**:
  * **IP Literal Host Attacks**: Raw IP usage (`http://192.168.1.50/login`) and hex/octal encoded hosts.
  * **Display Text Mismatch**: Discrepancy between visible anchor text (`paypal.com`) and hidden destination URL.
  * **Punycode / IDN Homographs**: Unicode character substitution (`xn--...`).
  * **URL Shortener Cloaking**: Identification of redirection hubs (`bit.ly`, `tinyurl.com`, `t.co`).
  * **High-Risk TLDs & Subdomain Nesting**: Deep subdomain trees and high-abuse top-level domains (`.xyz`, `.top`, `.loan`).

---

### 3.5. Attachment Malware Analyzer (`attachment_engine.py`)

* **Algorithm**: Cryptographic Hash Matching & MIME/Extension Discrepancy Matrix.
* **Features**:
  * SHA-256 instant known malware database verification.
  * Macro-dropper detection (`.xlsm`, `.docm`).
  * Executable container and script inspection (`.exe`, `.vbs`, `.ps1`, `.iso`).
  * Asynchronous hand-off protocol (`202 Accepted`) for dynamic sandbox detonation.

---

### 3.6. Multi-Signal Decision Aggregator (`aggregator.py`)

* **Algorithm**: Multi-Layer Weighted Fusion Model.
* **Composite Formula**:
  $$\text{CompositeScore} = 0.50 \cdot \mathcal{S}_{\text{Classifier}} + 0.20 \cdot \mathcal{S}_{\text{Forensics}} + 0.10 \cdot \mathcal{S}_{\text{NLP}} + 0.10 \cdot \mathcal{S}_{\text{Links}} + 0.10 \cdot \mathcal{S}_{\text{Attachments}}$$

* **Decision Matrix**:
  | Composite Score | Risk Level | Verdict | Automated Defense Action |
  | :--- | :--- | :--- | :--- |
  | $\ge 0.80$ | **CRITICAL** | `BLOCKED` | Quarantine message & purge from mailboxes |
  | $0.60 - 0.79$ | **HIGH** | `REVIEW_REQUIRED` | Flag to SOC analyst & alert recipient |
  | $0.35 - 0.59$ | **MEDIUM** | `SUSPICIOUS` | Inject warning banner in email body |
  | $< 0.35$ | **LOW** | `PASS` | Deliver to inbox |

---

### 3.7. Continuous Learning & Model Ops (`model_ops.py`)

* **Endpoints**:
  * `GET /ml/models/health`: Live telemetry of active model versions and training timestamps.
  * `POST /ml/models/feedback`: Ingests analyst-confirmed ground truth into retraining queues (`202 Accepted`).

---

## 4. Algorithms Summary Table for Quick Reference

| Component | Primary Algorithm / Technique | Key Output Metric | File Location |
| :--- | :--- | :--- | :--- |
| **Core Classifier** | Random Forest / Decision Trees (`RandomForestClassifier`) | Threat Category + Fraud Probability $[0, 1]$ | `app/ml/classifier_model.py` |
| **Explainable AI (XAI)** | Local Linear Feature Attribution | Feature Contribution % List | `app/ml/classifier_model.py` |
| **NLP Intent Engine** | Saturated Semantic Pattern Aggregation | Urgency & Impersonation Scores $[0, 1]$ + Spans | `app/ml/nlp_engine.py` |
| **Link Risk Analyzer** | Multi-Factor Structural Heuristics & Homograph Detection | Link Risk Score $[0, 1]$ + Obfuscation Reasons | `app/ml/link_engine.py` |
| **Attachment Scanner** | SHA-256 Hash Matching & MIME Discrepancy Matrix | Malware Probability Score $[0, 1]$ | `app/ml/attachment_engine.py` |
| **Aggregator Engine** | Weighted Multi-Signal Fusion Matrix | Final `FraudAssessment` + Action Playbooks | `app/ml/aggregator.py` |
| **Model Operations** | Active Learning Feedback Loop | Health Telemetry & Retraining Queue | `app/ml/model_ops.py` |
