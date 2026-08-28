from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_classify_contract_payload():
    """
    Test using exact payload structure from aiml-README.md Section 0
    """
    payload = {
        "submission_id": "a3f4c022-7945-4221-8723-5e923e414c71",
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
    response = client.post("/ml/classify", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["classification"] in ["legitimate", "suspicious", "impersonation", "phishing", "bec_fraud"]
    assert 0.0 <= data["fraud_score"] <= 1.0
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["model_version"] == "v4.1.0"
    assert "feature_importance" in data
    assert len(data["feature_importance"]) > 0

    # For high lookalike + fail auth + urgency, fraud score should be high
    assert data["fraud_score"] > 0.6
    assert data["classification"] in ["bec_fraud", "impersonation", "phishing"]

def test_classify_legitimate_payload():
    payload = {
        "submission_id": "b7e21a00-1122-3344-5566-778899aabbcc",
        "features": {
            "auth_results": { "spf": "pass", "dkim": "pass", "dmarc": "pass" },
            "domain_age_days": 1200,
            "lookalike_score": 0.02,
            "infra_flags": [],
            "header_anomalies_count": 0,
            "urgency_score": 0.05,
            "impersonation_language_score": 0.02,
            "link_risk_scores": [0.05]
        }
    }
    response = client.post("/ml/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] == "legitimate"
    assert data["fraud_score"] < 0.3

