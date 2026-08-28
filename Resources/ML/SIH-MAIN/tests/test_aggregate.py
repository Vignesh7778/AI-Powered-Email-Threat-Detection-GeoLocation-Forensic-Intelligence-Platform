from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_aggregate_fraud_assessment():
    payload = {
        "submission_id": "c9a76d88-b647-4632-9c12-70b9df4b3701",
        "forensics_results": {
            "auth_results": { "spf": "fail", "dkim": "none", "dmarc": "fail" },
            "domain_age_days": 5,
            "lookalike_score": 0.92
        },
        "classify_result": {
            "classification": "bec_fraud",
            "fraud_score": 0.88,
            "confidence": 0.92,
            "model_version": "v4.1.0"
        },
        "nlp_result": {
            "urgency_score": 0.85,
            "impersonation_language_score": 0.90
        },
        "links_result": {
            "links": [
                {
                    "displayed_text": "Sign In",
                    "actual_url": "http://192.168.1.50/login",
                    "obfuscated": True,
                    "risk_score": 0.92,
                    "reasons": ["ip_literal_host"]
                }
            ]
        },
        "attachment_results": []
    }

    response = client.post("/ml/aggregate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["submission_id"] == payload["submission_id"]
    assert data["verdict"] in ["PASS", "SUSPICIOUS", "BLOCKED", "REVIEW_REQUIRED"]
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert data["primary_threat"] == "bec_fraud"
    assert data["fraud_score"] >= 0.70
    assert "score_breakdown" in data
    assert len(data["key_findings"]) > 0
    assert len(data["recommended_actions"]) > 0

