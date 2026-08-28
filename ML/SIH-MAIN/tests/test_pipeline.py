from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_pipeline_evaluate_e2e():
    payload = {
        "submission_id": "ee44bb22-55aa-44cc-88dd-112233445566",
        "subject": "URGENT: Executive Wire Transfer Required Immediately",
        "body_text": "Hello, this is CEO. Are you at your desk? Please initiate an urgent wire transfer to the new vendor account within 24 hours.",
        "body_html": "<p>Please login to verify: <a href='http://192.168.1.100/login'>https://internal-portal.corp</a></p>",
        "forensics": {
            "auth_results": { "spf": "fail", "dkim": "none", "dmarc": "fail" },
            "domain_age_days": 3,
            "lookalike_score": 0.94,
            "infra_flags": ["vpn", "hosting"],
            "header_anomalies_count": 3
        },
        "attachments": [
            {
                "storage_ref": "invoice_macro.xlsm",
                "sha256": "8a329d91f2c282f185f140e90c9b05d5f35b9c02ff436d4b47e2b7a9bf9a4c8a",
                "content_type": "application/vnd.ms-excel.sheet.macroEnabled.12"
            }
        ]
    }

    response = client.post("/ml/pipeline/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["submission_id"] == payload["submission_id"]
    assert "nlp_analysis" in data
    assert "links_analysis" in data
    assert "classifier_result" in data
    assert "attachments_analysis" in data
    assert "final_assessment" in data

    assessment = data["final_assessment"]
    assert assessment["risk_level"] in ["HIGH", "CRITICAL"]
    assert assessment["verdict"] in ["BLOCKED", "REVIEW_REQUIRED"]

